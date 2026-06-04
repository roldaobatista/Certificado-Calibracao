"""Seed authz da acao `calibracao.registrar_recebimento_subcontratado`
(T-CAL-129 — destrava SubcontratacaoViewSet REST cl. 6.6 / US-CAL-017).

A acao `calibracao.subcontratar` ja foi seedada na 0013; o recebimento do
certificado externo (AGUARDANDO_SUBCONTRATADO -> RECEBIDA_DO_SUBCONTRATADO)
faltava no authz porque o ViewSet so chega agora (Wave A consolidacao).

Mapeamento perfil x acao (recebimento = funcao de gestao/qualidade):
  - admin_tenant         (dono do tenant)
  - gerente_operacional  (fecha o ciclo de subcontratacao cl. 6.6)
  - signatario           (RT confere o certificado do subcontratado cl. 6.2)

`metrologista_bancada` (tipico executor) NAO recebe a acao por authz; ainda
que recebesse, o use case `registrar_recebimento_subcontratado` enforce
`recebedor != executor` (INV-CAL-FRAUDE-RECEB-001 cl. 6.2.5) — defesa em
profundidade.

Idempotente (ON CONFLICT DO NOTHING) + tratamento TransactionTestCase truncate
identico a 0013_seed_authz_calibracao (memoria feedback_truncate_seed_transactional).
"""

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova

from __future__ import annotations

import uuid

from django.db import migrations

MATRIZ = [
    ("admin_tenant", "calibracao.registrar_recebimento_subcontratado"),
    ("gerente_operacional", "calibracao.registrar_recebimento_subcontratado"),
    ("signatario", "calibracao.registrar_recebimento_subcontratado"),
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE RLS controlado."""
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
            # test_afere + TransactionTestCase: authz_perfil pode estar TRUNCADA;
            # a fixture autouse _restaura_seeds_apos_truncate re-aplica os seeds
            # em ordem. Skip (early return) ao inves de raise (paralelo 0013).
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
        ("calibracao", "0020_fix_arredondamento_regra_max_length"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
