"""T-CAL-107 — OrcamentoIncertezaQueryService.

Agrega OrcamentoIncerteza + componentes (1:N) + breakdown por ponto
em UM resultado pra UI do orcamento detalhado / painel revisor.

Budget de performance: <= 300ms na implementacao Django (Fase 8) com
prefetch_related aninhado componentes+pontos. Aqui apenas a funcao
pura sobre snapshots.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from src.domain.metrologia.calibracao.entities import (
    ComponenteIncertezaSnapshot,
    OrcamentoIncertezaSnapshot,
)


@dataclass(frozen=True, slots=True)
class OrcamentoDetalhe:
    """Snapshot consolidado de um orcamento para UI."""

    orcamento: OrcamentoIncertezaSnapshot
    componentes: tuple[ComponenteIncertezaSnapshot, ...]  # ordem por nome
    componentes_tipo_a: tuple[ComponenteIncertezaSnapshot, ...]
    componentes_tipo_b: tuple[ComponenteIncertezaSnapshot, ...]
    pares_correlacionados: tuple[tuple[UUID, UUID], ...]  # (comp_id, comp_correlato_id)

    @property
    def total_componentes(self) -> int:
        return len(self.componentes)

    @property
    def tem_divergencia_algoritmos(self) -> bool:
        """Algoritmo 2 (MC) rodou e divergiu mais que zero da algoritmo 1 (GUM)."""
        if self.orcamento.divergencia_pct is None:
            return False
        return self.orcamento.divergencia_pct > Decimal("0")

    @property
    def tem_bias_orcado(self) -> bool:
        return self.orcamento.bias_orcado is not None


def executar(
    *,
    orcamento_id: UUID,
    orcamento: OrcamentoIncertezaSnapshot,
    componentes: list[ComponenteIncertezaSnapshot],
) -> OrcamentoDetalhe:
    """Agrega orcamento + componentes em snapshot de leitura.

    Filtra defensivamente: caller pode passar listas globais; isolamos
    apenas o que pertence ao orcamento + tenant.
    """
    if orcamento.id != orcamento_id:
        raise ValueError(
            f"orcamento: orcamento_id={orcamento_id} != orcamento.id={orcamento.id}"
        )

    tenant = orcamento.tenant_id

    componentes_filtrados = sorted(
        (
            c
            for c in componentes
            if c.tenant_id == tenant and c.orcamento_incerteza_id == orcamento_id
        ),
        key=lambda c: c.nome_componente,
    )

    tipo_a = tuple(c for c in componentes_filtrados if c.tipo_componente == "A")
    tipo_b = tuple(c for c in componentes_filtrados if c.tipo_componente == "B")

    pares: list[tuple[UUID, UUID]] = []
    for c in componentes_filtrados:
        if c.correlacao_com_componente_id is not None:
            pares.append((c.id, c.correlacao_com_componente_id))

    return OrcamentoDetalhe(
        orcamento=orcamento,
        componentes=tuple(componentes_filtrados),
        componentes_tipo_a=tipo_a,
        componentes_tipo_b=tipo_b,
        pares_correlacionados=tuple(pares),
    )
