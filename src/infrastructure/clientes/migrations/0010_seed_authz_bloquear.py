"""Adiciona 'clientes.bloquear' e 'clientes.desbloquear' na matriz authz (US-CLI-004).

TL7: so admin_tenant. Perfil 'financeiro' entra em Wave A.
"""

# policy-test-coverage: skip -- seed de matriz, sem CREATE POLICY novo
# tests-coverage: tests/test_clientes_us_cli_004_bloquear.py

from __future__ import annotations

import uuid

from django.db import migrations

ACOES = ("clientes.bloquear", "clientes.desbloquear")


def seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute("SELECT id FROM authz_perfil WHERE codigo = 'admin_tenant';")
        row = cur.fetchone()
        if row:
            for acao in ACOES:
                cur.execute(
                    "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                    "VALUES (%s, %s, %s, TRUE, now()) "
                    "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                    [str(uuid.uuid4()), row[0], acao],
                )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


def unseed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute(
            "DELETE FROM authz_perfil_acao WHERE acao = ANY(%s);",
            [list(ACOES)],
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("clientes", "0009_cliente_bloqueio_constraints"),
    ]
    operations = [migrations.RunPython(seed, reverse_code=unseed)]
