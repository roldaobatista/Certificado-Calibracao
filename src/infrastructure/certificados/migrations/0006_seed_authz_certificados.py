"""Seed da matriz authz para `certificados.*` — M8 (T-CER-025).

5 ações canônicas × papéis. Espelha M7 (procedimentos/0005): DISABLE RLS -> INSERT
ON CONFLICT DO NOTHING -> re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - certificados.ver          (list/retrieve — read-path lê SÓ snapshot, INV-CER-SNAPSHOT-CMC-001)
  - certificados.emitir       (US-CER-001 — emissão metrológica atômica)
  - certificados.reemitir     (US-CER-004 — nova versão)
  - certificados.decidir_ponto (NC-03 — decisão WORM do RT por ponto)
  - certificados.revogar      (pós-emissão; recall normativo = Wave A)

NOTA: o bloqueio RBC só-perfil-A é decidido em RUNTIME por `tenant_perfil_e`
(ADR-0067 / INV-CER-PERFIL-001), NÃO pela matriz RBAC aqui (que é por PAPEL).

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional / signatario (RT): todas.
  - metrologista_bancada / atendente: só leitura.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES = [
    "certificados.ver",
    "certificados.emitir",
    "certificados.reemitir",
    "certificados.decidir_ponto",
    "certificados.revogar",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES],
    *[("gerente_operacional", a) for a in _ACOES],
    *[("signatario", a) for a in _ACOES],
    ("metrologista_bancada", "certificados.ver"),
    ("atendente", "certificados.ver"),
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
            # do proximo test) — paralelo M4 0013 / M5 0005 / M6 0005 / M7 0005.
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
        ("certificados", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
