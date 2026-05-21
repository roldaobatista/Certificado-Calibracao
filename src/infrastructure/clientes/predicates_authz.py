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


# =============================================================
# T-CLI-109 — predicate `cliente.bloqueado_para_entrega`
# AC-CLI-004-10: calibração EM EXECUÇÃO (item no laboratório) é
# CONCLUÍDA mesmo com cliente bloqueado — ISO/IEC 17025 §7.1.1 + §7.8.1
# (dever técnico de finalizar e emitir relatório). O consumer
# `operacao/certificados` (Wave A — Marco futuro) consulta este
# predicate ANTES da entrega física do item/certificado: se True,
# roteia pra fluxo de RETENÇÃO FÍSICA (CC art. 644) sem afetar
# validade técnica. Predicate é semântica de DOMÍNIO, não ABAC —
# consumer chama direto (não via `AuthorizationProvider.can`).
# Fail-safe: cliente_id inválido / ausente no resource → retém por
# segurança (True, motivo_de_falha). Reter espúrio é reversível por
# operação humana; entregar a alguém bloqueado por inadimplência
# pode caracterizar descumprimento de cautela (CC art. 644).
# =============================================================


def cliente_bloqueado_para_entrega(resource: dict[str, Any]) -> tuple[bool, str]:
    """Consulta de domínio — está o cliente bloqueado pra fins de entrega física?

    Retorna `(True, motivo)` se consumer Wave A `operacao/certificados`
    deve aplicar retenção física do item/certificado; `(False, "")` se
    pode entregar normalmente.

    Motivos estáveis (contratuais com consumer):
    - `cliente_bloqueado_manual`: bloqueio comercial manual.
    - `cliente_bloqueado_inadimplencia`: bloqueio automático D+90.
    - `cliente_id_invalido`: resource trouxe valor não-UUID (fail-safe).
    - `cliente_id_ausente`: resource sem chave `cliente_id` (fail-safe).
    """
    cliente_id_raw = resource.get("cliente_id")
    if cliente_id_raw is None:
        # Fail-safe: consumer chamou sem cliente_id — retém.
        return True, "cliente_id_ausente"

    try:
        cliente_uuid = UUID(str(cliente_id_raw))
    except (ValueError, TypeError):
        return True, "cliente_id_invalido"

    # Import tardio — apps loading
    from src.infrastructure.clientes.models import ClienteBloqueio

    ativo = (
        ClienteBloqueio.objects.filter(cliente_id=cliente_uuid, desbloqueado_em__isnull=True)
        .only("motivo_categoria")
        .first()
    )
    if ativo is None:
        return False, ""

    motivo = ativo.motivo_categoria
    if motivo.startswith("automatico_"):
        return True, "cliente_bloqueado_inadimplencia"
    return True, "cliente_bloqueado_manual"


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
