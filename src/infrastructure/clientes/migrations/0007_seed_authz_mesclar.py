"""Adiciona a acao 'clientes.mesclar' na matriz authz_perfil_acao (US-CLI-005).

TL1 do tech-lead: matriz so aceita admin_tenant. Outros perfis (financeiro?)
ficam pra Wave A se aparecer demanda.
"""

# policy-test-coverage: skip -- seed de matriz, sem CREATE POLICY novo
# tests-coverage: tests/test_clientes_us_cli_005_mesclar.py

from __future__ import annotations

import uuid

from django.db import migrations


def seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute("SELECT id FROM authz_perfil WHERE codigo = 'admin_tenant';")
        row = cur.fetchone()
        if row:
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, 'clientes.mesclar', TRUE, now()) "
                "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                [str(uuid.uuid4()), row[0]],
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
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute("DELETE FROM authz_perfil_acao WHERE acao = 'clientes.mesclar';")
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [
        ("clientes", "0006_unique_doc_ativo"),
    ]
    operations = [migrations.RunPython(seed, reverse_code=unseed)]
