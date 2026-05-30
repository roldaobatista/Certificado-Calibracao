"""Use case `cadastrar_escopo` — US-ECMC-001 / US-ECMC-007 (M6 T-ECMC-020/021).

Cadastra um EscopoCMC novo (versão 1) em estado CONFIRMADO. Use case PURO
(ADR-0007): Input frozen + Repository Protocol. Perfil A declara escopo RBC
(`rbc_acreditado=True`); perfis B/C/D declaram capacidade interna (forçado
`False` — anti-fraude INV-ECMC-002/INV-015, ADR-0075). RBC exige `procedimento_id`
(T-ECMC-007). NÃO chama AuthorizationProvider (caller=guard).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import (
    EstadoEscopo,
    FormaCMC,
    OrigemEscopo,
)
from src.domain.metrologia.escopos_cmc.repository import EscopoRepository
from src.domain.metrologia.escopos_cmc.transicoes import rbc_efetivo
from src.domain.metrologia.value_objects import FaixaMedicao, Grandeza


class ChaveDuplicadaError(Exception):
    """INV-ECMC-001 — já existe escopo v1 para esta (grandeza, faixa, método)."""

    def __init__(self) -> None:
        super().__init__(
            "INV-ECMC-001: já existe escopo para esta grandeza+faixa+método "
            "(use revisar para criar nova versão)."
        )


class ProcedimentoObrigatorioParaRBCError(Exception):
    """T-ECMC-007 — escopo RBC (perfil A) exige procedimento (método)."""

    def __init__(self) -> None:
        super().__init__(
            "T-ECMC-007: escopo acreditado RBC exige procedimento_id (1 método por "
            "linha de escopo — NIT-DICLA-021)."
        )


@dataclass(frozen=True, slots=True)
class CadastrarEscopoInput:
    """Payload de cadastro de escopo/capacidade."""

    tenant_id: UUID
    grandeza: Grandeza
    faixa: FaixaMedicao
    cmc_forma: FormaCMC
    cmc_valor: Decimal
    cmc_unidade: str
    perfil: str  # perfil regulatório do tenant (A/B/C/D) — server-side, NUNCA payload
    rbc_solicitado: bool  # intenção; rbc_efetivo força False se perfil != A
    vigencia_inicio: datetime
    correlation_id: UUID
    cmc_coef_relativo: Decimal | None = None
    numero_escopo_cgcre: str = ""
    procedimento_id: UUID | None = None
    documento_regulatorio_id: UUID | None = None
    origem: OrigemEscopo = OrigemEscopo.MANUAL

    def __post_init__(self) -> None:
        if self.vigencia_inicio.tzinfo is None:
            raise ValueError(
                "cadastrar_escopo: vigencia_inicio exige datetime tz-aware (INV-VIG-004)."
            )
        if not self.cmc_unidade.strip():
            raise ValueError("cadastrar_escopo: cmc_unidade obrigatória.")
        if self.cmc_valor <= 0:
            raise ValueError("cadastrar_escopo: cmc_valor deve ser > 0.")
        if self.cmc_forma is FormaCMC.RELATIVA_LINEAR and self.cmc_coef_relativo is None:
            raise ValueError(
                "cadastrar_escopo: CMC RELATIVA_LINEAR exige cmc_coef_relativo (ADR-0074)."
            )


@dataclass(frozen=True, slots=True)
class CadastrarEscopoOutput:
    snapshot: EscopoCMCSnapshot


def executar(
    inp: CadastrarEscopoInput, repo: EscopoRepository
) -> CadastrarEscopoOutput:
    """Cadastra o escopo v1 CONFIRMADO após aplicar rbc_efetivo + INV-ECMC-001."""
    rbc = rbc_efetivo(rbc_solicitado=inp.rbc_solicitado, perfil=inp.perfil)
    if rbc and inp.procedimento_id is None:
        raise ProcedimentoObrigatorioParaRBCError

    if repo.existe_chave_confirmada(
        tenant_id=inp.tenant_id,
        grandeza=inp.grandeza,
        faixa=inp.faixa,
        procedimento_id=inp.procedimento_id,
        versao=1,
    ):
        raise ChaveDuplicadaError

    snapshot = EscopoCMCSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        grandeza=inp.grandeza,
        faixa=inp.faixa,
        cmc_forma=inp.cmc_forma,
        cmc_valor=inp.cmc_valor,
        cmc_unidade=inp.cmc_unidade,
        rbc_acreditado=rbc,
        versao=1,
        vigente_a_partir=inp.vigencia_inicio,
        estado=EstadoEscopo.CONFIRMADO,
        revision=0,
        vigencia_inicio=inp.vigencia_inicio,
        correlation_id=inp.correlation_id,
        cmc_coef_relativo=inp.cmc_coef_relativo,
        numero_escopo_cgcre=inp.numero_escopo_cgcre,
        procedimento_id=inp.procedimento_id,
        documento_regulatorio_id=inp.documento_regulatorio_id,
        origem=inp.origem,
    )
    repo.salvar_novo(snapshot)
    return CadastrarEscopoOutput(snapshot=snapshot)
