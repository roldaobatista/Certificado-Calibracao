"""Seed complementar de authz `precificacao.*` — ações faltantes da migration 0006.

A migration 0006 omitiu quatro ações que views.py referencia:
  - precificacao.ver               (retrieve/vigente/pendentes/listar_faixas/obter_parametros)
  - precificacao.solicitar_aprovacao (AprovacaoDescontoViewSet.solicitar)
  - precificacao.alcada_dono       (_derivar_papel_decisor — admin decide pedidos DONO)
  - precificacao.alcada_gerente    (_derivar_papel_decisor — gerente decide pedidos GERENTE)

Mapeamento papel × ação (completa o D-PRC-4 / spec §7):
  - admin_tenant: ver + solicitar + alcada_dono + alcada_gerente.
  - gerente_operacional: ver + solicitar + alcada_gerente.
  - signatario: ver + solicitar + alcada_gerente (papel aprovador).
  - atendente: ver + solicitar (atendente pode solicitar desconto).
  - metrologista_bancada: ver (consulta; não solicita desconto comercial).

Idempotente: ON CONFLICT DO NOTHING.

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova de RLS de dados
"""

from __future__ import annotations

import uuid

from django.db import migrations

_NOVA_VER = "precificacao.ver"
_NOVA_SOL = "precificacao.solicitar_aprovacao"
_ALCADA_DONO = "precificacao.alcada_dono"
_ALCADA_GERENTE = "precificacao.alcada_gerente"

# Matriz incremental (só as linhas novas — 0006 já inseriu as demais).
# NOTA: apenas perfis SISTÊMICOS (tenant_id IS NULL) — gerente_tenant é
# perfil por tenant, não aparece aqui (ausência causaria skip da seed).
MATRIZ = [
    # admin_tenant: ver + solicitar + alçada máxima (DONO decide qualquer pedido)
    ("admin_tenant", _NOVA_VER),
    ("admin_tenant", _NOVA_SOL),
    ("admin_tenant", _ALCADA_DONO),
    ("admin_tenant", _ALCADA_GERENTE),
    # gerente_operacional: ver + solicitar + alçada GERENTE
    ("gerente_operacional", _NOVA_VER),
    ("gerente_operacional", _NOVA_SOL),
    ("gerente_operacional", _ALCADA_GERENTE),
    # signatario: ver + solicitar + alçada GERENTE (papel aprovador)
    ("signatario", _NOVA_VER),
    ("signatario", _NOVA_SOL),
    ("signatario", _ALCADA_GERENTE),
    # atendente: ver + solicitar (faz o pedido de desconto no balcão)
    ("atendente", _NOVA_VER),
    ("atendente", _NOVA_SOL),
    # metrologista_bancada: ver (consulta apenas; não faz pedido comercial)
    ("metrologista_bancada", _NOVA_VER),
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING — não interfere com block_mutation."""
    with schema_editor.connection.cursor() as cur:
        # Lê IDs dos perfis sistêmicos presentes
        papeis = list({p for p, _ in MATRIZ})
        cur.execute(
            "SELECT codigo, id FROM authz_perfil WHERE codigo = ANY(%s) AND tenant_id IS NULL;",
            [papeis],
        )
        perfil_id_por_codigo = dict(cur.fetchall())
        faltando = set(papeis) - set(perfil_id_por_codigo)
        if faltando:
            # Seeds ainda não aplicadas (ex: rollback de environment) — skip seguro.
            return

        # Desbloqueia temporariamente a policy block_mutation para INSERT
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        try:
            for perfil_codigo, acao in MATRIZ:
                perfil_id = perfil_id_por_codigo.get(perfil_codigo)
                if perfil_id is None:
                    continue
                cur.execute(
                    "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                    "VALUES (%s, %s, %s, TRUE, now()) "
                    "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                    [str(uuid.uuid4()), perfil_id, acao],
                )
        finally:
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
            [[_NOVA_VER, _NOVA_SOL, _ALCADA_DONO, _ALCADA_GERENTE]],
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
        ("precificacao", "0008_seed_faixas_default"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
