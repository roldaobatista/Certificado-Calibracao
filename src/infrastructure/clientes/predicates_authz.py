"""Predicates ABAC do modulo clientes (US-CLI-004 TL2 + INV-INT-010).

`cliente_nao_bloqueado`: se resource carrega `cliente_id`, valida que o cliente
nao esta bloqueado comercialmente. Caso esteja bloqueado, retorna denied com
reason explicando.

Como modulos Wave A (OS, orcamentos, agenda) consomem:
  provider.can(
      usuario_id=u, action="os.criar",
      resource={"cliente_id": str(c.id)},
      tenant_id=t,
  )
"""

from __future__ import annotations

from typing import Any
from uuid import UUID


def cliente_nao_bloqueado(resource: dict[str, Any]) -> tuple[bool, str]:
    """Predicate ABAC — INV-INT-010.

    Retorna (True, "") se nao aplica (resource sem cliente_id) ou cliente
    nao bloqueado. (False, "<reason>") se bloqueado.
    """
    cliente_id_raw = resource.get("cliente_id")
    if cliente_id_raw is None:
        return True, ""  # nao aplica

    try:
        cliente_uuid = UUID(str(cliente_id_raw))
    except (ValueError, TypeError):
        return False, "cliente_id_invalido"

    # Import tardio — apps loading
    from src.infrastructure.clientes.models import ClienteBloqueio

    ativo = (
        ClienteBloqueio.objects.filter(
            cliente_id=cliente_uuid, desbloqueado_em__isnull=True
        )
        .only("motivo_categoria")
        .first()
    )
    if ativo is None:
        return True, ""

    # Reason estavel — modulos consumidores entendem
    motivo = ativo.motivo_categoria
    if motivo.startswith("automatico_"):
        return False, "cliente_bloqueado_inadimplencia"
    return False, "cliente_bloqueado_manual"
