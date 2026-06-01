"""Use case `reemitir_certificado` — M8 Fatia 2b (T-CER-043, US-CER-004/013).

Reemissão VERSIONADA: cria `v(N+1)` ligada a `v(N)` via `versao_anterior_id` e
marca `v(N) → SUBSTITUIDA` (one-shot CAS por `revision`). Correção de certificado
emitido é SEMPRE por nova versão (nunca UPDATE — INV-CER-WORM-001). Motivo ≥ 50
chars (US-CER-004). Herda os snapshots de contexto do `v(N)` (paridade pós-baixa
do equipamento — US-CER-013).

Use case PURO (ADR-0007). Reaproveita o miolo de `emitir_certificado` (reconcilia
a MESMA calibração APROVADA imutável → resultado determinístico) e só acrescenta a
validação do motivo + a transição WORM do anterior. O caller (view) envolve tudo
numa única `transaction.atomic` com advisory lock por calibração; se o CAS falhar
(`ReemissaoConflitanteError`), o INSERT da nova versão é revertido.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    OrcamentoPorPontoSnapshot,
)
from src.domain.metrologia.certificados.entities import CertificadoSnapshot
from src.domain.metrologia.certificados.erros import ReemissaoConflitanteError
from src.domain.metrologia.certificados.portas import CmcParaPort
from src.domain.metrologia.certificados.reconciliacao import PontoMedido
from src.domain.metrologia.certificados.repository import (
    AnaliseReconciliacaoRepository,
    CertificadoRepository,
)
from src.domain.metrologia.certificados.transicoes import validar_motivo_reemissao

from .emitir_certificado import EmitirCertificadoInput, emitir_certificado


@dataclass(frozen=True, slots=True)
class ReemitirCertificadoInput:
    tenant_id: UUID
    certificado_anterior: CertificadoSnapshot  # v(N) carregado pela view
    revision_anterior: int  # do Model (CAS — não vive no snapshot)
    motivo: str  # ≥ 50 chars (US-CER-004)
    calibracao: CalibracaoSnapshot
    pontos_medidos: Sequence[PontoMedido]
    orcamentos_por_ponto: Sequence[OrcamentoPorPontoSnapshot]
    perfil: str  # server-side (ADR-0067)
    numero_interno: int  # nova numeração (sequence — buracos OK)
    numero_certificado: str  # novo número visível reservado (sem buracos)
    data_emissao: date
    emitido_em: datetime
    correlation_id: UUID
    cmc_para: CmcParaPort | None = None
    acreditacao_vigencia_fim: date | None = None
    acreditacao_suspensa_em: date | None = None
    acreditacao_suspensa_ate: date | None = None
    # Override do snapshot de padrões; default ⇒ herda do v(N) (US-CER-013).
    snapshot_padroes_usados_json: Sequence[Mapping[str, object]] | None = None


def reemitir_certificado(
    inp: ReemitirCertificadoInput,
    *,
    cert_repo: CertificadoRepository,
    analise_repo: AnaliseReconciliacaoRepository,
) -> CertificadoSnapshot:
    """Crava `v(N+1)` e transiciona `v(N) → SUBSTITUIDA`. Raise
    `MotivoReemissaoInsuficienteError` (<50 chars) ou `ReemissaoConflitanteError`
    (CAS — corrida/já substituído → 409)."""
    validar_motivo_reemissao(inp.motivo)
    v_n = inp.certificado_anterior
    nova_versao = v_n.versao + 1

    # Herda o snapshot de padrões do v(N) salvo não vier override (US-CER-013).
    padroes = (
        inp.snapshot_padroes_usados_json
        if inp.snapshot_padroes_usados_json is not None
        else v_n.snapshot_padroes_usados_json
    )

    emit_inp = EmitirCertificadoInput(
        tenant_id=inp.tenant_id,
        calibracao=inp.calibracao,
        pontos_medidos=inp.pontos_medidos,
        orcamentos_por_ponto=inp.orcamentos_por_ponto,
        perfil=inp.perfil,
        numero_interno=inp.numero_interno,
        numero_certificado=inp.numero_certificado,
        snapshot_padroes_usados_json=padroes,
        data_emissao=inp.data_emissao,
        emitido_em=inp.emitido_em,
        correlation_id=inp.correlation_id,
        cmc_para=inp.cmc_para,
        acreditacao_vigencia_fim=inp.acreditacao_vigencia_fim,
        acreditacao_suspensa_em=inp.acreditacao_suspensa_em,
        acreditacao_suspensa_ate=inp.acreditacao_suspensa_ate,
        versao=nova_versao,
        versao_anterior_id=v_n.id,
    )

    # Re-reconcilia + crava a nova versão (idempotente por (tenant, calibração, N+1)).
    nova = emitir_certificado(emit_inp, cert_repo=cert_repo, analise_repo=analise_repo)

    # Transição WORM do anterior (CAS one-shot). False ⇒ corrida/já terminal → 409;
    # o caller reverte o INSERT da nova versão na mesma transação atômica.
    if not cert_repo.marcar_substituida(
        certificado_id=v_n.id, revision_anterior=inp.revision_anterior
    ):
        raise ReemissaoConflitanteError(
            f"reemissão de {v_n.id} falhou no CAS (revision={inp.revision_anterior}) "
            f"— corrida ou já substituído/revogado"
        )
    return nova
