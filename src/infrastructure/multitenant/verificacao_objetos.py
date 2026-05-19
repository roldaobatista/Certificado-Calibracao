"""Verificação de que objetos de segurança existem FISICAMENTE no banco.

FA-A4 (auditoria F-A rodada 1). O `manage.py migrate` pode reportar
"Applying ... OK" SEM executar o SQL de um `RunSQL` quando rodado no alias
errado (`router.allow_migrate` só executa no alias `migrator`; rodar no
`default` marca aplicada mas pula a operação). Resultado: RLS/trigger/policy
pode estar registrado em `django_migrations` e NÃO existir no banco.

Esta é a rede de proteção PERMANENTE: confere o catálogo real do Postgres
(`pg_class`, `pg_policies`, `pg_trigger`, `pg_proc`) contra o inventário
mínimo esperado. Usada por `tests/test_migrations_persistem.py` (roda na
suite) e pelo command `verificar_objetos_seguranca` (drill F-A). Fonte
única — não duplicar a lista.
"""

from __future__ import annotations

from django.db import connection

# Tabelas que DEVEM ter RLS habilitada E forçada (FORCE). Se uma migration
# de RLS reportar OK sem aplicar, relrowsecurity/relforcerowsecurity = false.
TABELAS_RLS = (
    "auditoria",
    "acessos_dados_cliente",
    "clientes",
    "cliente_bloqueios",
    "feature_flags",
    "usuario_perfil_tenant",
    "authz_decisions",
    "authz_perfil",
    "authz_perfil_acao",
)

# Triggers anti-mutation (imutabilidade de trilha — ISO 17025 / LGPD).
TRIGGERS_ANTI_MUTATION = (
    ("auditoria", "auditoria_anti_delete"),
    ("auditoria", "auditoria_anti_update"),
    ("acessos_dados_cliente", "acessos_anti_delete"),
    ("acessos_dados_cliente", "acessos_anti_update"),
    ("authz_decisions", "authz_decisions_anti_delete"),
    ("authz_decisions", "authz_decisions_anti_update"),
)

# Funções PL/pgSQL de segurança criadas por RunSQL.
FUNCOES_SEGURANCA = (
    "require_tenant_ctx",
    "auditoria_bloqueia_mutation",
    "acessos_bloqueia_mutation",
    "authz_decisions_bloqueia_mutation",
)


def verificar_objetos_seguranca() -> list[str]:
    """Retorna lista de problemas (vazia = tudo no banco como esperado).

    Cada string é um objeto de segurança que a migration deveria ter criado
    e NÃO está no catálogo real do Postgres.
    """
    problemas: list[str] = []
    with connection.cursor() as cur:
        # 1. RLS habilitada + forçada em cada tabela sensível.
        cur.execute(
            "SELECT relname, relrowsecurity, relforcerowsecurity "
            "FROM pg_class WHERE relkind='r' AND relname = ANY(%s);",
            [list(TABELAS_RLS)],
        )
        achadas = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
        for tabela in TABELAS_RLS:
            if tabela not in achadas:
                problemas.append(f"tabela ausente no banco: {tabela}")
                continue
            rowsec, forcesec = achadas[tabela]
            if not rowsec:
                problemas.append(f"RLS NAO habilitada em {tabela} (migration mentiu?)")
            if not forcesec:
                problemas.append(f"FORCE RLS NAO ativo em {tabela} (migration mentiu?)")

        # 2. Cada tabela RLS tem pelo menos 1 policy.
        cur.execute(
            "SELECT tablename, count(*) FROM pg_policies "
            "WHERE schemaname='public' AND tablename = ANY(%s) GROUP BY tablename;",
            [list(TABELAS_RLS)],
        )
        policies_por_tabela = {r[0]: r[1] for r in cur.fetchall()}
        for tabela in TABELAS_RLS:
            if policies_por_tabela.get(tabela, 0) == 0:
                problemas.append(f"nenhuma policy RLS em {tabela} (migration mentiu?)")

        # 3. Triggers anti-mutation existem.
        cur.execute(
            "SELECT tgrelid::regclass::text, tgname FROM pg_trigger " "WHERE NOT tgisinternal;"
        )
        triggers = {(r[0], r[1]) for r in cur.fetchall()}
        for tabela, trig in TRIGGERS_ANTI_MUTATION:
            if (tabela, trig) not in triggers:
                problemas.append(f"trigger anti-mutation ausente: {tabela}.{trig}")

        # 4. Funções de segurança existem.
        cur.execute(
            "SELECT proname FROM pg_proc "
            "WHERE pronamespace='public'::regnamespace AND proname = ANY(%s);",
            [list(FUNCOES_SEGURANCA)],
        )
        funcs = {r[0] for r in cur.fetchall()}
        for fn in FUNCOES_SEGURANCA:
            if fn not in funcs:
                problemas.append(f"funcao de seguranca ausente: {fn}() (migration mentiu?)")

    return problemas
