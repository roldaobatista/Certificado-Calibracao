"""Seed das acoes de `clientes` na matriz authz_perfil_acao (Wave A).

Acoes do modulo + qual perfil tem cada uma. Mantem o modulo auto-contido —
ao adicionar/remover acao, basta criar migration nova aqui.

Matriz (Marco 1):
    admin_tenant            -> criar, ler, atualizar, deletar
    tecnico                 -> ler (consulta cliente da OS)
    rt_signatario           -> ler
    cliente_externo_leitura -> ler (so os proprios — escopo ABAC entra depois)
"""

# policy-test-coverage: skip -- esta migration NAO cria policy nova; apenas semeia matriz authz cobertura testada em tests/test_clientes_api.py

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "clientes.criar"),
    ("admin_tenant", "clientes.ler"),
    ("admin_tenant", "clientes.atualizar"),
    ("admin_tenant", "clientes.deletar"),
    ("tecnico", "clientes.ler"),
    ("rt_signatario", "clientes.ler"),
    ("cliente_externo_leitura", "clientes.ler"),
]


def seed(apps, schema_editor):
    """Insere acoes desligando policy de bloqueio temporariamente (mesmo pattern do seed F-B)."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")

        # Pega ids dos perfis pelo codigo
        cur.execute(
            "SELECT codigo, id FROM authz_perfil WHERE codigo = ANY(%s);",
            [list({p for p, _ in MATRIZ})],
        )
        perfil_id_por_codigo = dict(cur.fetchall())

        for perfil_codigo, acao in MATRIZ:
            perfil_id = perfil_id_por_codigo[perfil_codigo]
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, %s, TRUE, now()) "
                "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                [str(uuid.uuid4()), perfil_id, acao],
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
            [list({a for _, a in MATRIZ})],
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
        ("clientes", "0002_rls_policies"),
        ("authz", "0003_seed_perfis"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
