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
        ClienteBloqueio.objects.filter(cliente_id=cliente_uuid, desbloqueado_em__isnull=True)
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

    Consulta `Tenant.status_lifecycle` (criado na Foundation, com 3 valores:
    ATIVO/SUSPENSO/CANCELADO). Endereca CONCERN Seguranca 4 do Auditor
    Familia 5 em 2026-05-18 noite final — substituiu o stub anterior.

    Usado por `clientes.importar`. Outras actions de alto impacto (mesclar,
    bloquear) podem reusar quando ADR-0015 fluxo 3 estender o ciclo de vida
    (modos: ativo/aviso/restrito/bloqueado_total/cancelado).
    """
    if tenant_id is None:
        return True, ""  # nao aplica

    # Import tardio — apps loading
    from src.infrastructure.tenant.models import StatusLifecycle, Tenant

    tenant = Tenant.objects.filter(id=tenant_id).only("status_lifecycle").first()
    if tenant is None:
        return False, "tenant_nao_existe"
    if tenant.status_lifecycle == StatusLifecycle.SUSPENSO:
        return False, "tenant_suspenso"
    if tenant.status_lifecycle == StatusLifecycle.CANCELADO:
        return False, "tenant_cancelado"
    return True, ""
