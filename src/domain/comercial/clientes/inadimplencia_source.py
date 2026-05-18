"""Protocol pra fonte de inadimplencia (US-CLI-004 — TL5 + ADR-0007).

Wave A do `financeiro/contas-receber` implementa o adapter real (lendo
TituloVencido). Por enquanto, adapter mock (lendo dict de settings) cumpre
o contrato.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator, Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class InadimplenciaItem:
    """1 linha do iterador: cliente inadimplente >= 90 dias.

    causation_id liga ao titulo vencido (FK em Wave A).
    """

    tenant_id: UUID
    cliente_id: UUID
    dias_vencido: int
    causation_titulo_id: UUID


@runtime_checkable
class InadimplenciaSource(Protocol):
    """Iterador de clientes inadimplentes >= 90 dias."""

    def iter_inadimplentes_90d(self) -> Iterator[InadimplenciaItem]:
        ...
