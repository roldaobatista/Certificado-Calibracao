"""T-CT-026 — Seed da matriz authz para ``caixa_tecnico.*``.

9 ações × papéis. Molde agenda/0006_seed_authz e contas_receber/0005_seed_authz.
DISABLE RLS → INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation.
Idempotente.

Ações:
  - caixa_tecnico.ver                    — leitura (extrato, histórico)
  - caixa_tecnico.solicitar_adiantamento — técnico solicita adiantamento
  - caixa_tecnico.aprovar_adiantamento   — gestor aprova adiantamento
  - caixa_tecnico.entregar_adiantamento  — confirmação de entrega
  - caixa_tecnico.recusar_adiantamento   — gestor recusa adiantamento
  - caixa_tecnico.lancar_despesa         — técnico lança despesa
  - caixa_tecnico.validar_despesa        — gestor valida despesa
  - caixa_tecnico.rejeitar_despesa       — gestor rejeita despesa
  - caixa_tecnico.fechar_prestacao       — gestor fecha prestação de contas

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional: todas as 9 ações.
  - atendente: ver + lancar_despesa + solicitar_adiantamento.
  - metrologista_bancada / signatario: só leitura (ver).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_TODAS = [
    "caixa_tecnico.ver",
    "caixa_tecnico.solicitar_adiantamento",
    "caixa_tecnico.aprovar_adiantamento",
    "caixa_tecnico.entregar_adiantamento",
    "caixa_tecnico.recusar_adiantamento",
    "caixa_tecnico.lancar_despesa",
    "caixa_tecnico.validar_despesa",
    "caixa_tecnico.rejeitar_despesa",
    "caixa_tecnico.fechar_prestacao",
]

_ACOES_ATENDENTE = [
    "caixa_tecnico.ver",
    "caixa_tecnico.lancar_despesa",
    "caixa_tecnico.solicitar_adiantamento",
]

_SO_LEITURA = ["caixa_tecnico.ver"]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES_TODAS],
    *[("gerente_operacional", a) for a in _ACOES_TODAS],
    *[("atendente", a) for a in _ACOES_ATENDENTE],
    *[("signatario", a) for a in _SO_LEITURA],
    *[("metrologista_bancada", a) for a in _SO_LEITURA],
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE/ENABLE RLS controlado."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute(
            "SELECT codigo, id FROM authz_perfil WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
            [list({p for p, _ in MATRIZ})],
        )
        perfil_id_por_codigo = dict(cur.fetchall())
        faltando = {p for p, _ in MATRIZ} - set(perfil_id_por_codigo)
        if faltando:
            # test_afere TransactionTestCase pode ter truncado authz_perfil;
            # fixture autouse re-aplica seeds. Skip cedo.
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
        ("caixa_tecnico", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
