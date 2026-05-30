"""Use case `revisar_escopo` — US-ECMC-002 / AC-CAL-015-2 (M6 T-ECMC-022).

Revisão = INSERT de nova `versao` preservando a anterior (TL-C-07 — nunca UPDATE
in-place dos campos metrológicos, que são WORM). A chave natural (grandeza+faixa+
método) é preservada; só CMC/número/documento mudam. A versão anterior tem a
`vigencia_fim` encerrada no instante em que a nova passa a valer — calibrações já
configuradas sob a versão antiga continuam rastreáveis (auditoria retroativa
cl. 8.4 / RBC-NC-05). Use case PURO (ADR-0007).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import EstadoEscopo, FormaCMC
from src.domain.metrologia.escopos_cmc.repository import EscopoRepository


class EscopoNaoEncontradoError(Exception):
    def __init__(self, escopo_id: UUID) -> None:
        super().__init__(f"Escopo {escopo_id} não encontrado neste tenant.")


class EscopoNaoRevisavelError(Exception):
    """Só escopo CONFIRMADO pode ser revisado (revogado é terminal)."""

    def __init__(self, estado: str) -> None:
        super().__init__(f"Escopo em estado {estado} não pode ser revisado.")


class ConflitoVersaoError(Exception):
    """CAS — a versão anterior mudou concorrentemente (caller 409)."""


@dataclass(frozen=True, slots=True)
class RevisarEscopoInput:
    tenant_id: UUID
    escopo_id_atual: UUID  # versão vigente a ser revisada
    cmc_forma: FormaCMC
    cmc_valor: Decimal
    cmc_unidade: str
    vigencia_inicio: datetime  # quando a nova versão passa a valer
    correlation_id: UUID
    cmc_coef_relativo: Decimal | None = None
    numero_escopo_cgcre: str = ""
    documento_regulatorio_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.vigencia_inicio.tzinfo is None:
            raise ValueError("revisar_escopo: vigencia_inicio exige tz-aware (INV-VIG-004).")
        if self.cmc_valor <= 0:
            raise ValueError("revisar_escopo: cmc_valor deve ser > 0.")
        if self.cmc_forma is FormaCMC.RELATIVA_LINEAR and self.cmc_coef_relativo is None:
            raise ValueError("revisar_escopo: CMC RELATIVA_LINEAR exige cmc_coef_relativo.")


@dataclass(frozen=True, slots=True)
class RevisarEscopoOutput:
    nova_versao: EscopoCMCSnapshot
    anterior_id: UUID


def executar(inp: RevisarEscopoInput, repo: EscopoRepository) -> RevisarEscopoOutput:
    atual = repo.obter_por_id(inp.escopo_id_atual)
    if atual is None or atual.tenant_id != inp.tenant_id:
        raise EscopoNaoEncontradoError(inp.escopo_id_atual)
    if atual.estado is not EstadoEscopo.CONFIRMADO:
        raise EscopoNaoRevisavelError(atual.estado.value)

    # nova versão preserva a chave natural (grandeza/faixa/método) e o status RBC.
    nova = EscopoCMCSnapshot(
        id=uuid4(),
        tenant_id=atual.tenant_id,
        grandeza=atual.grandeza,
        faixa=atual.faixa,
        cmc_forma=inp.cmc_forma,
        cmc_valor=inp.cmc_valor,
        cmc_unidade=inp.cmc_unidade,
        rbc_acreditado=atual.rbc_acreditado,
        versao=atual.versao + 1,
        vigente_a_partir=inp.vigencia_inicio,
        estado=EstadoEscopo.CONFIRMADO,
        revision=0,
        vigencia_inicio=inp.vigencia_inicio,
        correlation_id=inp.correlation_id,
        cmc_coef_relativo=inp.cmc_coef_relativo,
        numero_escopo_cgcre=inp.numero_escopo_cgcre,
        procedimento_id=atual.procedimento_id,
        documento_regulatorio_id=inp.documento_regulatorio_id,
        origem=atual.origem,
    )
    repo.salvar_novo(nova)
    # encerra a vigência da versão anterior no instante em que a nova começa
    # (a anterior NÃO é apagada — WORM Padrão B — só deixa de ser vigente).
    if not repo.encerrar_vigencia(
        escopo_id=atual.id,
        vigencia_fim=inp.vigencia_inicio,
        revision_anterior=atual.revision,
    ):
        raise ConflitoVersaoError
    return RevisarEscopoOutput(nova_versao=nova, anterior_id=atual.id)
