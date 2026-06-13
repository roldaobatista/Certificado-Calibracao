"""Seed da matriz authz para `precificacao.*` (T-PRC-025 — D-PRC-4 / spec §7).

4 ações × papéis. Espelha o molde configuracoes_sistema/fiscal/PPS:
DISABLE RLS → INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation.
Idempotente.

Ações:
  - precificacao.configurar      (regras/faixas/perfil/parametros — gerente+admin)
  - precificacao.calcular        (usar motor de calculo — atendente+)
  - precificacao.ver_margem      (ver custo/margem estimada — segredo comercial D-PRC-4)
  - precificacao.aprovar_desconto (decidir pedido — papel aprovador)

Mapeamento papel × ação (D-PRC-4 / spec §7):
  - admin_tenant: todas.
  - gerente_operacional: configurar + calcular + ver_margem + aprovar_desconto.
  - signatario: calcular + aprovar_desconto + ver_margem (papel aprovador tem ver_margem).
  - atendente: calcular.
  - metrologista_bancada: calcular.

Coerência D-PRC-4: papel aprovador (signatario / gerente_operacional) DEVE ter
`ver_margem` para avaliar a solicitação de desconto.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_TODAS = [
    "precificacao.configurar",
    "precificacao.calcular",
    "precificacao.ver_margem",
    "precificacao.aprovar_desconto",
]

_SO_CALCULAR = ["precificacao.calcular"]

_APROVADOR = [
    "precificacao.calcular",
    "precificacao.ver_margem",
    "precificacao.aprovar_desconto",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _TODAS],
    *[("gerente_operacional", a) for a in _TODAS],
    # signatario é papel aprovador: precisa ver_margem pra avaliar (D-PRC-4)
    *[("signatario", a) for a in _APROVADOR],
    *[("atendente", a) for a in _SO_CALCULAR],
    *[("metrologista_bancada", a) for a in _SO_CALCULAR],
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
            # fixture autouse re-aplica seeds. Skip cedo — paralelo fiscal/CFG/PPS.
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
        ("precificacao", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
