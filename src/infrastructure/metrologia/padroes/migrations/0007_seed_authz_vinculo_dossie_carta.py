"""Seed authz das acoes novas do P10 (M5 fechamento).

3 acoes novas x perfis (segregacao cl. 6.2). Mesmo padrao idempotente de
0005_seed_authz_padroes (DISABLE RLS -> INSERT ON CONFLICT DO NOTHING ->
re-CREATE POLICY block_mutation). Funcao `seed` reconhecida pelo catalogo do
conftest (_SEED_MIGRATIONS).

Acoes:
  - padrao.gerir_vinculo_auxiliar (US-PAD-007-4 — criar/revogar vinculo cl. 6.4.5)
  - padrao.ler_dossie            (US-PAD-006 — dossie CGCRE, perfil A na borda)
  - padrao.ler_carta             (US-PAD-008-1 — read-model carta Shewhart, perfil A)

Mapeamento perfil x acao:
  - admin_tenant / gerente_operacional: todas.
  - signatario (RT): todas (decisoes/supervisao tecnica do RT).
  - metrologista_bancada: so ler_carta (monitora a carta; nao gere vinculo nem
    exporta dossie regulatorio).
  - atendente: nenhuma (regulatorio/tecnico).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "padrao.gerir_vinculo_auxiliar"),
    ("admin_tenant", "padrao.ler_dossie"),
    ("admin_tenant", "padrao.ler_carta"),
    ("gerente_operacional", "padrao.gerir_vinculo_auxiliar"),
    ("gerente_operacional", "padrao.ler_dossie"),
    ("gerente_operacional", "padrao.ler_carta"),
    ("signatario", "padrao.gerir_vinculo_auxiliar"),
    ("signatario", "padrao.ler_dossie"),
    ("signatario", "padrao.ler_carta"),
    ("metrologista_bancada", "padrao.ler_carta"),
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE/ENABLE RLS controlado."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        cur.execute(
            "SELECT codigo, id FROM authz_perfil "
            "WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
            [list({p for p, _ in MATRIZ})],
        )
        perfil_id_por_codigo = dict(cur.fetchall())
        faltando = {p for p, _ in MATRIZ} - set(perfil_id_por_codigo)
        if faltando:
            # test_afere TransactionTestCase pode ter truncado authz_perfil;
            # fixture autouse re-aplica seeds. Skip cedo (paralelo 0005/M4 0013).
            cur.execute(
                "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
                "FOR ALL USING (false) WITH CHECK (false);"
            )
            cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
            cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")
            return
        for perfil_codigo, acao in MATRIZ:
            perfil_id = perfil_id_por_codigo[perfil_codigo]
            cur.execute(
                "INSERT INTO authz_perfil_acao "
                "(id, perfil_id, acao, pode_executar, criado_em) "
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
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
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
        ("padroes", "0006_check_jsonb_nao_vazio"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
