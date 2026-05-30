"""Use case `confirmar_escopo_extraido` — M6 Fatia 4 (T-ECMC-052).

A conferência humana revisou o staging (`EscopoExtraido`) e devolve as linhas
APROVADAS já NORMALIZADAS (grandeza no enum, faixa Decimal, unidade na whitelist,
CMC) como `CadastrarEscopoInput`. Cada linha aprovada vira uma linha CONFIRMADA em
`escopo_cmc` (WORM) — REUSA `cadastrar_escopo` (não duplica rbc_efetivo/INV-ECMC-001/
procedimento RBC). Marca o staging confirmado (quem/quando — audit). Ação authz
`escopos_cmc.confirmar_extraido` (caller=guard).

Puro (ADR-0007). Atomicidade (criar N escopos + marcar confirmado) é do caller
(view envolve em transaction.atomic). INV-ECMC-007: só aqui um extraído promove.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from uuid import UUID

from src.application.metrologia.escopos_cmc.cadastrar_escopo import (
    CadastrarEscopoInput,
)
from src.application.metrologia.escopos_cmc.cadastrar_escopo import (
    executar as cadastrar_executar,
)
from src.domain.metrologia.escopos_cmc.entities import EscopoCMCSnapshot
from src.domain.metrologia.escopos_cmc.enums import OrigemEscopo
from src.domain.metrologia.escopos_cmc.repository import (
    EscopoExtraidoRepository,
    EscopoRepository,
)


class ExtraidoNaoEncontrado(Exception):
    """ID de staging não existe no tenant (RLS já filtrou) — caller 404."""


class ExtraidoJaConfirmado(Exception):
    """One-shot — staging já promovido (INV-ECMC-007). Caller 409."""


@dataclass(frozen=True, slots=True)
class ConfirmarEscopoExtraidoInput:
    extraido_id: UUID
    tenant_id: UUID
    confirmado_por_id_hash: str  # quem confirmou (audit — HashVersionado)
    confirmado_em: datetime
    escopos: tuple[CadastrarEscopoInput, ...]  # linhas aprovadas+normalizadas

    def __post_init__(self) -> None:
        if self.confirmado_em.tzinfo is None:
            raise ValueError(
                "confirmar_escopo_extraido: confirmado_em exige tz-aware (INV-VIG-004)."
            )
        if not self.confirmado_por_id_hash.strip():
            raise ValueError(
                "confirmar_escopo_extraido: confirmado_por_id_hash obrigatório (audit)."
            )
        if not self.escopos:
            raise ValueError(
                "confirmar_escopo_extraido: nenhuma linha aprovada para confirmar."
            )


@dataclass(frozen=True, slots=True)
class ConfirmarEscopoExtraidoOutput:
    extraido_id: UUID
    confirmados: tuple[EscopoCMCSnapshot, ...]


def executar(
    inp: ConfirmarEscopoExtraidoInput,
    repo_extraido: EscopoExtraidoRepository,
    repo_escopo: EscopoRepository,
) -> ConfirmarEscopoExtraidoOutput:
    """Promove o staging: cria N escopos CONFIRMADO (origem=EXTRACAO_PDF) + marca
    confirmado. Levanta ExtraidoNaoEncontrado/ExtraidoJaConfirmado; propaga
    ChaveDuplicadaError/ProcedimentoObrigatorioParaRBCError do cadastro."""
    staging = repo_extraido.obter_por_id(inp.extraido_id)
    if staging is None or staging.tenant_id != inp.tenant_id:
        raise ExtraidoNaoEncontrado(str(inp.extraido_id))
    if staging.confirmado_em is not None:
        raise ExtraidoJaConfirmado(str(inp.extraido_id))

    confirmados: list[EscopoCMCSnapshot] = []
    for linha in inp.escopos:
        # Proveniência forçada EXTRACAO_PDF (não confiar no payload) + tenant do staging.
        linha_pdf = replace(
            linha, origem=OrigemEscopo.EXTRACAO_PDF, tenant_id=inp.tenant_id
        )
        out = cadastrar_executar(linha_pdf, repo_escopo)
        confirmados.append(out.snapshot)

    marcado = repo_extraido.marcar_confirmado(
        extraido_id=inp.extraido_id,
        confirmado_em=inp.confirmado_em,
        por_id_hash=inp.confirmado_por_id_hash,
    )
    if not marcado:
        # Corrida: outro confirmou entre o obter e o marcar (one-shot perdido).
        raise ExtraidoJaConfirmado(str(inp.extraido_id))

    return ConfirmarEscopoExtraidoOutput(
        extraido_id=inp.extraido_id, confirmados=tuple(confirmados)
    )
