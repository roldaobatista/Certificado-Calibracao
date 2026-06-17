"""T-AGE-026 — Seed da matriz authz para ``agenda.*`` (análogo contas_receber/0005).

9 ações × papéis. Espelha o molde fiscal/contas_receber:
DISABLE RLS → INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation.
Idempotente.

Ações:
  - agenda.ver              — leitura da grade (calendário)
  - agenda.criar            — criar novo evento
  - agenda.mover            — mover evento (drag-and-drop)
  - agenda.reagendar        — reagendar evento com notificação
  - agenda.cancelar         — cancelar evento
  - agenda.bloquear         — criar bloqueio de agenda (férias/atestado)
  - agenda.no_show          — registrar no-show
  - agenda.resolver_conflito — resolver conflito de sobreposição
  - agenda.enquadrar_regime  — override humano de regime de jornada (RH/advogado)

Mapeamento papel × ação:
  - admin_tenant / gerente_operacional: todas.
  - atendente: criar + mover + reagendar + cancelar + bloquear + no_show + ver.
  - metrologista_bancada / signatario: só leitura.
  - enquadrar_regime: apenas admin_tenant e gerente_operacional (ato de RH).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_TODAS = [
    "agenda.ver",
    "agenda.criar",
    "agenda.mover",
    "agenda.reagendar",
    "agenda.cancelar",
    "agenda.bloquear",
    "agenda.no_show",
    "agenda.resolver_conflito",
    "agenda.enquadrar_regime",
]

_ACOES_ATENDENTE = [
    "agenda.ver",
    "agenda.criar",
    "agenda.mover",
    "agenda.reagendar",
    "agenda.cancelar",
    "agenda.bloquear",
    "agenda.no_show",
    "agenda.resolver_conflito",
]

_SO_LEITURA = ["agenda.ver"]

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
            "SELECT codigo, id FROM authz_perfil " "WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
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
        ("agenda", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
