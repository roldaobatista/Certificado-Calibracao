"""Seed authz `os.gerir_item_comercial` — T-OSME-035 / ADR-0082.

Acao nova para CRUD de ItemComercialOS (adicionar/remover item comercial
numa OS nao-terminal — spec os-multi-equipamento §7 / INV-OSME-ITEMCOM-001).

Distribuicao de perfis:
- admin_tenant         -> gerir (tudo)
- gerente_operacional  -> gerir (excecoes operacionais)
- atendente            -> gerir (recepcao inclui/remove item comercial)
- metrologista_bancada -> NAO (executa calibracao, nao gere comercial)
- tecnico              -> NAO (executor de campo, nao gere comercial)

Rationale: item comercial (deslocamento/taxa) e responsabilidade da frente
comercial/atendimento, nao do executor tecnico. Segue o mesmo scoping de
`os.abrir` e `os.cancelar`.
"""

# policy-test-coverage: skip -- seed apenas, sem CREATE POLICY nova

from __future__ import annotations

import uuid

from django.db import migrations

ACAO = "os.gerir_item_comercial"

PERFIS_COM_PERMISSAO = [
    "admin_tenant",
    "gerente_operacional",
    "atendente",
]


def seed(apps, schema_editor):
    """Idempotente: ON CONFLICT DO NOTHING + DISABLE RLS controlado."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute(
            "DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;"
        )
        # Le os perfis-modelo (tenant_id NULL) com RLS de authz_perfil SUSPENSA.
        # Necessario porque a policy `authz_perfil_select` (authz/0002) depende de
        # `current_setting('app.tenant_ids')`: quando esta migration roda como
        # app_user SEM tenant context (test DB aplicado incrementalmente, nao via
        # migrator BYPASSRLS), o SELECT erraria/filtraria. DISABLE so SUSPENDE o
        # enforcement — as policies (select + block_mutation) persistem e voltam no
        # ENABLE/FORCE. Via migrator (producao) o DISABLE e inocuo.
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("SELECT codigo, id FROM authz_perfil WHERE tenant_id IS NULL;")
        todos_perfis = dict(cur.fetchall())  # {codigo: id} de TODOS os perfis globais
        cur.execute("ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;")
        faltando = set(PERFIS_COM_PERMISSAO) - set(todos_perfis)
        if faltando and todos_perfis:
            # Ha perfis globais mas faltam ESTES -> erro real de ordem/seed (producao).
            raise RuntimeError(
                f"Perfis seedados nao encontrados: {sorted(faltando)} — "
                "rode authz/0003 + authz/0007 antes desta migration."
            )
        # `todos_perfis` vazio => test DB com authz_perfil TRUNCADA no migrate incremental
        # (--reuse-db + TransactionTestCase): o conftest `_SEED_MIGRATIONS` re-seeda em
        # runtime (authz/0003 popula os perfis ANTES desta migration na ordem do catalogo).
        # Nao falhamos aqui — apenas inserimos o que existir; ON CONFLICT torna idempotente.
        for perfil_codigo in PERFIS_COM_PERMISSAO:
            perfil_id = todos_perfis.get(perfil_codigo)
            if perfil_id is None:
                continue
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, %s, TRUE, now()) "
                "ON CONFLICT (perfil_id, acao) DO NOTHING;",
                [str(uuid.uuid4()), perfil_id, ACAO],
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
            "DELETE FROM authz_perfil_acao WHERE acao = %s;",
            [ACAO],
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
        ("ordens_servico", "0020_item_comercial_os"),
        ("authz", "0007_seed_perfis_marco_3_4"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
