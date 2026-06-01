"""Use case `emitir_certificado` — M8 Fatia 2b (T-CER-041/042, US-CER-001).

Emissão metrológica ATÔMICA fail-closed: consome uma calibração APROVADA, reconcilia
a cobertura ponto-a-ponto (ADR-0076: pontos ⊆ declarada + U ≥ CMC), aplica as decisões
WORM do RT sobre pontos problemáticos, determina RBC/NÃO-RBC, e crava o
`CertificadoSnapshot` + N `PontoReconciliadoSnapshot` + `reconciliacao_hash` numa única
transação (o caller envolve em `transaction.atomic`). Use case PURO (ADR-0007).

Fecha GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC. Perfil A com ponto
não-RBC SEM decisão do RT → bloqueia (422 `RECONCILIACAO_PENDENTE_DECISAO_RT`) sem
persistir nada (INV-CER-EMISSAO-001 / NC-03).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from uuid import UUID, uuid4

from src.domain.metrologia.calibracao.entities import (
    CalibracaoSnapshot,
    OrcamentoPorPontoSnapshot,
)
from src.domain.metrologia.calibracao.enums import EstadoCalibracao
from src.domain.metrologia.certificados.entities import (
    CertificadoSnapshot,
    PontoReconciliadoSnapshot,
)
from src.domain.metrologia.certificados.enums import (
    ClassificacaoPonto,
    DecisaoReconciliacaoRT,
    EstadoCertificado,
    TipoAcreditacao,
)
from src.domain.metrologia.certificados.erros import (
    CalibracaoNaoAprovadaError,
    CertificadoJaEmitidoError,
    FaixaDeclaradaAusenteError,
)
from src.domain.metrologia.certificados.portas import CmcParaPort
from src.domain.metrologia.certificados.reconciliacao import (
    PontoMedido,
    reconciliar_pontos,
)
from src.domain.metrologia.certificados.reconciliacao_hash import reconciliacao_hash
from src.domain.metrologia.certificados.repository import (
    AnaliseReconciliacaoRepository,
    CertificadoRepository,
)
from src.domain.metrologia.certificados.transicoes import (
    aplicar_decisoes_rt,
    perfil_e_acreditado,
    validar_completude_decisoes_rt,
)

_VERSAO_RECONCILIACAO = "1.0.0"


@dataclass(frozen=True, slots=True)
class EmitirCertificadoInput:
    tenant_id: UUID
    calibracao: CalibracaoSnapshot
    pontos_medidos: Sequence[PontoMedido]
    orcamentos_por_ponto: Sequence[OrcamentoPorPontoSnapshot]
    perfil: str  # server-side (ADR-0067), nunca do body
    numero_interno: int
    numero_certificado: str
    snapshot_padroes_usados_json: Sequence[Mapping[str, object]]
    data_emissao: date
    emitido_em: datetime
    correlation_id: UUID
    cmc_para: CmcParaPort | None = None  # None ⇒ emissão NÃO-RBC
    versao: int = 1
    versao_anterior_id: UUID | None = None


def emitir_certificado(
    inp: EmitirCertificadoInput,
    *,
    cert_repo: CertificadoRepository,
    analise_repo: AnaliseReconciliacaoRepository,
) -> CertificadoSnapshot:
    cal = inp.calibracao

    # 1. INV-CER-EMISSAO-001 — só calibração APROVADA.
    if cal.status is not EstadoCalibracao.APROVADA:
        raise CalibracaoNaoAprovadaError(
            f"calibração {cal.id} em {cal.status.value} — só APROVADA emite (2ª conferência)"
        )

    # Idempotência: 1 certificado por (tenant, calibração, versão).
    if cert_repo.existe_chave(
        tenant_id=inp.tenant_id, calibracao_id=cal.id, versao=inp.versao
    ):
        raise CertificadoJaEmitidoError(
            f"certificado já existe para calibração {cal.id} versão {inp.versao}"
        )

    # 2. Faixa declarada presente (ADR-0076 — CGCRE não extrapola).
    if cal.grandeza_calibrada is None or cal.faixa_calibrada_declarada is None:
        raise FaixaDeclaradaAusenteError(
            f"calibração {cal.id} sem grandeza/faixa declarada — não reconciliável"
        )

    # 3. Reconciliação ponto-a-ponto (puro).
    rec = reconciliar_pontos(
        pontos_medidos=inp.pontos_medidos,
        orcamentos_por_ponto=inp.orcamentos_por_ponto,
        faixa_declarada=cal.faixa_calibrada_declarada,
        grandeza=cal.grandeza_calibrada,
        cmc_para=inp.cmc_para,
        data_emissao=inp.data_emissao,
        tenant_id=inp.tenant_id,
    )

    # 4. Decisões do RT já tomadas (pré-condição).
    decisoes = analise_repo.obter_decisao_por_ponto(
        tenant_id=inp.tenant_id, calibracao_id=cal.id
    )

    # 5. Completude (perfil A bloqueia ponto não-RBC sem decisão — NC-03).
    validar_completude_decisoes_rt(
        pontos_nao_rbc=[p.ponto_calibracao for p in rec.pontos_nao_rbc],
        pontos_com_decisao=list(decisoes.keys()),
        perfil=inp.perfil,
    )

    # 6. Aplica decisões (EXCLUIR/EMITIR_NAO_RBC/ABORTAR→erro).
    pontos_finais = aplicar_decisoes_rt(rec.pontos, decisoes)

    # 7. Tipo de acreditação do certificado (cl. 8.1.3 / ADR-0075).
    incluidos = [p for p in pontos_finais if p.incluido_no_certificado]
    tem_rbc = any(p.classificacao is ClassificacaoPonto.RBC_OK for p in incluidos)
    tipo = (
        TipoAcreditacao.RBC
        if (perfil_e_acreditado(inp.perfil) and tem_rbc)
        else TipoAcreditacao.NAO_RBC
    )

    # 8. faixa_certificado dos pontos VÁLIDOS (metadado — INV-CER-RECONCILIA-003).
    validos = [p.ponto_calibracao for p in incluidos]
    faixa_min = min(validos) if validos else None
    faixa_max = max(validos) if validos else None

    # 9. Snapshots WORM (ressalva por ponto vem da decisão EMITIR_NAO_RBC_NO_PONTO).
    cert_id = uuid4()
    pontos_snap: list[PontoReconciliadoSnapshot] = []
    for p in pontos_finais:
        dec = decisoes.get(p.ponto_calibracao)
        ressalva = (
            dec.ressalva_nao_rbc
            if dec is not None
            and dec.decisao_rt is DecisaoReconciliacaoRT.EMITIR_NAO_RBC_NO_PONTO
            else ""
        )
        pontos_snap.append(
            PontoReconciliadoSnapshot.de_reconciliado(
                p, id=uuid4(), tenant_id=inp.tenant_id, certificado_id=cert_id,
                ressalva_nao_rbc=ressalva,
            )
        )

    rhash = reconciliacao_hash(
        pontos=pontos_snap,
        versao_reconciliacao=_VERSAO_RECONCILIACAO,
        faixa_certificado_min=faixa_min,
        faixa_certificado_max=faixa_max,
        tipo_acreditacao=tipo.value,
    )

    cert = CertificadoSnapshot(
        id=cert_id,
        tenant_id=inp.tenant_id,
        calibracao_id=cal.id,
        equipamento_id=cal.instrumento_id,
        numero_interno=inp.numero_interno,
        numero_certificado=inp.numero_certificado,
        versao=inp.versao,
        versao_anterior_id=inp.versao_anterior_id,
        status=EstadoCertificado.EMITIDO,
        perfil_emissor_no_momento=inp.perfil,
        faixa_certificado_min=faixa_min,
        faixa_certificado_max=faixa_max,
        tipo_acreditacao=tipo,
        snapshot_equipamento_json=cal.snapshot_equipamento_json,
        snapshot_padroes_usados_json=inp.snapshot_padroes_usados_json,
        cliente_ref_hash=cal.cliente_referencia_hash,
        reconciliacao_hash=rhash,
        emitido_em=inp.emitido_em,
        correlation_id=inp.correlation_id,
        regra_decisao_snapshot={"regra_decisao": cal.regra_decisao.value},
    )

    # 10. Persistência atômica (caller envolve em transaction.atomic).
    cert_repo.salvar_novo(cert, pontos_snap)
    return cert
