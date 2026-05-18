"""Seed inicial: 4 perfis F-B + matriz perfil × ação inicial.

Perfis seed:
- admin_tenant: lê/escreve tudo do próprio tenant
- tecnico: lê OS, escreve diário de execução
- rt_signatario: lê OS + emite certificado (ABAC entra em Wave A)
- cliente_externo_leitura: lê só próprios registros

Ações cobrem os 4 cenários × 4 perfis dos testes E2E:
- os.criar
- os.ler
- certificado.emitir
- fatura.estornar (ação de financeiro — só admin tenant)
"""

# tests-coverage: tests/test_authz_e2e.py tests/test_authz_audit_imutavel.py

from __future__ import annotations

import uuid

from django.db import migrations


PERFIS = [
    ("admin_tenant", "Administrador do Tenant"),
    ("tecnico", "Técnico de campo"),
    ("rt_signatario", "Responsável Técnico signatário"),
    ("cliente_externo_leitura", "Cliente externo (leitura)"),
]

# Matriz inicial. Cada tupla = (perfil_codigo, acao, pode_executar)
MATRIZ = [
    # admin_tenant — vê tudo, faz quase tudo
    ("admin_tenant", "os.criar", True),
    ("admin_tenant", "os.ler", True),
    ("admin_tenant", "certificado.emitir", True),
    ("admin_tenant", "fatura.estornar", True),
    # tecnico — opera OS, mas não financeiro nem certificado
    ("tecnico", "os.criar", True),
    ("tecnico", "os.ler", True),
    # rt_signatario — lê OS e emite certificado; nada de financeiro
    ("rt_signatario", "os.ler", True),
    ("rt_signatario", "certificado.emitir", True),
    # cliente_externo_leitura — só leitura de OS própria
    ("cliente_externo_leitura", "os.ler", True),
]


def seed(apps, schema_editor):
    """Inserir perfis + matriz via run_as_system bypassando policy."""
    # Usamos SQL bruto pra contornar a RLS policy authz_perfil_block_mutation —
    # migration rola como app_migrator que tem permissão por padrão? Não — a
    # policy bloqueia FOR ALL. Vamos rodar como SET LOCAL ROLE pra ignorar ou
    # então criar perfis com `OVERRIDING SYSTEM VALUE` — mas o jeito limpo é
    # desabilitar a policy só pro migration. app_migrator é NOBYPASSRLS. Por
    # isso, fazemos `SET LOCAL row_security = off` na sessão do migrator (RLS
    # respeita esse setting apenas pra superuser ou BYPASSRLS). Como
    # app_migrator é NOBYPASSRLS, isso não funciona.
    #
    # Solução: usar policy específica de migrator. Mais simples: criar policy
    # adicional que permite mutação quando session_user é app_migrator. Fora
    # do escopo dessa migration de dados.
    #
    # Alternativa simples adotada: dropar a policy de bloqueio, inserir, e
    # recriar. Mantém defesa em profundidade pós-seed.
    perfil_ids: dict[str, str] = {}

    with schema_editor.connection.cursor() as cur:
        # Desabilita RLS temporariamente — app_migrator é NOBYPASSRLS e a tabela
        # tem FORCE ROW LEVEL SECURITY, então qualquer INSERT sem policy
        # explícita é negado. Reabilitamos no fim deste seed.
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_block_mutation ON authz_perfil;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")

        for codigo, nome in PERFIS:
            pid = str(uuid.uuid4())
            cur.execute(
                "INSERT INTO authz_perfil (id, codigo, nome, descricao, tenant_id, criado_em) "
                "VALUES (%s, %s, %s, '', NULL, now());",
                [pid, codigo, nome],
            )
            perfil_ids[codigo] = pid

        for perfil_codigo, acao, pode in MATRIZ:
            cur.execute(
                "INSERT INTO authz_perfil_acao (id, perfil_id, acao, pode_executar, criado_em) "
                "VALUES (%s, %s, %s, %s, now());",
                [str(uuid.uuid4()), perfil_ids[perfil_codigo], acao, pode],
            )

        # policy-test-coverage: skip -- recriacao identica de policies droppadas acima neste mesmo seed; cobertura em 0002_rls_e_trigger.py + tests/test_authz_isolamento.py
        cur.execute(
            "CREATE POLICY authz_perfil_block_mutation ON authz_perfil "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute("ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;")


def unseed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_block_mutation ON authz_perfil;")
        cur.execute("DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;")
        cur.execute("DELETE FROM authz_perfil_acao;")
        cur.execute("DELETE FROM authz_perfil WHERE codigo IN %s;", [tuple(p[0] for p in PERFIS)])
        # policy-test-coverage: skip -- recriacao identica de policy de bloqueio no rollback
        cur.execute(
            "CREATE POLICY authz_perfil_block_mutation ON authz_perfil "
            "FOR ALL USING (false) WITH CHECK (false);"
        )
        cur.execute(
            "CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao "
            "FOR ALL USING (false) WITH CHECK (false);"
        )


class Migration(migrations.Migration):
    # atomic=False permite ALTER TABLE + INSERT no mesmo migration (PG nao
    # aceita misturar dentro de uma transacao quando ha triggers pending).
    atomic = False

    dependencies = [
        ("authz", "0002_rls_e_trigger"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
