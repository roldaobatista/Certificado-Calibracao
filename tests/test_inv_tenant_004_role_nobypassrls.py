"""INV-TENANT-004: roles app_user e app_migrator sao NOBYPASSRLS + NOSUPERUSER.

TST-004: teste cujo nome cita explicitamente o ID da invariante.

Background: o drill `validar_f_a` ja checa via management command; aqui temos a
forma pytest equivalente pra atender TST-004 (auditor de Qualidade exige citacao
nominal do ID).
"""

from __future__ import annotations

import pytest
from django.db import connection


@pytest.mark.django_db
def test_inv_tenant_004_role_app_user_e_nobypassrls_e_nosuperuser():
    """Role corrente (app_user em runtime) tem rolbypassrls=false E rolsuper=false."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT rolname, rolbypassrls, rolsuper FROM pg_roles "
            "WHERE rolname = current_user;"
        )
        row = cur.fetchone()
    assert row is not None
    rolname, bypass, superuser = row
    assert bypass is False, (
        f"INV-TENANT-004 VIOLADA: role {rolname} tem BYPASSRLS — RLS pode ser ignorada"
    )
    assert superuser is False, (
        f"INV-TENANT-004 VIOLADA: role {rolname} eh SUPERUSER — bypassa toda seguranca"
    )


@pytest.mark.django_db
def test_inv_tenant_004_role_app_migrator_separada_e_nobypassrls():
    """Existe role 'app_migrator' separada, tambem NOBYPASSRLS NOSUPERUSER."""
    with connection.cursor() as cur:
        cur.execute(
            "SELECT rolname, rolbypassrls, rolsuper FROM pg_roles "
            "WHERE rolname = 'app_migrator';"
        )
        row = cur.fetchone()
    assert row is not None, "Role app_migrator nao existe — INV-TENANT-004 violada"
    rolname, bypass, superuser = row
    assert bypass is False, "app_migrator tem BYPASSRLS — INV-TENANT-004 violada"
    assert superuser is False, "app_migrator eh SUPERUSER — INV-TENANT-004 violada"
