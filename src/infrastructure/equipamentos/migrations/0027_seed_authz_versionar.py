"""Seed authz `equipamentos.versionar` (T-EQP-015 / US-EQP-002 AC-EQP-002-4).

admin_tenant + tecnico podem versionar (criar ou solicitar aprovacao
quando motivo `outros`/`substituicao_componente_critico`/
`atualizacao_firmware`). Gestor_qualidade decide aprovacoes — sua
permissao de decisao vive em authz separadamente (Wave A).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova
"""

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "equipamentos.versionar"),
    ("tecnico", "equipamentos.versionar"),
]


def seed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
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
        ("equipamentos", "0026_equipamentorecebimento_ambiente"),
        ("authz", "0003_seed_perfis"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
