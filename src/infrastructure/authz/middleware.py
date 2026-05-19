"""MfaRequiredMiddleware — força TOTP cadastrado/verificado pros perfis sensíveis (SEC-MFA-001).

Roda DEPOIS de OTPMiddleware (que popula `request.user.is_verified()`) e
DEPOIS de TenantMiddleware (que setou `active_tenant_context`).

Regras F-B:
- Usuário com `mfa_obrigatorio=True` que NÃO está OTP-verificado → 401.
- Usuário com algum perfil sensível (admin_tenant, rt_signatario, financeiro)
  no tenant ativo precisa estar OTP-verificado → 401 se não.
- Paths públicos + admin login + setup MFA bypass.
"""

from __future__ import annotations

from collections.abc import Callable

from django.http import HttpRequest, HttpResponse, JsonResponse

PERFIS_SENSIVEIS = frozenset({"admin_tenant", "rt_signatario", "financeiro"})

# Paths que bypassa MFA check (auth setup, healthz, OTP enroll futuro).
# Auditor de Seguranca concern #3 (2026-05-18): removida entrada generica
# "/accounts/" — qualquer view nova ali ganhava bypass silencioso. Quando
# Wave A criar fluxo de enroll TOTP, ADICIONE path especifico (ex:
# "/accounts/2fa/enroll/" ou "/accounts/2fa/qr/").
MFA_BYPASS_PREFIX = (
    "/healthz",
    "/api/schema",
    "/api/docs",
    "/static/",
    "/media/",
    "/admin/login/",
    "/admin/logout/",
)


class MfaRequiredMiddleware:
    """Bloqueia request de perfil sensível sem TOTP verificado."""

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path
        if any(path.startswith(p) for p in MFA_BYPASS_PREFIX):
            return self.get_response(request)

        user = getattr(request, "user", None)
        if not user or not user.is_authenticated:
            return self.get_response(request)  # outras camadas tratam

        # django-otp expõe is_verified() — sem isso, presumimos NÃO-verificado
        otp_ok = bool(getattr(user, "is_verified", lambda: False)())

        if getattr(user, "mfa_obrigatorio", False) and not otp_ok:
            return JsonResponse(
                {
                    "detail": "MFA TOTP obrigatório — cadastre/verifique antes de continuar",
                    "reason": "mfa_required_user",
                },
                status=401,
            )

        # Checagem por perfil sensível no tenant ativo
        if self._tem_perfil_sensivel(request) and not otp_ok:
            return JsonResponse(
                {
                    "detail": "MFA TOTP obrigatório pra este perfil",
                    "reason": "mfa_required_perfil_sensivel",
                },
                status=401,
            )

        return self.get_response(request)

    @staticmethod
    def _tem_perfil_sensivel(request: HttpRequest) -> bool:
        from src.infrastructure.multitenant.context import (
            active_tenant_context,
            usuario_id_context,
        )

        usuario_id = usuario_id_context.get()
        tenant_id = active_tenant_context.get()
        if usuario_id is None or tenant_id is None:
            return False

        from django.utils import timezone

        from src.infrastructure.usuario.models import UsuarioPerfilTenant
        from src.infrastructure.usuario.vigencia import janela_vigente

        # T-FB-02 / FB-A4: janela COMPLETA (fonte única) — antes filtrava
        # só `valido_de`, então perfil sensível EXPIRADO ainda barrava.
        agora = timezone.now()
        perfis = (
            UsuarioPerfilTenant.objects.filter(
                usuario_id=usuario_id,
                tenant_id=tenant_id,
            )
            .filter(janela_vigente(agora))
            .values_list("perfil", flat=True)
        )
        return any(p in PERFIS_SENSIVEIS for p in perfis)
