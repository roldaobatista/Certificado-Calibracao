"""Helpers para jobs multi-tenant (T-EQP-054 / P-EQP-T9).

ADR-0002 §6 + memoria `feedback_sem_codigo_descartavel`: codigo que
itera tenants deve ser unico ponto, NUNCA duplicado por job. Jobs
ativam tenant_ids contexto + run_in_tenant_context dentro do loop.

API:
- `processar_em_contexto_tenant(funcao, tenants=None) -> dict[UUID, T]`
- `iter_tenants_ativos() -> Iterable[Tenant]`

Marco 2: chamado por management commands (`processar_provisorios_
expirados`, `marcar_equipamentos_orfaos`, `alertar_aprovacoes_d1_
equipamento`). Wave A: Procrastinate task fan-out (1 task por tenant).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypeVar
from uuid import UUID

from src.infrastructure.multitenant.connection import run_in_tenant_context
from src.infrastructure.tenant.models import Tenant

T = TypeVar("T")


def iter_tenants_ativos() -> Iterable[Tenant]:
    """Itera todos os tenants (sem filtro de status Marco 2).

    Wave A: filtrar `Tenant.status='ativo'` quando Onboarding (ADR-0015)
    introduzir maquina de estados de tenant.
    """
    return Tenant.objects.all()


def processar_em_contexto_tenant(
    funcao: Callable[[Tenant], T],
    *,
    tenants: Iterable[Tenant] | None = None,
) -> dict[UUID, T]:
    """Roda `funcao(tenant)` em `run_in_tenant_context(tenant.id)` para
    cada tenant em `tenants` (ou todos se None).

    Retorna `{tenant_id: resultado}`. Caller decide o que fazer com
    cada resultado.

    Excecoes dentro de `funcao` propagam — caller responsabiliza-se
    por capturar+logar quando convem isolar 1 tenant ruim.
    """
    alvos = list(tenants) if tenants is not None else list(iter_tenants_ativos())
    resultados: dict[UUID, T] = {}
    for tenant in alvos:
        with run_in_tenant_context(tenant.id):
            resultados[tenant.id] = funcao(tenant)
    return resultados
