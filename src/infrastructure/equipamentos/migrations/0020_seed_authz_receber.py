"""Seed authz `equipamentos.receber` + `equipamentos.transicionar_recebimento`
(T-EQP-047 / T-EQP-050 / US-EQP-006).

admin_tenant + tecnico podem receber e transicionar. RT signatario nao
participa (recebimento e operacional; transicao para
`aguardando_aprovacao_tecnica` em diante envolve RT mas nao via este
endpoint — Wave A cria endpoint dedicado de aprovacao).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova
"""

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "equipamentos.receber"),
    ("tecnico", "equipamentos.receber"),
    ("admin_tenant", "equipamentos.transicionar_recebimento"),
    ("tecnico", "equipamentos.transicionar_recebimento"),
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
        ("equipamentos", "0019_equipamentorecebimento"),
        ("authz", "0003_seed_perfis"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
