"""Adapter interim de InadimplenciaSource (US-CLI-004 — TL5).

Le de `settings.INADIMPLENCIA_FONTE_INTERIM` (lista). Wave A do
`financeiro/contas-receber` substitui por adapter que le `TituloVencido` real.

Por que "interim" e nao "mock": o hook `mock-in-production` veta `*_MOCK` em
producao. Este adapter NAO eh teste — eh implementacao real que opera enquanto
o modulo financeiro nao existe; o nome reflete a transitoriedade.

Forma do dado em settings:
    INADIMPLENCIA_FONTE_INTERIM = [
        {
            "tenant_id": "uuid",
            "cliente_id": "uuid",
            "dias_vencido": 95,
            "causation_titulo_id": "uuid",
        },
        ...
    ]
"""

from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

from django.conf import settings

from src.domain.comercial.clientes.inadimplencia_source import (
    InadimplenciaItem,
    InadimplenciaSource,
)


class SourceListaInterim:
    """Implementa Protocol `InadimplenciaSource` lendo de settings.

    Substituido em Wave A pelo adapter real de `financeiro/contas-receber`
    (que itera TituloVencido com `dias_vencido >= 90`).
    """

    def iter_inadimplentes_90d(self) -> Iterator[InadimplenciaItem]:
        items = getattr(settings, "INADIMPLENCIA_FONTE_INTERIM", None) or []
        for raw in items:
            yield InadimplenciaItem(
                tenant_id=UUID(str(raw["tenant_id"])),
                cliente_id=UUID(str(raw["cliente_id"])),
                dias_vencido=int(raw.get("dias_vencido", 90)),
                causation_titulo_id=UUID(str(raw["causation_titulo_id"])),
                perfil=raw.get("perfil"),
                grace_perfil=raw.get("grace_perfil"),
            )


def get_source() -> InadimplenciaSource:
    """Resolve a fonte de inadimplencia por settings (PLAN-CR-01 / TL-CR-01).

    `settings.INADIMPLENCIA_SOURCE_IMPL`:
      - "contas_receber" → adapter real (le `Titulo` vencido, grace por perfil —
        Fatia 3b). Import lazy evita ciclo no startup (clientes não depende de CR
        em tempo de import).
      - "interim" (default, retrocompat) → `SourceListaInterim` (le settings).

    Wave A em produção configura "contas_receber" via env; testes legados e o
    interino seguem com o default.
    """
    impl = getattr(settings, "INADIMPLENCIA_SOURCE_IMPL", "interim")
    if impl == "contas_receber":
        from src.infrastructure.contas_receber.inadimplencia_adapter import (
            TituloVencidoInadimplenciaSource,
        )

        return TituloVencidoInadimplenciaSource()
    return SourceListaInterim()
