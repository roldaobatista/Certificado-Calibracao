"""Seed `clientes.visao360` na matriz authz para os 4 perfis seed (US-CLI-002).

Todos podem ler visao 360 — ABAC em Wave A restringe escopo (cliente_externo
ve so o proprio cadastro, tecnico ve so OS atribuida etc).
"""

# policy-test-coverage: skip -- seed de matriz, sem CREATE POLICY novo
# tests-coverage: tests/test_clientes_us_cli_002_visao360.py

from __future__ import annotations

import uuid

from django.db import migrations


def seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute(
            "SELECT codigo, id FROM authz_perfil WHERE codigo = ANY(%s);",
            [["admin_tenant", "tecnico", "rt_signatario", "cliente_externo_leitura"]],
        )
        for _codigo, pid in cur.fetchall():
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, 'clientes.visao360', TRUE, now()) "
                "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                [str(uuid.uuid4()), pid],
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
        cur.execute("DELETE FROM authz_perfil_acao WHERE acao = 'clientes.visao360';")
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("clientes", "0010_seed_authz_bloquear")]
    operations = [migrations.RunPython(seed, reverse_code=unseed)]
