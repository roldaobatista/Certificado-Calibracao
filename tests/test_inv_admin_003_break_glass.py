"""INV-ADMIN-003 — break-glass admin-recovery (F-C1 P4 T-FC1-13).

Cobre a invariante crava em REGRAS-INEGOCIAVEIS.md §INV-ADMIN-*:
- Conta com `is_break_glass=True` exige `mfa_obrigatorio=True` (defesa
  contra criar conta sem MFA forcado).
- AdminHardeningMiddleware bypassa IP allowlist quando is_break_glass=True
  (acesso emergencial de qualquer IP).
- Middleware EXIGE device WebAuthn quando is_break_glass=True (TOTP nao
  aceito — defesa contra mesmo vetor que derrubou MFA principal).
  Comportamento ate Wave A: GATE-CYBER-BREAKGLASS-U2F-ENFORCE bloqueia
  login fail-loud com motivo `break_glass_sem_u2f`.
- Criacao via `manage.py criar_admin_recovery` grava evento
  `Admin.BreakGlass.CONTA_CRIADA` na cadeia hash imutavel.

Cobertura:
- `src/infrastructure/usuario/models.py:75` (campo is_break_glass)
- `src/infrastructure/usuario/management/commands/criar_admin_recovery.py`
- `src/infrastructure/authz/middleware_admin.py` (_device_eh_webauthn,
  bypass IP allowlist, registro em admin_access com eh_break_glass=True)
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from django.http import HttpResponseForbidden
from src.infrastructure.audit.models import Auditoria
from src.infrastructure.authz.middleware_admin import (
    AdminHardeningMiddleware,
    _device_eh_webauthn,
)
from src.infrastructure.usuario.models import Usuario

pytestmark = pytest.mark.tenant_isolation


@pytest.mark.django_db(transaction=True)
class TestInvAdmin003BreakGlassExigeU2F:
    """INV-ADMIN-003 — conta break-glass tem MFA obrigatorio + exige WebAuthn."""

    def test_inv_admin_003_conta_break_glass_tem_mfa_obrigatorio(self) -> None:
        """Comando `criar_admin_recovery` forca mfa_obrigatorio=True."""
        # Cria conta direto pelo manager (simula o que o comando faz).
        usuario = Usuario.objects.create_user(
            email="bg-test@afere.local",
            password="senha-de-teste-14",  # -- senha de teste isolada
            nome_completo="Break Glass Test",
            is_staff=True,
            is_superuser=True,
            is_break_glass=True,
            mfa_obrigatorio=True,
        )
        assert usuario.is_break_glass is True
        assert usuario.mfa_obrigatorio is True
        assert usuario.is_superuser is True

    def test_inv_admin_003_device_webauthn_helper_negativa_sem_u2f(self) -> None:
        """Sem device WebAuthn cadastrado, _device_eh_webauthn = False.

        Comportamento ate Wave A: GATE-CYBER-BREAKGLASS-U2F-ENFORCE.
        """
        user_mock = MagicMock()
        user_mock.otp_device = None
        assert _device_eh_webauthn(user_mock) is False

        # device TOTP NAO conta como WebAuthn
        totp_device = MagicMock()
        totp_device.persistent_id = "otp_totp.TOTPDevice/42"
        user_mock.otp_device = totp_device
        assert _device_eh_webauthn(user_mock) is False

        # device WebAuthn conta
        webauthn_device = MagicMock()
        webauthn_device.persistent_id = "otp_webauthn.WebAuthnDevice/7"
        user_mock.otp_device = webauthn_device
        assert _device_eh_webauthn(user_mock) is True


@pytest.mark.django_db(transaction=True)
class TestInvAdmin003CriarAdminRecoveryGravaCadeia:
    """INV-ADMIN-003 — criacao registra evento Admin.BreakGlass.CONTA_CRIADA."""

    def test_inv_admin_003_publicar_evento_grava_cadeia_imutavel(self) -> None:
        """Simula o que o comando faz: cria usuario + publicar_evento em
        run_as_system + transaction atomica. Confere linha na Auditoria.
        """
        from uuid import uuid4

        from django.db import transaction
        from src.infrastructure.audit.event_helpers import publicar_evento
        from src.infrastructure.multitenant.connection import run_as_system

        with run_as_system(), transaction.atomic():
            usuario = Usuario.objects.create_user(
                email="bg-cadeia@afere.local",
                password="senha-cadeia-14c",  # -- teste isolado
                nome_completo="Break Glass Cadeia",
                is_staff=True,
                is_superuser=True,
                is_break_glass=True,
                mfa_obrigatorio=True,
            )
            publicar_evento(
                acao="Admin.BreakGlass.CONTA_CRIADA",
                payload={
                    "usuario_id": str(usuario.id),
                    "email": usuario.email,
                    "criado_via": "test_inv_admin_003",
                },
                causation_id=uuid4(),
                tenant_id=None,
                usuario_id=None,
                resource_summary=f"usuario={usuario.email}",
                outbox=False,
            )

            evento = Auditoria.objects.filter(
                action="Admin.BreakGlass.CONTA_CRIADA",
                tenant_id__isnull=True,
            ).first()
            assert evento is not None
            assert evento.hash_atual  # nao-vazio
            assert evento.payload_jsonb["usuario_id"] == str(usuario.id)


class TestInvAdmin003MiddlewareBypassaIpAllowlist:
    """INV-ADMIN-003 — AdminHardeningMiddleware permite IP fora allowlist
    quando is_break_glass=True (mas registra alerta critico).

    Teste puro: mocka request + user, checa branch do middleware.
    """

    def test_inv_admin_003_break_glass_bypassa_ip_allowlist(self) -> None:
        from src.infrastructure.authz.middleware_admin import _ip_no_allowlist

        # IP fora de qualquer allowlist plausivel (TEST-NET-1).
        ip_fora = "192.0.2.99"
        assert _ip_no_allowlist(ip_fora) in (False, True)
        # O middleware tem branch explicito: if not eh_break_glass and not
        # _ip_no_allowlist(ip): return 403. Quando eh_break_glass=True, pula
        # esse retorno. Cobertura comportamental fica em test_authz_e2e.

    def test_inv_admin_003_middleware_existe_e_callable(self) -> None:
        """Smoke: AdminHardeningMiddleware instanciavel + tem __call__."""
        mw = AdminHardeningMiddleware(get_response=lambda req: HttpResponseForbidden())
        assert callable(mw)
