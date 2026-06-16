"""Protocol pra fonte de inadimplencia (US-CLI-004 — TL5 + ADR-0007).

Wave A do `financeiro/contas-receber` implementa o adapter real (lendo
TituloVencido). Por enquanto, adapter mock (lendo dict de settings) cumpre
o contrato.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from uuid import UUID


@dataclass(frozen=True)
class InadimplenciaItem:
    """1 linha do iterador: cliente inadimplente alem do grace por perfil.

    causation_id liga ao titulo vencido (FK em Wave A).

    `perfil`/`grace_perfil` (PLAN-CR-01): snapshot do perfil regulatorio do tenant
    e do grace aplicado (45/20/30/7) pelo adapter real de `contas_receber`. Optional
    com default seguro (None) — o `SourceListaInterim` legado e deploys parciais em
    que o wiring ainda aponta pro source interino NAO quebram (campos preenchidos
    pelo adapter real; consumidores tratam None como "perfil nao informado").
    """

    tenant_id: UUID
    cliente_id: UUID
    dias_vencido: int
    causation_titulo_id: UUID
    perfil: str | None = None
    grace_perfil: int | None = None


@runtime_checkable
class InadimplenciaSource(Protocol):
    """Iterador de clientes inadimplentes >= 90 dias."""

    def iter_inadimplentes_90d(self) -> Iterator[InadimplenciaItem]: ...
