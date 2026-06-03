"""Use case `renovar_documento` — US-LIC-002/004 (M9 T-LIC-042 + T-LIC-050).

Cria uma nova `RevisaoDocumento` (RENOVACAO/RETIFICACAO) append-only, avança a
vigência da raiz (`atualizar_vigencia_cache`), AUTO-RESOLVE bloqueios ativos do
documento e cancela alertas PENDENTES (o job reagenda na nova vigência).

**Fatia 3 (T-LIC-050 / D-LIC-3 / ADR-0079):** quando o documento renovado é a
`ACREDITACAO_CGCRE` de um tenant perfil **A**, o use case SINCRONIZA o cache
`Tenant.acreditacao_vigencia_fim` (que o M8 lê) via porta `RenovarVigenciaCgcrePort`
→ `aplicar_evento_cgcre(renovacao_vigencia_cgcre)` (único caminho de mutação —
INV-LIC-VIG-SYNC-001; nunca UPDATE direto). Mantém o invariante de não-drift
`cache == fonte` (`vigencia_fim_acreditacao_cgcre` no query service). Para os demais
tipos/perfis a sincronização NÃO dispara (porta opcional). Use case PURO (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Protocol
from uuid import UUID, uuid4

from src.domain.metrologia.licencas_acreditacoes.entities import RevisaoDocumento
from src.domain.metrologia.licencas_acreditacoes.enums import MotivoRevisao
from src.domain.metrologia.licencas_acreditacoes.repository import (
    AlertaRepository,
    BloqueioRepository,
    DocumentoRegulatorioRepository,
    RevisaoRepository,
)
from src.domain.metrologia.licencas_acreditacoes.transicoes import validar_anexo

_PERFIL_ACREDITADO = "A"


class RenovarVigenciaCgcrePort(Protocol):
    """Porta para a função SECURITY DEFINER `aplicar_evento_cgcre`
    (direção `renovacao_vigencia_cgcre`) — renova a vigência da acreditação no cache
    `Tenant.acreditacao_vigencia_fim` SEM mudar o perfil (D-LIC-3). Roda na transação
    do caller (advisory lock por tenant é interno à função). Adapter real faz o raw
    cursor — testável com Fake."""

    def renovar_vigencia(
        self, *, tenant_id: UUID, vigencia_fim: date, motivo: str
    ) -> None: ...


class SincronizacaoCgcreAusenteError(Exception):
    """Renovação de ACREDITACAO_CGCRE de tenant A exige a porta de sincronização
    (erro de configuração do caller — a view sempre injeta o adapter real)."""


def _motivo_renovacao_cgcre(documento_id: UUID, vigencia_fim: date) -> str:
    """Motivo descritivo ≥100 chars exigido pelo CHECK de `aplicar_evento_cgcre`
    (auditável no `tenant_perfil_historico`). Sincronização unidirecional ADR-0079."""
    return (
        f"renovacao de vigencia da acreditacao CGCRE (documento {documento_id}) "
        f"sincronizando o cache Tenant.acreditacao_vigencia_fim para "
        f"{vigencia_fim.isoformat()} via aplicar_evento_cgcre (ADR-0079 / D-LIC-3 — "
        f"fonte rica Licenca, caminho oficial INV-LIC-VIG-SYNC-001)"
    )


class DocumentoNaoEncontradoError(Exception):
    """Documento não existe no tenant (404)."""


@dataclass(frozen=True, slots=True)
class RenovarDocumentoInput:
    tenant_id: UUID
    documento_id: UUID
    nova_vigencia_inicio: date
    nova_vigencia_fim: date
    anexo_id: UUID
    anexo_sha256: str
    motivo: MotivoRevisao
    criado_por: UUID
    criado_em: datetime
    correlation_id: UUID
    perfil: str = ""  # server-side (A/B/C/D) — dispara sync CGCRE só em A (ADR-0067)

    def __post_init__(self) -> None:
        if self.motivo is MotivoRevisao.CADASTRO_INICIAL:
            raise ValueError("renovar_documento: motivo não pode ser CADASTRO_INICIAL.")


@dataclass(frozen=True, slots=True)
class RenovarDocumentoOutput:
    revisao: RevisaoDocumento
    bloqueios_resolvidos: int
    alertas_cancelados: int


def executar(
    inp: RenovarDocumentoInput,
    *,
    doc_repo: DocumentoRegulatorioRepository,
    revisao_repo: RevisaoRepository,
    bloqueio_repo: BloqueioRepository,
    alerta_repo: AlertaRepository,
    cgcre_sync: RenovarVigenciaCgcrePort | None = None,
) -> RenovarDocumentoOutput:
    doc = doc_repo.obter_por_id(
        tenant_id=inp.tenant_id, documento_id=inp.documento_id
    )
    if doc is None:
        raise DocumentoNaoEncontradoError(str(inp.documento_id))
    validar_anexo(anexo_sha256=inp.anexo_sha256)

    numero = revisao_repo.proximo_numero_revisao(
        tenant_id=inp.tenant_id, documento_id=inp.documento_id
    )
    revisao = RevisaoDocumento(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        documento_id=inp.documento_id,
        numero_revisao=numero,
        data_emissao=inp.nova_vigencia_inicio,
        data_validade=inp.nova_vigencia_fim,
        anexo_id=inp.anexo_id,
        anexo_sha256=inp.anexo_sha256,
        motivo=inp.motivo,
        criado_em=inp.criado_em,
        criado_por=inp.criado_por,
    )
    revisao_repo.append(revisao)
    # Avança a vigência da raiz + recalcula status_cache (Padrão B mutável).
    doc_repo.atualizar_vigencia_cache(
        tenant_id=inp.tenant_id,
        documento_id=inp.documento_id,
        vigencia_inicio=inp.nova_vigencia_inicio,
        vigencia_fim=inp.nova_vigencia_fim,
    )
    # Sincronização Licenca(CGCRE) → cache (ADR-0079 / D-LIC-3): só acreditação CGCRE
    # de tenant A renova o cache `Tenant.acreditacao_vigencia_fim` (que o M8 lê), via
    # a função canônica (nunca UPDATE direto — INV-LIC-VIG-SYNC-001).
    if doc.tipo.e_acreditacao_cgcre and inp.perfil == _PERFIL_ACREDITADO:
        if cgcre_sync is None:
            raise SincronizacaoCgcreAusenteError(
                "renovação de ACREDITACAO_CGCRE de tenant A exige a porta "
                "RenovarVigenciaCgcrePort (caller deve injetar o adapter real)."
            )
        cgcre_sync.renovar_vigencia(
            tenant_id=inp.tenant_id,
            vigencia_fim=inp.nova_vigencia_fim,
            motivo=_motivo_renovacao_cgcre(inp.documento_id, inp.nova_vigencia_fim),
        )
    # Auto-resolve bloqueios + cancela alertas pendentes (job reagenda).
    bloqueios = bloqueio_repo.resolver_ativos(
        tenant_id=inp.tenant_id,
        documento_id=inp.documento_id,
        em=inp.criado_em.date(),
    )
    alertas = alerta_repo.cancelar_pendentes(
        tenant_id=inp.tenant_id, documento_id=inp.documento_id
    )
    return RenovarDocumentoOutput(
        revisao=revisao, bloqueios_resolvidos=bloqueios, alertas_cancelados=alertas
    )
