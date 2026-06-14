"""T-ORC-025 — seed da matriz authz `orcamento.*` (molde ordens_servico/0013+0021).

9 acoes canonicas x 5 perfis seedados (admin_tenant, gerente_operacional,
atendente, metrologista_bancada, tecnico).

Acoes (D-ORC-12 / spec §7):
- criar / editar / enviar / aprovar / recusar / cancelar / ver / gerir_template / ver_margem.

Distribuicao (decisao de produto registrada — revisavel; molde scoping da OS):
- admin_tenant         -> 9 (dono do tenant: tudo)
- gerente_operacional  -> 9 (aprova orcamento interno + ve margem/comissao)
- atendente            -> criar/editar/enviar/recusar/cancelar/ver/gerir_template
                          (recepcao comercial faz o ciclo; NAO aprova interno, NAO ve margem)
- metrologista_bancada -> ver (consulta o orcamento tecnico que vira OS)
- tecnico              -> ver (consulta; executor de campo)

`ver_margem` (segredo comercial — INV-ORC-MARGEM-OFF / D-ORC-10) restrito a
admin_tenant + gerente_operacional. `aprovar` interno NAO vai a atendente
(aprovacao publica do cliente e via token, sem authz — D-ORC-7).

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova
"""

from __future__ import annotations

import uuid

from django.db import migrations

_ACOES_TODAS = (
    "orcamento.criar",
    "orcamento.editar",
    "orcamento.enviar",
    "orcamento.aprovar",
    "orcamento.recusar",
    "orcamento.cancelar",
    "orcamento.ver",
    "orcamento.gerir_template",
    "orcamento.ver_margem",
)
_ACOES_ATENDENTE = (
    "orcamento.criar",
    "orcamento.editar",
    "orcamento.enviar",
    "orcamento.recusar",
    "orcamento.cancelar",
    "orcamento.ver",
    "orcamento.gerir_template",
)

MATRIZ: list[tuple[str, str]] = (
    [("admin_tenant", a) for a in _ACOES_TODAS]
    + [("gerente_operacional", a) for a in _ACOES_TODAS]
    + [("atendente", a) for a in _ACOES_ATENDENTE]
    + [("metrologista_bancada", "orcamento.ver")]
    + [("tecnico", "orcamento.ver")]
)


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE RLS controlado (molde 0021)."""
    perfis_alvo = {p for p, _ in MATRIZ}
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        # Le os perfis-modelo (tenant_id NULL) com RLS de authz_perfil SUSPENSA — necessario
        # quando a migration roda como app_user sem tenant context (test DB incremental).
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("SELECT codigo, id FROM authz_perfil WHERE tenant_id IS NULL;")
        todos_perfis = dict(cur.fetchall())
        cur.execute("ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;")
        faltando = perfis_alvo - set(todos_perfis)
        if faltando and todos_perfis:
            raise RuntimeError(
                f"Perfis seedados nao encontrados: {sorted(faltando)} — "
                "rode authz/0003 + authz/0007 antes desta migration."
            )
        # todos_perfis vazio => test DB com authz_perfil truncada; conftest re-seeda em runtime.
        for perfil_codigo, acao in MATRIZ:
            perfil_id = todos_perfis.get(perfil_codigo)
            if perfil_id is None:
                continue
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
    acoes = list({a for _, a in MATRIZ})
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute(
            "DELETE FROM authz_perfil_acao WHERE acao = ANY(%s);",
            [acoes],
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
        ("orcamentos", "0005_grants_app_user"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
