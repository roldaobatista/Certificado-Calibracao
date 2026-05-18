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


# =============================================================
# US-CLI-003 R4 tech-lead — tenant_nao_suspenso (STUB)
# ADR-0015 fluxo 3 ainda nao tem campo `modo_suspensao` no Tenant; aqui
# registramos o CONTRATO (predicate existe + decisao passa por ele) pra
# que Wave A nao precise re-introduzir a checagem em outro lugar.
# Mantemos `allowed=True` ate ADR-0015 entrar — TODO removivel quando
# campo existir.
# =============================================================


def tenant_nao_suspenso(
    resource: dict[str, Any] | None = None,
    tenant_id: UUID | None = None,
) -> tuple[bool, str]:
    """Predicate ABAC — INV-INT-009 (suspensao de tenant desliga features).

    Stub atual: retorna sempre (True, "") porque ADR-0015 fluxo 3 ainda nao
    foi implementado. Quando entrar, consulta `Tenant.modo_suspensao` e
    nega com reason `tenant_suspenso_bloqueado_total` ou similar.

    Usado por `clientes.importar`. Quando ADR-0015 estiver pronto, basta
    trocar o corpo deste predicate — view e use case nao mudam.
    """
    # TODO(US-ADR-0015 fluxo 3): trocar pelo lookup real em Tenant.modo_suspensao.
    return True, ""
