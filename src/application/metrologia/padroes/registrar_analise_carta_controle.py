"""Use case `registrar_analise_carta_controle` — US-PAD-008 (M5 T-PAD-026).

Registra a DECISAO do RT sobre uma violacao Western Electric detectada na carta
Shewhart (ADR-0070 — registro WORM congelado, INV-PAD-010). EXCLUSIVO perfil A
(INV-PAD-008). Congela LC/UCL/LCL/sigma + `versao_motor_shewhart` (cl. 7.11) +
decisao + justificativa canonicalizada + hash — reconstruivel em auditoria
CGCRE (cl. 8.4). NAO copia os pontos (referencia VIs/recais por id).

Apos esta analise, a porta `padrao_bloqueado_para_uso` (P4) considera o padrao
liberado SO se a decisao for ACEITO_COM_JUSTIFICATIVA (DecisaoRTCarta.libera_uso);
RECALIBRAR/SUSPENDER_USO mantem bloqueio logico (INV-PAD-010). Este use case
nao muta a maquina de estados (nao ha estado "suspenso" — o bloqueio e logico).

Use case PURO.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from src.domain.metrologia.padroes.entities import AnaliseCartaControleSnapshot
from src.domain.metrologia.padroes.enums import DecisaoRTCarta, RegraWesternElectric
from src.domain.metrologia.padroes.repository import (
    AnaliseCartaControleRepository,
    PadraoRepository,
)

from .registrar_recal_envio import PadraoNaoEncontradoError


class PerfilNaoPermiteCartaError(Exception):
    """INV-PAD-008 — cartas Shewhart exclusivas perfil A."""

    def __init__(self) -> None:
        super().__init__(
            "INV-PAD-008: carta de controle Shewhart e exclusiva de tenant "
            "perfil A (laboratorio acreditado — ADR-0067)."
        )


@dataclass(frozen=True, slots=True)
class RegistrarAnaliseCartaInput:
    tenant_id: UUID
    padrao_id: UUID
    regra_violada: RegraWesternElectric
    pontos_referenciados_ids: tuple[UUID, ...]
    linha_central: Decimal
    ucl: Decimal
    lcl: Decimal
    sigma: Decimal
    n_pontos: int
    janela_meses: int
    versao_motor_shewhart: str
    decisao_rt: DecisaoRTCarta
    justificativa_canonicalizada: str
    justificativa_hash: str
    criado_em: datetime
    tenant_e_perfil_a: bool
    assinatura_a3_rt_id: UUID | None = None

    def __post_init__(self) -> None:
        if self.criado_em.tzinfo is None:
            raise ValueError("criado_em exige datetime tz-aware (INV-VIG-004).")
        if not self.pontos_referenciados_ids:
            raise ValueError(
                "analise da carta exige >=1 ponto referenciado (VIs/recais)."
            )
        if not self.justificativa_canonicalizada or not self.justificativa_hash:
            raise ValueError(
                "decisao do RT exige justificativa canonicalizada + hash "
                "(ADR-0029 — registro probatorio)."
            )
        if self.versao_motor_shewhart == "":
            raise ValueError(
                "versao_motor_shewhart obrigatoria (cl. 7.11 — replay CGCRE)."
            )


@dataclass(frozen=True, slots=True)
class RegistrarAnaliseCartaOutput:
    analise: AnaliseCartaControleSnapshot


def executar(
    inp: RegistrarAnaliseCartaInput,
    repo_padrao: PadraoRepository,
    repo_analise: AnaliseCartaControleRepository,
) -> RegistrarAnaliseCartaOutput:
    if not inp.tenant_e_perfil_a:
        raise PerfilNaoPermiteCartaError
    padrao = repo_padrao.obter_por_id(inp.padrao_id)
    if padrao is None:
        raise PadraoNaoEncontradoError(inp.padrao_id)

    analise = AnaliseCartaControleSnapshot(
        id=uuid4(),
        tenant_id=inp.tenant_id,
        padrao_id=inp.padrao_id,
        regra_violada=inp.regra_violada,
        pontos_referenciados_ids=inp.pontos_referenciados_ids,
        linha_central=inp.linha_central,
        ucl=inp.ucl,
        lcl=inp.lcl,
        sigma=inp.sigma,
        n_pontos=inp.n_pontos,
        janela_meses=inp.janela_meses,
        versao_motor_shewhart=inp.versao_motor_shewhart,
        decisao_rt=inp.decisao_rt,
        justificativa_canonicalizada=inp.justificativa_canonicalizada,
        justificativa_hash=inp.justificativa_hash,
        criado_em=inp.criado_em,
        assinatura_a3_rt_id=inp.assinatura_a3_rt_id,
    )
    repo_analise.salvar_nova(analise)
    return RegistrarAnaliseCartaOutput(analise=analise)
