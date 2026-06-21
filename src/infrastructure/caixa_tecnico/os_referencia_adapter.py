"""Adapter real do ``OSReferenciaPort`` (Fatia 3a — T-CT-042).

Seam de **leitura pura** sobre ``ordens_servico`` (módulo fechado — NÃO estende):
``OS.objects.filter(id=os_id, tenant_id=tenant_id).exists()`` (D-CT-11).

Cross-tenant → False (filtro defensivo + RLS). O vínculo OS↔despesa é rastro
histórico: a despesa NÃO segue cancelamento da OS (D-CT-11 / spec §7).

Refs: T-CT-042; D-CT-11; spec §7.
"""

from __future__ import annotations

from uuid import UUID


class OSReferenciaAdapter:
    """Implementação real de ``OSReferenciaPort`` sobre o model ``OS``."""

    def existe_os(self, os_id: UUID, tenant_id: UUID) -> bool:
        """True se a OS existe e pertence ao tenant; False caso contrário (inclui cross-tenant)."""
        from src.infrastructure.ordens_servico.models import OS

        return OS.objects.filter(id=os_id, tenant_id=tenant_id).exists()
