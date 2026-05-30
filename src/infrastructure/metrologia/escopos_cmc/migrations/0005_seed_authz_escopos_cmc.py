"""Seed da matriz authz para `escopos_cmc.*` — M6 (T-ECMC-015).

6 ações canônicas × perfis. Espelha o padrão do M5
(padroes/0005_seed_authz_padroes): DISABLE RLS -> INSERT ON CONFLICT DO NOTHING
-> re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - escopos_cmc.ver                 (list/retrieve/cobertura)
  - escopos_cmc.cadastrar           (US-ECMC-001 — escopo RBC perfil A)
  - escopos_cmc.declarar_capacidade (US-ECMC-007 — capacidade interna B/C/D)
  - escopos_cmc.revisar             (US-ECMC-002 — nova versão, AC-CAL-015-2)
  - escopos_cmc.revogar             (US-ECMC-003 — soft-delete B)
  - escopos_cmc.confirmar_extraido  (Fatia 4 — confirma rascunho PDF, INV-ECMC-007)

NOTA: o perfil regulatório A/B/C/D (escopo RBC vs capacidade interna) é decidido
em RUNTIME por `tenant_perfil_e`/`rbc_efetivo` (ADR-0067/0075), NÃO pela matriz
RBAC aqui (que é por PAPEL: admin/gerente/RT/metrologista/atendente).

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional / signatario (RT): todas (o escopo de
    acreditação é responsabilidade do RT + gestão).
  - metrologista_bancada / atendente: só leitura.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_ESCRITA = [
    "escopos_cmc.ver",
    "escopos_cmc.cadastrar",
    "escopos_cmc.declarar_capacidade",
    "escopos_cmc.revisar",
    "escopos_cmc.revogar",
    "escopos_cmc.confirmar_extraido",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES_ESCRITA],
    *[("gerente_operacional", a) for a in _ACOES_ESCRITA],
    *[("signatario", a) for a in _ACOES_ESCRITA],
    ("metrologista_bancada", "escopos_cmc.ver"),
    ("atendente", "escopos_cmc.ver"),
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
            # do proximo test) — paralelo M4 0013 / M5 0005.
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
        ("escopos_cmc", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
