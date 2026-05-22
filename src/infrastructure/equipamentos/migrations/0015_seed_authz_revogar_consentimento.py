"""Seed authz `equipamentos.revogar_consentimento_historico` (T-EQP-041 /
US-EQP-004 AC-EQP-004-8 / P-EQP-R6).

admin_tenant + atendente podem revogar (mesmo perfil que processa
aceite presencial). RT signatario nao participa (responsabilidade
administrativa, nao tecnica). Portal-cliente OTP (Wave B+ GATE-EQP-3)
adicionara perfil `cliente_externo_titular_dados` quando o cedente
puder revogar diretamente via auto-atendimento.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova
"""

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "equipamentos.revogar_consentimento_historico"),
    ("tecnico", "equipamentos.revogar_consentimento_historico"),
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
        ("equipamentos", "0014_consentimento_historico_equipamento"),
        ("authz", "0003_seed_perfis"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
