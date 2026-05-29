"""Seed da matriz authz para `padrao.*` — M5 P5 (T-PAD-041).

9 acoes canonicas padroes x perfis. Espelha o padrao do M4
(calibracao/0013_seed_authz_calibracao): DISABLE RLS -> INSERT ON CONFLICT
DO NOTHING -> re-CREATE POLICY block_mutation. Idempotente.

Acoes:
  - padrao.ler                    (list/retrieve/disponiveis)
  - padrao.cadastrar              (US-PAD-001)
  - padrao.gerir_recal            (envio + retorno — operacional)
  - padrao.aprovar_recal          (analise critica RT — C-4)
  - padrao.registrar_vi           (US-PAD-003)
  - padrao.registrar_pt           (US-PAD-005 — perfil A)
  - padrao.analisar_carta         (US-PAD-008 — decisao RT, perfil A)
  - padrao.baixar                 (US-PAD-004 — A3 RT)
  - padrao.revogar_rastreabilidade (C-5 — evento externo, gestor)

Mapeamento perfil x acao (segregacao cl. 6.2 — quem executa nao aprova):
  - admin_tenant / gerente_operacional: todas.
  - metrologista_bancada: ler + cadastrar + gerir_recal + registrar_vi +
    registrar_pt (executa; NAO aprova recal, NAO analisa carta, NAO baixa).
  - signatario (RT): ler + aprovar_recal + analisar_carta + baixar +
    revogar_rastreabilidade (decisoes tecnicas do RT).
  - atendente: ler.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    # admin_tenant — todas
    ("admin_tenant", "padrao.ler"),
    ("admin_tenant", "padrao.cadastrar"),
    ("admin_tenant", "padrao.gerir_recal"),
    ("admin_tenant", "padrao.aprovar_recal"),
    ("admin_tenant", "padrao.registrar_vi"),
    ("admin_tenant", "padrao.registrar_pt"),
    ("admin_tenant", "padrao.analisar_carta"),
    ("admin_tenant", "padrao.baixar"),
    ("admin_tenant", "padrao.revogar_rastreabilidade"),
    # gerente_operacional — todas
    ("gerente_operacional", "padrao.ler"),
    ("gerente_operacional", "padrao.cadastrar"),
    ("gerente_operacional", "padrao.gerir_recal"),
    ("gerente_operacional", "padrao.aprovar_recal"),
    ("gerente_operacional", "padrao.registrar_vi"),
    ("gerente_operacional", "padrao.registrar_pt"),
    ("gerente_operacional", "padrao.analisar_carta"),
    ("gerente_operacional", "padrao.baixar"),
    ("gerente_operacional", "padrao.revogar_rastreabilidade"),
    # metrologista_bancada — executa (nao aprova proprio trabalho)
    ("metrologista_bancada", "padrao.ler"),
    ("metrologista_bancada", "padrao.cadastrar"),
    ("metrologista_bancada", "padrao.gerir_recal"),
    ("metrologista_bancada", "padrao.registrar_vi"),
    ("metrologista_bancada", "padrao.registrar_pt"),
    # signatario (RT) — decisoes tecnicas
    ("signatario", "padrao.ler"),
    ("signatario", "padrao.aprovar_recal"),
    ("signatario", "padrao.analisar_carta"),
    ("signatario", "padrao.baixar"),
    ("signatario", "padrao.revogar_rastreabilidade"),
    # atendente — so leitura
    ("atendente", "padrao.ler"),
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
            # fixture autouse re-aplica seeds. Skip cedo (estado restaurado
            # antes do proximo test) — paralelo M4 0013.
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
        ("padroes", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
