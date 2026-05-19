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

from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from django.core.cache import cache
from django.utils import timezone

from src.domain.authz import AuthDecision, AuthorizationProvider
from src.infrastructure.audit.canonicalizar import canonicalizar
from src.infrastructure.audit.hash_chain import calcular_hash
from src.infrastructure.audit.services import (
    _ADVISORY_LOCK_CLASSE_AUTHZ,
    registrar_em_cadeia,
)

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


_PRIMITIVOS = (str, int, float)  # bool tratado à parte (subclasse de int)

# T-FB-05 / advogado C-A2.1: `resource` aceita só REFERÊNCIAS, nunca PII
# por valor. Imposto por CÓDIGO (não docstring — `_normalizar_para_hash`
# serializa, não redige). Chave permitida sse: termina em `_id` (ref),
# está na allowlist fixa, ou o valor é bool (flag). `cpf`/`nome`/`email`/
# `documento`/... → fail-loud ANTES da transação.
_RESOURCE_KEYS_OK = frozenset({"recurso_tipo", "recurso_id", "escopo"})


def _validar_resource_sem_pii(resource: dict[str, Any]) -> None:
    """Allowlist das chaves de TOPO do `resource` (minimização LGPD art.
    6 III). Chave de topo válida sse: termina em `_id` (referência),
    está na allowlist fixa, ou valor é bool (flag). `cpf`/`nome`/`email`
    /`documento`/... → fail-loud ANTES da transação.

    Não recursa: `escopo` é o container designado de atributos de
    scope (não-PII por contrato); a governança do CONTEÚDO de `escopo`
    em Wave A (redator/allowlist fina) é o GATE-FB-3 rastreado — em F-B
    não há módulo de produto alimentando isso (NG-FB-7)."""
    for k, v in resource.items():
        if not isinstance(k, str):
            raise ValueError(f"resource authz: chave não-str ({k!r}) — inválida (T-FB-05).")
        if k in _RESOURCE_KEYS_OK or k.endswith("_id") or isinstance(v, bool):
            continue
        raise ValueError(
            f"resource authz: chave {k!r} não permitida — `resource` aceita "
            "só referências (`*_id`, `recurso_tipo`, `escopo`) e flags "
            "booleanas. PII por REFERÊNCIA, nunca por valor (minimização "
            "LGPD art. 6 III / T-FB-05 / advogado C-A2.1)."
        )


def _normalizar_para_hash(obj: Any, _caminho: str = "resource") -> Any:
    """Normaliza `resource` p/ forma canônica JSON-safe ANTES de transação.

    FB-C1 BLOQ #2/#4: o `resource` vem da view (pode ter `set`, instância
    Django, datetime naive). Dois problemas se isso for adiante cru:
    (1) `canonicalizar` faria `raise` DENTRO da transação do helper → erro
        opaco que derruba a autorização;
    (2) `resource_summary` é `JSONField` — Decimal/UUID/datetime crus
        quebram a serialização no INSERT.

    Solução: converter AQUI (fora de qualquer transação) para a forma
    canônica EM STRING idêntica à que `audit.canonicalizar` produziria.
    O resultado é fonte ÚNICA: alimenta o hash E é o que se persiste —
    persistido == hasheado → verificação de integridade recomputa o MESMO
    hash (round-trip íntegro; senão acusaria adulteração falsa).

    - str/int/float → intactos; bool → intacto;
    - datetime tz-aware → `astimezone(utc).isoformat()`; naive → erro claro;
    - date → `isoformat()`; Decimal → `str`; UUID → `str`;
    - dict → recursão (chave não-str → erro claro);
    - list/tuple → lista; set/frozenset → lista ORDENADA (determinismo);
    - qualquer outro → ValueError com o caminho exato (fail-loud cedo).
    """
    if isinstance(obj, bool) or obj is None or isinstance(obj, _PRIMITIVOS):
        return obj
    if isinstance(obj, datetime):
        if obj.tzinfo is None:
            raise ValueError(
                f"resource authz: datetime naive em {_caminho} ({obj!r}). "
                "Use timezone.now() — fail-loud antes da transação (FB-C1)."
            )
        return obj.astimezone(UTC).isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return str(obj)
    if isinstance(obj, UUID):
        return str(obj)
    if isinstance(obj, dict):
        norm: dict[str, Any] = {}
        for k, v in obj.items():
            if not isinstance(k, str):
                raise ValueError(
                    f"resource authz: chave não-str em {_caminho} ({k!r}: "
                    f"{type(k).__name__}) — não serializável (FB-C1)."
                )
            norm[k] = _normalizar_para_hash(v, f"{_caminho}.{k}")
        return norm
    if isinstance(obj, list | tuple):
        return [_normalizar_para_hash(v, f"{_caminho}[{i}]") for i, v in enumerate(obj)]
    if isinstance(obj, set | frozenset):
        itens = [_normalizar_para_hash(v, f"{_caminho}{{}}") for v in obj]
        # set não tem ordem → ordenar a forma canônica p/ hash determinístico.
        return sorted(itens, key=repr)
    raise ValueError(
        f"resource authz contém tipo não serializável em {_caminho}: "
        f"{type(obj).__name__} (FB-C1 — normalize antes de chamar can())."
    )


def _payload_para_hash(
    *,
    usuario_id: UUID,
    tenant_id: UUID | None,
    action: str,
    resource_summary: Any,
    purpose: str,
    decision: bool | str,
    reason: str,
    perfis_aplicados: Any,
    escopo_avaliado: Any,
    ip_hash: str = "",
) -> dict[str, Any]:
    """Monta o dict que entra no hash da cadeia authz.

    Fonte ÚNICA usada por `_gravar_audit` (gravação) E pela verificação de
    integridade (recomputo) — divergir aqui = mesma classe de bug do BLOQ #1
    (cadeia acusa adulteração falsa). `decision` aceita bool (gravação) ou
    str já normalizada "allowed"/"denied" (recomputo a partir da linha).
    T-FB-04: `ip_hash` entra NO HASH (não só na coluna) — senão a
    verificação de integridade não o cobriria e ele seria adulterável.
    """
    dec = decision if isinstance(decision, str) else ("allowed" if decision else "denied")
    return {
        "usuario_id": str(usuario_id),
        "tenant_id": str(tenant_id) if tenant_id else None,
        "action": action,
        "resource_summary": resource_summary,
        "purpose": purpose,
        "decision": dec,
        "reason": reason,
        "perfis_aplicados": list(perfis_aplicados),
        "escopo_avaliado": escopo_avaliado,
        "ip_hash": ip_hash,
    }


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
        # T-FB-05: allowlist anti-PII ANTES de tudo (minimização). Depois
        # normaliza CEDO, fora de transação (BLOQ #2/#4): tipo inválido →
        # erro claro AQUI. `resource_norm` é fonte ÚNICA (hash E persist).
        resource = resource or {}
        _validar_resource_sem_pii(resource)
        resource_norm = _normalizar_para_hash(resource)
        agora = at_time or timezone.now()

        perfis = self._resolver_perfis_vigentes(usuario_id, tenant_id, agora)
        decision_intermediate = self._decidir(perfis, action, resource_norm)

        # Grava audit ANTES de retornar. NÃO há `transaction.atomic()` aninhado
        # aqui (FB-A2): o helper `registrar_em_cadeia` é a fronteira
        # transacional + advisory lock — abrir atomic externo só criaria
        # savepoint inútil. Sob ATOMIC_REQUESTS o lock vive até o COMMIT do
        # request (documentado no helper) — correto, não regressão.
        audit_row = self._gravar_audit(
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            action=action,
            resource=resource_norm,
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
        from src.infrastructure.usuario.vigencia import janela_vigente

        qs = UsuarioPerfilTenant.objects.filter(usuario_id=usuario_id).filter(janela_vigente(agora))
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
        """RBAC classico + predicates ABAC (US-CLI-004 TL2).

        Pipeline:
        1. Sem perfis → denied "sem_perfil_no_tenant".
        2. RBAC: algum perfil tem PerfilAcao(acao, pode_executar=True)?
           Não → "rbac_denied".
        3. ABAC: predicates cujo ESCOPO casa `action` (binding —
           T-FB-01) passam? Primeiro denied curto-circuita. Ação sem
           predicate aplicável ⇒ ABAC neutro (segue RBAC), NÃO deny.
        """
        from .predicates import predicates_aplicaveis

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
        if not permitidos:
            return AuthDecision(
                allowed=False,
                reason="rbac_denied",
                perfis_aplicados=tuple(sorted(perfis)),
            )

        # ABAC: só predicates VINCULADOS à action (binding — T-FB-01).
        # Lista vazia ⇒ ABAC neutro (não roda nada, segue RBAC).
        for pred in predicates_aplicaveis(action):
            ok, motivo = pred.fn(resource)
            if not ok:
                return AuthDecision(
                    allowed=False,
                    reason=motivo or f"abac_denied:{pred.nome}",
                    perfis_aplicados=tuple(sorted(permitidos)),
                    escopo_avaliado={"predicate_negado": pred.nome},
                )

        return AuthDecision(
            allowed=True,
            reason="ok",
            perfis_aplicados=tuple(sorted(permitidos)),
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
        """INSERT na cadeia hash via helper ÚNICO (FB-C1). Trigger PG bloqueia
        UPDATE/DELETE (INV-AUTHZ-002).

        Cadeia POR-TENANT quando há tenant; POR-USUÁRIO quando pré-tenant
        (decisão authz pré-tenant TEM dono — o usuário; FB-C3). `cadeia_filtro`
        identifica a cadeia E deriva a chave do advisory lock (helper).

        BLOQ #2: decisão pré-tenant SEM usuário não pode existir — reiniciaria
        a cadeia silenciosamente. Fail-loud.
        """
        if tenant_id is None and usuario_id is None:
            raise ValueError(
                "can() pré-tenant sem usuario_id: cadeia authz pré-tenant é "
                "POR-USUÁRIO (FB-C3). Use run_in_user_context(usuario_id)."
            )

        cadeia_filtro: dict[str, Any] = (
            {"tenant_id": tenant_id}
            if tenant_id is not None
            else {"tenant_id__isnull": True, "usuario_id": usuario_id}
        )
        decision_str = "allowed" if decision else "denied"
        # T-FB-04: ip_hash vem do CONTEXTO (não da assinatura de can() —
        # domínio puro NG-FB-1). Vazio fora de request HTTP (task).
        from src.infrastructure.multitenant.context import ip_hash_context

        ip_hash = ip_hash_context.get()
        payload = _payload_para_hash(
            usuario_id=usuario_id,
            tenant_id=tenant_id,
            action=action,
            resource_summary=resource,
            purpose=purpose,
            decision=decision_str,
            reason=reason,
            perfis_aplicados=perfis_aplicados,
            escopo_avaliado=escopo_avaliado,
            ip_hash=ip_hash,
        )
        return registrar_em_cadeia(  # type: ignore[return-value]
            AuthzDecision,
            classe_lock=_ADVISORY_LOCK_CLASSE_AUTHZ,
            cadeia_filtro=cadeia_filtro,
            payload_hash=payload,
            campos={
                "usuario_id": usuario_id,
                "tenant_id": tenant_id,
                "action": action,
                "resource_summary": resource,
                "purpose": purpose,
                "decision": decision_str,
                "reason": reason,
                "perfis_aplicados": list(perfis_aplicados),
                "escopo_avaliado": escopo_avaliado,
                "ip_hash": ip_hash,
            },
        )


def verificar_integridade_cadeia_authz(
    cadeia_filtro: dict[str, Any],
) -> tuple[bool, int, list[str]]:
    """Recalcula a cadeia hash authz de UMA partição (FB-C1 / INV-AUTHZ-002).

    `cadeia_filtro`: ORM kwargs da partição (ex.: `{"tenant_id": tid}` ou
    `{"tenant_id__isnull": True, "usuario_id": uid}`). RLS deve permitir ler
    essas linhas no contexto chamador (cadeia do tenant → contexto do tenant;
    pré-tenant → run_in_user_context; tudo → run_as_system).

    Algoritmo ÚNICO: `calcular_hash(anterior, canonicalizar(_payload_para_hash
    (linha)))`. Q-02 (igual audit): encadeia no RECALCULADO, não no salvo —
    adulteração no meio quebra ESSE elo e TODOS os seguintes (prova real de
    hash chain). Reconstrói o payload das MESMAS colunas que `_gravar_audit`
    persistiu → round-trip íntegro (BLOQ #4: resource_summary persistido ==
    o que entrou no hash).

    Returns: (ok, total, [ids_quebrados]).
    """
    quebrados: list[str] = []
    total = 0
    hash_anterior_esperado: str | None = None

    qs = (
        AuthzDecision.objects.filter(**cadeia_filtro).order_by("sequencia").iterator(chunk_size=500)
    )
    for linha in qs:
        total += 1
        payload = _payload_para_hash(
            usuario_id=linha.usuario_id,
            tenant_id=linha.tenant_id,
            action=linha.action,
            resource_summary=linha.resource_summary,
            purpose=linha.purpose,
            decision=linha.decision,
            reason=linha.reason,
            perfis_aplicados=linha.perfis_aplicados,
            escopo_avaliado=linha.escopo_avaliado,
            ip_hash=linha.ip_hash,
        )
        recalc = calcular_hash(hash_anterior_esperado, canonicalizar(payload))
        if recalc != linha.hash_atual:
            quebrados.append(str(linha.id))
        hash_anterior_esperado = recalc

    return (len(quebrados) == 0, total, quebrados)


# T-FB-02: a regra de vigência vive em FONTE ÚNICA
# `src.infrastructure.usuario.vigencia.janela_vigente` — a cópia
# `models_q_valido_ate_ok` ("evita import circular") foi REMOVIDA
# (era débito que recriava FB-A4 a cada edição).


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
