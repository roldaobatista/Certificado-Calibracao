"""Seed da matriz authz para `catalogo.*` (T-PPS-021 — NFR PRD `catalogo:edit`).

4 ações × papéis. Espelha o molde configuracoes_sistema/fiscal: DISABLE RLS →
INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - catalogo.ver              (retrieve/listar/preco-vigente)
  - catalogo.editar           (US-CAT-001/002/003/005 — item/versão/kit/inativar)
  - catalogo.gerenciar_tabela (TabelaPreco + linhas — ADR-0081)
  - catalogo.importar         (US-CAT-004 — staging CSV, Fatia 3)

Mapeamento papel × ação:
  - admin_tenant: todas.
  - gerente_operacional: todas (almoxarife/comprador do PRD operam catálogo
    e tabela — gestão operacional do tenant).
  - signatario / metrologista_bancada / atendente: só ver (seleção em OS).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_TODAS = [
    "catalogo.ver",
    "catalogo.editar",
    "catalogo.gerenciar_tabela",
    "catalogo.importar",
]

_SO_LEITURA = ["catalogo.ver"]

MATRIZ = [
    *[("admin_tenant", a) for a in _TODAS],
    *[("gerente_operacional", a) for a in _TODAS],
    *[("signatario", a) for a in _SO_LEITURA],
    *[("metrologista_bancada", a) for a in _SO_LEITURA],
    *[("atendente", a) for a in _SO_LEITURA],
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
            # fixture autouse re-aplica seeds. Skip cedo — paralelo fiscal/CFG.
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
        ("produtos_pecas_servicos", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
