"""T-CR-025 — Seed da matriz authz para `contas_receber.*` (análogo fiscal 0005).

6 ações × papéis. Espelha o molde fiscal/0005:
DISABLE RLS → INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation.
Idempotente.

Ações:
  - contas_receber.ver              (retrieve/list)
  - contas_receber.criar            (lançamento manual)
  - contas_receber.emitir           (emitir boleto/PIX)
  - contas_receber.baixar           (baixa manual)
  - contas_receber.cancelar         (cancelar título)
  - contas_receber.override_bloqueio (override A3 — papel gerente)

Mapeamento papel × ação:
  - admin_tenant / gerente_financeiro (→ gerente_operacional no seed): todas.
  - atendente / metrologista_bancada / signatario: só leitura.

NOTA: o perfil regulatório (trava CALIBRACAO_RBC só perfil A) é decidido em
RUNTIME no use case (ADR-0073), NÃO pela matriz RBAC aqui (que é por PAPEL).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_ESCRITA = [
    "contas_receber.ver",
    "contas_receber.criar",
    "contas_receber.emitir",
    "contas_receber.baixar",
    "contas_receber.cancelar",
    "contas_receber.override_bloqueio",
]

_SO_LEITURA = ["contas_receber.ver"]

MATRIZ = [
    *[("admin_tenant", a) for a in _ACOES_ESCRITA],
    *[("gerente_operacional", a) for a in _ACOES_ESCRITA],
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
            "SELECT codigo, id FROM authz_perfil " "WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
            [list({p for p, _ in MATRIZ})],
        )
        perfil_id_por_codigo = dict(cur.fetchall())
        faltando = {p for p, _ in MATRIZ} - set(perfil_id_por_codigo)
        if faltando:
            # test_afere TransactionTestCase pode ter truncado authz_perfil;
            # fixture autouse re-aplica seeds. Skip cedo — paralelo M5/M6/M9.
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
        ("contas_receber", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
