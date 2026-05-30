"""Seed da matriz authz para `procedimentos_calibracao.*` — M7 (T-PROC-025).

5 ações canônicas × papéis. Espelha o padrão M6 (escopos_cmc/0005): DISABLE RLS
-> INSERT ON CONFLICT DO NOTHING -> re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - procedimentos_calibracao.ver       (list/retrieve/resolução)
  - procedimentos_calibracao.cadastrar (US-PROC-001 — RASCUNHO)
  - procedimentos_calibracao.publicar  (US-PROC-002 — RT publica, cl. 7.2.1/8.3)
  - procedimentos_calibracao.revisar   (US-PROC-003 — nova versão, AC-CAL-016-3)
  - procedimentos_calibracao.revogar   (US-PROC-004 — soft-delete B)

NOTA: o bloqueio 412 só-RBC (perfil A) é decidido em RUNTIME por `tenant_perfil_e`
(ADR-0067 / D-PROC-1), NÃO pela matriz RBAC aqui (que é por PAPEL).

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional / signatario (RT): todas (procedimento é
    responsabilidade do RT + gestão; publicar exige aprovação cl. 8.3.1).
  - metrologista_bancada / atendente: só leitura.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES = [
    "procedimentos_calibracao.ver",
    "procedimentos_calibracao.cadastrar",
    "procedimentos_calibracao.publicar",
    "procedimentos_calibracao.revisar",
    "procedimentos_calibracao.revogar",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES],
    *[("gerente_operacional", a) for a in _ACOES],
    *[("signatario", a) for a in _ACOES],
    ("metrologista_bancada", "procedimentos_calibracao.ver"),
    ("atendente", "procedimentos_calibracao.ver"),
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
            # fixture autouse re-aplica seeds. Skip cedo (estado restaurado antes
            # do proximo test) — paralelo M4 0013 / M5 0005 / M6 0005.
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
        ("procedimentos_calibracao", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
