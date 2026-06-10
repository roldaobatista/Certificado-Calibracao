"""Seed da matriz authz para `configuracoes_sistema.*` (T-CFG-025 / D-CFG-8).

7 ações × papéis. Espelha o molde fiscal (0005_seed_authz_fiscal): DISABLE RLS →
INSERT ON CONFLICT DO NOTHING → re-CREATE POLICY block_mutation. Idempotente.

Ações:
  - configuracoes_sistema.ver               (retrieve/listar)
  - configuracoes_sistema.atualizar_empresa (US-CFG-001)
  - configuracoes_sistema.gerenciar_filial  (US-CFG-001 — adicionar/editar)
  - configuracoes_sistema.cadastrar_imposto (US-CFG-003)
  - configuracoes_sistema.encerrar_imposto  (US-CFG-003 — encerrar vigência)
  - configuracoes_sistema.criar_serie       (US-CFG-002)
  - configuracoes_sistema.reservar_numero   (US-CFG-002 — consumo por emissores)

Mapeamento papel × ação:
  - admin_tenant: todas (config tributária/cadastral é administração do tenant).
  - gerente_operacional: ver + criar_serie + reservar_numero (operação emite
    documentos; NÃO mexe em empresa/tributos).
  - signatario / metrologista_bancada / atendente: só ver.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_TODAS = [
    "configuracoes_sistema.ver",
    "configuracoes_sistema.atualizar_empresa",
    "configuracoes_sistema.gerenciar_filial",
    "configuracoes_sistema.cadastrar_imposto",
    "configuracoes_sistema.encerrar_imposto",
    "configuracoes_sistema.criar_serie",
    "configuracoes_sistema.reservar_numero",
]

_OPERACAO = [
    "configuracoes_sistema.ver",
    "configuracoes_sistema.criar_serie",
    "configuracoes_sistema.reservar_numero",
]

_SO_LEITURA = ["configuracoes_sistema.ver"]

MATRIZ = [
    *[("admin_tenant", a) for a in _TODAS],
    *[("gerente_operacional", a) for a in _OPERACAO],
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
            # fixture autouse re-aplica seeds. Skip cedo — paralelo fiscal/M9.
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
        ("configuracoes_sistema", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
