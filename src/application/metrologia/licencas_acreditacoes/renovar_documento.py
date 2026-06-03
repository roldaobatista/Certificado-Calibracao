"""Use case `renovar_documento` — US-LIC-002/004 (M9 T-LIC-042).

Cria uma nova `RevisaoDocumento` (RENOVACAO/RETIFICACAO) append-only, avança a
vigência da raiz (`atualizar_vigencia_cache`), AUTO-RESOLVE bloqueios ativos do
documento e cancela alertas PENDENTES (o job reagenda na nova vigência). NÃO toca o
cache `Tenant.acreditacao_*` — a renovação da acreditação CGCRE no cache é feita por
`aplicar_evento_cgcre(renovacao_vigencia_cgcre)` no caller (D-LIC-3). Use case PURO.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
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
