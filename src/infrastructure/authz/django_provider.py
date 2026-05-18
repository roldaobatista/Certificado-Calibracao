"""Adapter `DjangoAuthorizationProvider` — implementa `AuthorizationProvider`.

Fluxo de `can()`:
1. Resolver perfis vigentes do usuário no tenant (`UsuarioPerfilTenant`
   com janela de validade).
2. Checar feature flag (se `action` mapeia pra uma feature).
3. Checar RBAC clássico (matriz `PerfilAcao`).
4. ABAC contextual — F-B só tem hook stub; Wave A liga atributos reais
   (acreditação vigente, treinamento matriz, etc).
5. GRAVAR `AuthzDecision` na mesma transação ANTES de retornar
   (INV-AUTHZ-002).
6. Retornar `AuthDecision` imutável.

Cache: `LocMemCache` Django nesta fase (decisão F-B — ver ADR-0012 §
"Ajustes na aceitação"). Redis vira backend em Wave A trocando só o
nome de cache em settings, sem mexer aqui.

Quem importa este módulo: `infrastructure/*` (apps Django, views, signals).
NÃO importar de `domain/*` — domain só conhece a porta.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any
from uuid import UUID

from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from src.domain.authz import AuthDecision, AuthorizationProvider

from .models import AuthzDecision, PerfilAcao


CACHE_TTL_SECS = 300  # 5 min — invalidação por evento entra em Wave A
CACHE_KEY_PREFIX = "authz:user"


def _cache_key(usuario_id: UUID, tenant_id: UUID | None) -> str:
    t = tenant_id.hex if tenant_id else "none"
    return f"{CACHE_KEY_PREFIX}:{usuario_id.hex}:tenant:{t}"


def invalidate_user_cache(usuario_id: UUID, tenant_id: UUID | None = None) -> None:
    """Forçar invalidação. Chamar quando UsuarioPerfilTenant muda.

    Wave A liga isso a evento `BillingSaas.PlanoMudouModulos` (INV-INT-008).
    """
    cache.delete(_cache_key(usuario_id, tenant_id))


def _canonicalizar_payload(payload: dict[str, Any]) -> str:
    """JSON ordenado pra hash determinístico — espelha audit/canonicalizar."""
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)


def _hash_linha(hash_anterior: str, payload: dict[str, Any]) -> str:
    base = hash_anterior + _canonicalizar_payload(payload)
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


class DjangoAuthorizationProvider:
    """Implementação Django/PG da porta `AuthorizationProvider`.

    Honra o Protocol `src.domain.authz.AuthorizationProvider` via
    duck-typing — não herda explicitamente porque Protocol+runtime_checkable
    permite isinstance() sem herança.
    """

    def can(
        self,
        usuario_id: UUID,
        action: str,
        resource: dict[str, Any] | None = None,
        tenant_id: UUID | None = None,
        purpose: str = "execucao_contrato",
        at_time: datetime | None = None,
    ) -> AuthDecision:
        resource = resource or {}
        agora = at_time or timezone.now()

        perfis = self._resolver_perfis_vigentes(usuario_id, tenant_id, agora)
        decision_intermediate = self._decidir(perfis, action, resource)

        # Grava audit ANTES de retornar — mesma transação, fail-loud se romper.
        # transaction.atomic() já é garantido pelo TenantMiddleware
        # (ATOMIC_REQUESTS=True em base.py); aqui só asseguramos no caso de
        # chamadas fora de request HTTP (tasks Celery).
        with transaction.atomic():
            audit_row = self._gravar_audit(
                usuario_id=usuario_id,
                tenant_id=tenant_id,
                action=action,
                resource=resource,
                purpose=purpose,
                decision=decision_intermediate.allowed,
                reason=decision_intermediate.reason,
                perfis_aplicados=decision_intermediate.perfis_aplicados,
                escopo_avaliado=decision_intermediate.escopo_avaliado,
            )

        return AuthDecision(
            allowed=decision_intermediate.allowed,
            reason=decision_intermediate.reason,
            perfis_aplicados=decision_intermediate.perfis_aplicados,
            escopo_avaliado=decision_intermediate.escopo_avaliado,
            audit_id=audit_row.id,
        )

    def _resolver_perfis_vigentes(
        self,
        usuario_id: UUID,
        tenant_id: UUID | None,
        agora: datetime,
    ) -> tuple[str, ...]:
        """Lista de codigos de perfil vigentes do usuário no tenant.

        Cacheado por (user, tenant) com TTL curto. Em Wave A o invalidador
        vira event-driven (INV-INT-008).
        """
        key = _cache_key(usuario_id, tenant_id)
        cached = cache.get(key)
        if cached is not None:
            return tuple(cached)

        # Import tardio — quebra ciclo com apps Django loading.
        from src.infrastructure.usuario.models import UsuarioPerfilTenant

        qs = UsuarioPerfilTenant.objects.filter(
            usuario_id=usuario_id,
            valido_de__lte=agora,
        ).filter(
            models_q_valido_ate_ok(agora)
        )
        if tenant_id is not None:
            qs = qs.filter(tenant_id=tenant_id)
        perfis = tuple(qs.values_list("perfil", flat=True).distinct())
        cache.set(key, perfis, timeout=CACHE_TTL_SECS)
        return perfis

    def _decidir(
        self,
        perfis: tuple[str, ...],
        action: str,
        resource: dict[str, Any],
    ) -> AuthDecision:
        """RBAC clássico — F-B. ABAC entra em Wave A.

        Sem perfis = denied "sem_perfil".
        Algum perfil tem PerfilAcao(acao, pode_executar=True) = allowed.
        Caso contrário = denied "rbac_denied".
        """
        if not perfis:
            return AuthDecision(
                allowed=False,
                reason="sem_perfil_no_tenant",
                perfis_aplicados=(),
            )

        permitidos = set(
            PerfilAcao.objects.filter(
                perfil__codigo__in=perfis,
                acao=action,
                pode_executar=True,
            ).values_list("perfil__codigo", flat=True)
        )
        if permitidos:
            return AuthDecision(
                allowed=True,
                reason="ok",
                perfis_aplicados=tuple(sorted(permitidos)),
            )
        return AuthDecision(
            allowed=False,
            reason="rbac_denied",
            perfis_aplicados=tuple(sorted(perfis)),
        )

    def _gravar_audit(
        self,
        usuario_id: UUID,
        tenant_id: UUID | None,
        action: str,
        resource: dict[str, Any],
        purpose: str,
        decision: bool,
        reason: str,
        perfis_aplicados: tuple[str, ...],
        escopo_avaliado: dict[str, Any],
    ) -> AuthzDecision:
        """INSERT na cadeia. Trigger PG bloqueia UPDATE/DELETE (INV-AUTHZ-002)."""
        ultimo = (
            AuthzDecision.objects.order_by("-timestamp").only("hash_atual").first()
        )
        hash_anterior = ultimo.hash_atual if ultimo else ""

        payload = {
            "usuario_id": str(usuario_id),
            "tenant_id": str(tenant_id) if tenant_id else None,
            "action": action,
            "resource_summary": resource,
            "purpose": purpose,
            "decision": "allowed" if decision else "denied",
            "reason": reason,
            "perfis_aplicados": list(perfis_aplicados),
            "escopo_avaliado": escopo_avaliado,
        }
        hash_atual = _hash_linha(hash_anterior, payload)

        return AuthzDecision.objects.create(
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            action=action,
            resource_summary=resource,
            purpose=purpose,
            decision="allowed" if decision else "denied",
            reason=reason,
            perfis_aplicados=list(perfis_aplicados),
            escopo_avaliado=escopo_avaliado,
            hash_anterior=hash_anterior,
            hash_atual=hash_atual,
        )


def models_q_valido_ate_ok(agora):  # type: ignore[no-untyped-def]
    """Helper duplicado de multitenant/middleware.py — evita import circular."""
    from django.db.models import Q

    return Q(valido_ate__isnull=True) | Q(valido_ate__gte=agora)


# Instância única (poderia virar service em DI container futuro)
_PROVIDER: DjangoAuthorizationProvider | None = None


def get_provider() -> AuthorizationProvider:
    """Singleton lazy do provider. Permite swap em testes via monkeypatch."""
    global _PROVIDER
    if _PROVIDER is None:
        _PROVIDER = DjangoAuthorizationProvider()
    return _PROVIDER


def set_provider_for_test(provider: AuthorizationProvider | None) -> None:
    """Swap pra teste (None = volta ao default)."""
    global _PROVIDER
    _PROVIDER = provider  # type: ignore[assignment]
