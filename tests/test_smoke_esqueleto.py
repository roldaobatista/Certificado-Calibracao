"""Smoke test do esqueleto F-A — prova que settings carregam + URLs respondem.

Marca: nao depende de banco, roda em <1s. Validado no Marco 1.
"""

import pytest
from django.test import Client
from django.urls import reverse


def test_settings_carrega_em_pt_br_sp(settings) -> None:
    assert settings.LANGUAGE_CODE == "pt-br"
    assert settings.TIME_ZONE == "America/Sao_Paulo"
    assert settings.USE_TZ is True


def test_django_apps_essenciais_instaladas(settings) -> None:
    obrigatorios = {
        "django.contrib.admin",
        "django.contrib.auth",
        "rest_framework",
        "drf_spectacular",
        "django_otp",
    }
    assert obrigatorios.issubset(set(settings.INSTALLED_APPS))


def test_argon2_eh_primeiro_password_hasher(settings) -> None:
    assert settings.PASSWORD_HASHERS[0].endswith("Argon2PasswordHasher")


@pytest.mark.django_db
def test_healthz_responde_ok(client: Client) -> None:
    response = client.get(reverse("healthz"))
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "fase": "foundation-f-a"}
