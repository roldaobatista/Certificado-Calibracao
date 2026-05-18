"""Seed `clientes.importar` na matriz authz para `admin_tenant` apenas (US-CLI-003).

R4 advogado + TL7: least privilege — importacao em massa eh operacao de alto
impacto (cria N titulares, expoe PII, pode ser revertida apenas manualmente).
Soh dono/admin pode operar.

Pareada com predicado ABAC `tenant_nao_suspenso` (predicates_authz.py — stub
ate ADR-0015 fluxo 3 entrar).
"""

# policy-test-coverage: skip -- seed de matriz, sem CREATE POLICY novo
# tests-coverage: tests/test_clientes_us_cli_003_importar.py

from __future__ import annotations

import uuid

from django.db import migrations


def seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        # Soh admin_tenant — TL7 least privilege.
        cur.execute(
            "SELECT codigo, id FROM authz_perfil WHERE codigo = %s;",
            ["admin_tenant"],
        )
        for codigo, pid in cur.fetchall():
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, 'clientes.importar', TRUE, now()) "
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
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute("DELETE FROM authz_perfil_acao WHERE acao = 'clientes.importar';")
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False
    dependencies = [("clientes", "0012_cliente_lgpd_base_legal_e_decl")]
    operations = [migrations.RunPython(seed, reverse_code=unseed)]
