"""Seed da matriz authz para `licencas.*` — M9 (T-LIC-020).

5 ações canônicas × papéis. Espelha M5/M6/M7: DISABLE RLS -> INSERT ON CONFLICT
DO NOTHING -> re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - licencas.ver                 (list/retrieve/histórico)
  - licencas.cadastrar           (US-LIC-001 — inclui promoção perfil A com A3)
  - licencas.renovar             (US-LIC-002/004 — nova revisão)
  - licencas.acionar_emergencial (US-LIC-003 — INV-033, A3 + justificativa ≥100ch)
  - licencas.revogar             (soft-delete B)

NOTA: o perfil regulatório A/B/C/D (quem cadastra ACREDITACAO_CGCRE) é decidido em
RUNTIME por `tenant_perfil_e(['A','B','C'])` (INV-LIC-PERFIL-001 — defesa L6), NÃO
pela matriz RBAC aqui (que é por PAPEL).

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional / signatario (RT): todas.
  - metrologista_bancada / atendente: só leitura.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_ESCRITA = [
    "licencas.ver",
    "licencas.cadastrar",
    "licencas.renovar",
    "licencas.acionar_emergencial",
    "licencas.revogar",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES_ESCRITA],
    *[("gerente_operacional", a) for a in _ACOES_ESCRITA],
    *[("signatario", a) for a in _ACOES_ESCRITA],
    ("metrologista_bancada", "licencas.ver"),
    ("atendente", "licencas.ver"),
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
        ("licencas_acreditacoes", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
