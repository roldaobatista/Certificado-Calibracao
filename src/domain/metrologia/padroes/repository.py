"""Protocols dos repositorios do dominio padroes (M5 T-PAD-006).

Use cases consomem estes Protocols; adapters Django concretos vivem em
src/infrastructure/metrologia/padroes/repositories.py (Wave A P4 — ADR-0072).
Convencao M4: `obter_*` retorna snapshot ou None; mutacao da raiz via CAS
(`atualizar_com_lock`); filhas WORM via `salvar_*` (append-only).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from .entities import (
    AnaliseCartaControleSnapshot,
    IntercomparacaoPTSnapshot,
    PadraoMetrologicoSnapshot,
    RecalExternoPadraoSnapshot,
    VerificacaoIntermediariaSnapshot,
    VinculoAuxiliarSnapshot,
)


@runtime_checkable
class PadraoRepository(Protocol):
    """Raiz do agregado. CAS optimistic via `revision` (plan D-PAD-1)."""

    def obter_por_id(self, padrao_id: UUID) -> PadraoMetrologicoSnapshot | None: ...

    def existe_numero_serie(self, tenant_id: UUID, numero_serie: str) -> bool:
        """INV-PAD-001 — UNIQUE (tenant, numero_serie)."""
        ...

    def salvar_novo(self, snapshot: PadraoMetrologicoSnapshot) -> None:
        """INSERT em EM_USO."""
        ...

    def atualizar_com_lock(
        self, snapshot: PadraoMetrologicoSnapshot, revision_anterior: int
    ) -> bool:
        """UPDATE CAS WHERE revision=esperada; rowcount=0 -> corrida (caller 409).

        NAO atualiza `incertezas_certificado`/`validade_*` — isso so via fluxo de
        recal (INV-PAD-006, trigger PG).
        """
        ...


@runtime_checkable
class RecalExternoRepository(Protocol):
    def salvar_novo(self, snapshot: RecalExternoPadraoSnapshot) -> None: ...

    def obter_por_id(self, recal_id: UUID) -> RecalExternoPadraoSnapshot | None: ...

    def ultimo_do_padrao(
        self, padrao_id: UUID
    ) -> RecalExternoPadraoSnapshot | None: ...

    def atualizar_retorno_e_aprovacao(
        self, snapshot: RecalExternoPadraoSnapshot
    ) -> None:
        """UPDATE controlado do retorno/aprovacao RT (imutavel pos-aprovacao)."""
        ...


@runtime_checkable
class VerificacaoIntermediariaRepository(Protocol):
    def salvar_nova(self, snapshot: VerificacaoIntermediariaSnapshot) -> None: ...

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[VerificacaoIntermediariaSnapshot]:
        """Ordenado por data_vi (alimenta a serie da carta Shewhart)."""
        ...


@runtime_checkable
class IntercomparacaoPTRepository(Protocol):
    def salvar_nova(self, snapshot: IntercomparacaoPTSnapshot) -> None: ...

    def obter_por_id(self, pt_id: UUID) -> IntercomparacaoPTSnapshot | None: ...

    def atualizar_resultado(self, snapshot: IntercomparacaoPTSnapshot) -> None: ...


@runtime_checkable
class AnaliseCartaControleRepository(Protocol):
    """Registro WORM da decisao Shewhart (ADR-0070 — INV-PAD-010)."""

    def salvar_nova(self, snapshot: AnaliseCartaControleSnapshot) -> None: ...

    def listar_por_padrao(
        self, padrao_id: UUID
    ) -> list[AnaliseCartaControleSnapshot]: ...


@runtime_checkable
class VinculoAuxiliarRepository(Protocol):
    """Vinculo temporal principal<->auxiliar (cl. 6.4.5 — C-8)."""

    def salvar_novo(self, snapshot: VinculoAuxiliarSnapshot) -> None: ...

    def listar_auxiliares_vigentes_de(
        self, padrao_principal_id: UUID
    ) -> list[VinculoAuxiliarSnapshot]: ...
