"""Seed da matriz authz para `colaboradores.*` (T-COL-025 — D-COL-4 / spec §7).

10 ações × papéis de perfil. Molde exato do precificacao/0006_seed_authz_precificacao.py.
DISABLE RLS → INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation.
Idempotente.

Ações:
  - colaboradores.cadastrar          (criar novo colaborador)
  - colaboradores.editar             (editar dados do colaborador)
  - colaboradores.desligar           (registrar desligamento)
  - colaboradores.ver                (visualizar dados não-PII)
  - colaboradores.ver_pii            (visualizar CPF/email/telefone — PII)
  - colaboradores.gerir_papel        (atribuir/revogar papéis de negócio)
  - colaboradores.gerir_habilidade   (registrar/remover habilidades)
  - colaboradores.ver_comissao       (visualizar comissão — dado sensível)
  - colaboradores.ver_auditoria      (visualizar trilha de auditoria)
  - colaboradores.consultar_elegiveis (listar colaboradores elegíveis para atribuição)

Mapeamento papel × ação (D-COL-4 / spec §7):
  - admin_tenant: todas.
  - gerente_operacional: todas.
  - signatario: ver, consultar_elegiveis.
  - atendente: ver, consultar_elegiveis.
  - tecnico: ver, consultar_elegiveis.
  - metrologista_bancada: ver, consultar_elegiveis.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_TODAS = [
    "colaboradores.cadastrar",
    "colaboradores.editar",
    "colaboradores.desligar",
    "colaboradores.ver",
    "colaboradores.ver_pii",
    "colaboradores.gerir_papel",
    "colaboradores.gerir_habilidade",
    "colaboradores.ver_comissao",
    "colaboradores.ver_auditoria",
    "colaboradores.consultar_elegiveis",
]

_SO_VER = [
    "colaboradores.ver",
    "colaboradores.consultar_elegiveis",
]

MATRIZ = [
    *[("admin_tenant", a) for a in _TODAS],
    *[("gerente_operacional", a) for a in _TODAS],
    *[("signatario", a) for a in _SO_VER],
    *[("atendente", a) for a in _SO_VER],
    *[("tecnico", a) for a in _SO_VER],
    *[("metrologista_bancada", a) for a in _SO_VER],
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
            # TransactionTestCase pode ter truncado authz_perfil;
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
        ("colaboradores", "0004_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
