"""TenantMiddleware — porteiro que ativa o contexto de tenant em cada request.

Fluxo (ADR-0002 v2 §3):
1. Extrai user_id do request (session do Django Admin; JWT entra em Marco F-B)
2. Resolve lista de tenants vigentes consultando UsuarioPerfilTenant (com
   `app.usuario_id` ja setado — policy RLS dessa tabela permite leitura)
3. Le tenant "ativo" do header `X-Aferê-Active-Tenant` ou query param
4. Valida que active_tenant in tenant_ids
5. Seta `app.tenant_ids` + `app.active_tenant_id` no PG via SET LOCAL
6. Chama proxima view (todas as queries protegidas)
7. Limpa contexto no finally

Endpoints publicos (`/healthz/`, `/admin/login/`, `/api/schema/`, `/api/docs/`)
bypass o middleware via lista hardcoded.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone

from .connection import run_in_user_context, setar_contexto_pg_na_conexao
from .context import (
    active_tenant_context,
    ip_hash_context,
    perfil_tenant_context,
    tenant_ids_context,
    usuario_id_context,
)


def _extrair_ip(request: HttpRequest) -> str:
    """IP do cliente: 1º hop de X-Forwarded-For, senão REMOTE_ADDR."""
    meta = getattr(request, "META", {}) or {}
    xff = str(meta.get("HTTP_X_FORWARDED_FOR", "") or "")
    if xff:
        return xff.split(",")[0].strip()
    return str(meta.get("REMOTE_ADDR", "") or "")


# Paths que NAO exigem tenant context. Mantido pequeno e explicito.
PUBLIC_PATHS_PREFIX = (
    "/healthz",
    "/api/schema",
    "/api/docs",
    "/static/",
    "/media/",
    # T-EQP-025 (US-EQP-003 AC-EQP-003-2 / INV-051): QR publico Escopo C
    # (anonimo) resolve em `/api/v1/qr/{hash}/` sem tenant context. View
    # PublicEndpoint + funcao SECURITY DEFINER `resolver_qr_publico`.
    "/api/v1/qr/",
)

# /admin/ tem casos especiais: login/logout sao publicos, resto exige usuario logado
# mas NAO exige tenant context (admin acessa diretamente sem RLS — usado pra suporte).
ADMIN_PATH_PREFIX = "/admin/"


class TenantMiddleware:
    """Middleware DJANGO classico (request -> response).

    Roda DEPOIS de AuthenticationMiddleware (precisa de request.user). Ver
    config/settings/base.py — ordem importa.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path

        # Bypass de paths publicos / admin
        if path.startswith(PUBLIC_PATHS_PREFIX) or path.startswith(ADMIN_PATH_PREFIX):
            return self.get_response(request)

        # Sem usuario logado em path nao-publico = 401
        if not getattr(request, "user", None) or not request.user.is_authenticated:
            return JsonResponse(
                {"detail": "Autenticacao obrigatoria"},
                status=401,
            )

        usuario_id: UUID = request.user.pk
        tenant_ids = self._resolver_tenants_permitidos(usuario_id)
        if not tenant_ids:
            return JsonResponse(
                {"detail": "Usuario sem tenant ativo"},
                status=403,
            )

        active_tenant = self._extrair_active_tenant(request, tenant_ids)
        if active_tenant is None:
            return JsonResponse(
                {
                    "detail": (
                        "Tenant ativo nao informado. Inclua header "
                        "'X-Afere-Active-Tenant' OU query param 'tenant'."
                    )
                },
                status=400,
            )

        # T-FB-04: HMAC do IP no contexto (NUNCA IP cru), token+reset
        # igual aos demais — leak-safe em pool de threads (mesmo padrão
        # do usuario_id; via contexto, não parâmetro de can() — NG-FB-1).
        from src.infrastructure.audit.services import hashear_ip

        # T-SAN-PERFIL-016 (Sprint 2 ADR-0067 / AC-SAN-PERFIL-003-5):
        # Resolve perfil regulatorio do active_tenant a partir do banco e cacheia
        # no ContextVar. Leitura barata (1 SELECT por request) — predicate
        # tenant_perfil_e usa este cache, eliminando N+1 (AC-002-8).
        # Falha de DB / tenant ausente / perfil NULL = "" (predicate decide
        # fail-closed downstream).
        perfil_atual = self._resolver_perfil_active_tenant(active_tenant)

        token_list = tenant_ids_context.set(tenant_ids)
        token_active = active_tenant_context.set(active_tenant)
        token_user = usuario_id_context.set(usuario_id)
        token_ip = ip_hash_context.set(hashear_ip(_extrair_ip(request)))
        token_perfil = perfil_tenant_context.set(perfil_atual)
        try:
            with transaction.atomic():
                setar_contexto_pg_na_conexao(
                    tenant_ids=tenant_ids,
                    active_tenant=active_tenant,
                    usuario_id=usuario_id,
                )
                return self.get_response(request)
        finally:
            tenant_ids_context.reset(token_list)
            active_tenant_context.reset(token_active)
            usuario_id_context.reset(token_user)
            ip_hash_context.reset(token_ip)
            perfil_tenant_context.reset(token_perfil)

    def _resolver_tenants_permitidos(self, usuario_id: UUID) -> list[UUID]:
        """Consulta UsuarioPerfilTenant filtrando por janela de validade.

        Roda no contexto AUTENTICADO PRÉ-TENANT (`run_in_user_context`):
        `app.usuario_id` setado dentro de transacao (SET LOCAL expira no
        commit) — a policy RLS de UsuarioPerfilTenant permite leitura. FB-C1+C3
        BLOQ #2: este é o MESMO contexto que `can()` pré-tenant exige; fonte
        única em `connection.run_in_user_context`.
        """
        from src.infrastructure.usuario.models import UsuarioPerfilTenant
        from src.infrastructure.usuario.vigencia import janela_vigente

        agora = timezone.now()
        with run_in_user_context(usuario_id):
            return list(
                UsuarioPerfilTenant.objects.filter(usuario_id=usuario_id)
                .filter(janela_vigente(agora))
                .values_list("tenant_id", flat=True)
                .distinct()
            )

    def _resolver_perfil_active_tenant(self, active_tenant: UUID) -> str:
        """T-SAN-PERFIL-016 / AC-SAN-PERFIL-003-5.

        Le `tenants.perfil_regulatorio` do banco para popular o ContextVar
        `perfil_tenant_context`. Predicate `tenant_perfil_e` (Sprint 2)
        consulta este ContextVar — eliminando N+1 por request.

        Returns:
            - "A" / "B" / "C" / "D" se tenant encontrado e perfil setado.
            - "" se tenant nao encontrado OU perfil NULL (estado invalido
              pos-backfill).

        Predicate downstream decide fail-closed em "" (AC-SAN-PERFIL-002-5).
        Esta funcao NAO levanta excecao — falha silenciosa pra "" e o caller
        decide gravidade.

        Tabela `tenants` e SHARED ACROSS TENANTS (ADR-0002 §8) — sem RLS — entao
        o SELECT funciona mesmo antes do `setar_contexto_pg_na_conexao` ser
        chamado (que e o que ativa policies RLS pra demais tabelas).
        """
        from src.infrastructure.tenant.models import Tenant

        try:
            perfil = (
                Tenant.objects.filter(id=active_tenant)
                .values_list("perfil_regulatorio", flat=True)
                .first()
            )
            return perfil or ""
        except Exception:  # noqa: BLE001 — defensivo, predicate decide
            return ""

    def _extrair_active_tenant(self, request: HttpRequest, tenant_ids: list[UUID]) -> UUID | None:
        """Header > query param > default (se so 1 tenant)."""
        raw = request.headers.get("X-Afere-Active-Tenant") or request.GET.get("tenant")
        if raw:
            try:
                active = UUID(raw)
            except (ValueError, TypeError):
                return None
            return active if active in tenant_ids else None
        # Default: se usuario tem 1 tenant so, usa ele.
        if len(tenant_ids) == 1:
            return tenant_ids[0]
        return None


# T-FB-02: regra de vigência movida p/ FONTE ÚNICA
# `src.infrastructure.usuario.vigencia.janela_vigente` (janela completa).


# Suprime warning de import nao usado de settings (futuro: feature flag de modo strict)
_ = settings
