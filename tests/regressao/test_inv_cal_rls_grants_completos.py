"""T-CAL-025: drill RLS + grants completos nas 23 tabelas M4 calibracao.

Validacao automatizada do fechamento P4 Fase 1 (migrations 0001..0012 +
ordens_servico.0014 cross-marco). Garante que toda tabela M4 tem:

1. RLS habilitada (relrowsecurity=true) — INV-TENANT-001.
2. FORCE ROW LEVEL SECURITY (relforcerowsecurity=true) — bloqueia
   bypass de owner (INV-TENANT-002).
3. app_user com 4 grants (SELECT, INSERT, UPDATE, DELETE) — sem grants,
   queries de runtime batem em "permission denied".
4. app_migrator com >=5 grants (SELECT, INSERT, UPDATE, DELETE, TRUNCATE).

Se algum item falhar, este teste pega antes do drill `validar_m4_calibracao`
(Fase 10 — T-CAL-145..160). Mata por causa-raiz: bloqueia commit que
introduzir migration nova sem RLS/grants apropriados.

Trigger pra esse teste: hook `migration-rls-check.sh` ja garante na origem
(BLOCK em migration nova que cria tabela com tenant_id sem CREATE POLICY).
Este teste eh defesa em runtime — pega mesmo se hook for desabilitado.
"""

from __future__ import annotations

import pytest
from django.db import connection


# Lista canonica das 23 tabelas M4 (P4 Fase 1 completa)
TABELAS_M4 = [
    # Migration 0001-0010 (T-CAL-001..014)
    "calibracao",
    "leitura",
    "leitura_correcao",
    "condicoes_ambientais",
    "orcamento_incerteza",
    "componente_incerteza",
    "orcamento_por_ponto",
    "padrao_usado",
    "recepcao_item_calibracao",
    "medicao_controle",
    "evento_de_calibracao",
    "nao_conformidade",
    "analise_impacto_nc_proficiencia",
    "plano_acao_proficiencia_warning",
    # Migration 0011 (T-CAL-015..017+021 cluster subcontratacao)
    "laboratorio_subcontratado",
    "aceite_subcontratacao",
    "avaliacao_periodica_subcontratado",
    "aceite_regra_decisao",
    # Migration 0012 (T-CAL-018..020+023 entidades P3 advogado+RBC)
    "override_regra_decisao_cliente",
    "reclamacao_calibracao",
    "consentimento_contato_tecnico_cliente",
    "consentimento_foto_recusado",
    "evento_backup_metrologico",
]

GRANTS_APP_USER_ESPERADOS = {"SELECT", "INSERT", "UPDATE", "DELETE"}
GRANTS_APP_MIGRATOR_MINIMOS = {"SELECT", "INSERT", "UPDATE", "DELETE", "TRUNCATE"}


@pytest.mark.django_db
def test_t_cal_025_todas_23_tabelas_m4_existem_em_pg():
    """As 23 tabelas M4 P4 Fase 1 estao criadas em PG (sanity check)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT relname
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname = ANY(%s)
            """,
            [TABELAS_M4],
        )
        existentes = {row[0] for row in cur.fetchall()}
    faltando = set(TABELAS_M4) - existentes
    assert (
        not faltando
    ), f"T-CAL-025: tabelas M4 ausentes em PG (P4 Fase 1 incompleta): {faltando}"


@pytest.mark.django_db
def test_t_cal_025_todas_23_tabelas_m4_tem_rls_habilitada():
    """relrowsecurity=true em todas as 23 tabelas (INV-TENANT-001)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT relname, relrowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname = ANY(%s)
            """,
            [TABELAS_M4],
        )
        sem_rls = [row[0] for row in cur.fetchall() if row[1] is False]
    assert not sem_rls, (
        f"INV-TENANT-001 VIOLADA: tabelas M4 sem RLS habilitada: {sem_rls}. "
        f"Cada migration nova deve ENABLE ROW LEVEL SECURITY na mesma transacao."
    )


@pytest.mark.django_db
def test_t_cal_025_todas_23_tabelas_m4_tem_force_rls():
    """relforcerowsecurity=true (INV-TENANT-002 — bloqueia bypass de owner)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT relname, relforcerowsecurity
            FROM pg_class c
            JOIN pg_namespace n ON c.relnamespace = n.oid
            WHERE n.nspname = 'public'
              AND c.relkind = 'r'
              AND c.relname = ANY(%s)
            """,
            [TABELAS_M4],
        )
        sem_force = [row[0] for row in cur.fetchall() if row[1] is False]
    assert not sem_force, (
        f"INV-TENANT-002 VIOLADA: tabelas M4 sem FORCE ROW LEVEL SECURITY: "
        f"{sem_force}. Sem FORCE, o owner (app_migrator) bypassa RLS."
    )


@pytest.mark.django_db
def test_t_cal_025_app_user_tem_4_grants_em_todas_23_tabelas():
    """app_user precisa SELECT/INSERT/UPDATE/DELETE pra runtime funcionar."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, privilege_type
            FROM information_schema.table_privileges
            WHERE table_schema = 'public'
              AND grantee = 'app_user'
              AND table_name = ANY(%s)
            """,
            [TABELAS_M4],
        )
        grants_por_tabela: dict[str, set[str]] = {}
        for tabela, priv in cur.fetchall():
            grants_por_tabela.setdefault(tabela, set()).add(priv)

    tabelas_incompletas: dict[str, set[str]] = {}
    for tabela in TABELAS_M4:
        atual = grants_por_tabela.get(tabela, set())
        faltando = GRANTS_APP_USER_ESPERADOS - atual
        if faltando:
            tabelas_incompletas[tabela] = faltando

    assert not tabelas_incompletas, (
        f"T-CAL-025: app_user sem grants completos em tabelas M4 "
        f"(runtime quebra com 'permission denied'). Faltando: "
        f"{tabelas_incompletas}. Conferir ALTER DEFAULT PRIVILEGES no setup."
    )


@pytest.mark.django_db
def test_t_cal_025_app_migrator_tem_5_grants_minimos_em_todas_23_tabelas():
    """app_migrator precisa SELECT/INSERT/UPDATE/DELETE/TRUNCATE.

    Skip em test_afere — OWNER do banco eh app_user (nao app_migrator). Em
    DEV/PROD, owner eh app_migrator e este check vale (memoria
    feedback_test_db_owner_app_user.md).
    """
    with connection.cursor() as cur:
        cur.execute("SELECT current_database();")
        db = cur.fetchone()[0]
    if db.startswith("test_"):
        pytest.skip(
            "Banco de teste tem OWNER=app_user; check de app_migrator nao se aplica "
            "(memoria test_db_owner_app_user). Validacao real eh em DEV/PROD."
        )
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT table_name, privilege_type
            FROM information_schema.table_privileges
            WHERE table_schema = 'public'
              AND grantee = 'app_migrator'
              AND table_name = ANY(%s)
            """,
            [TABELAS_M4],
        )
        grants_por_tabela: dict[str, set[str]] = {}
        for tabela, priv in cur.fetchall():
            grants_por_tabela.setdefault(tabela, set()).add(priv)

    tabelas_incompletas: dict[str, set[str]] = {}
    for tabela in TABELAS_M4:
        atual = grants_por_tabela.get(tabela, set())
        faltando = GRANTS_APP_MIGRATOR_MINIMOS - atual
        if faltando:
            tabelas_incompletas[tabela] = faltando

    assert not tabelas_incompletas, (
        f"T-CAL-025: app_migrator sem grants minimos em tabelas M4. "
        f"Faltando: {tabelas_incompletas}."
    )


@pytest.mark.django_db
def test_t_cal_025_todas_23_tabelas_tem_4_policies_rls():
    """Cada tabela M4 tem 4 policies (SELECT/UPDATE/DELETE/INSERT)."""
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT tablename, COUNT(*) AS qtd_policies
            FROM pg_policies
            WHERE schemaname = 'public'
              AND tablename = ANY(%s)
            GROUP BY tablename
            """,
            [TABELAS_M4],
        )
        contagem = dict(cur.fetchall())

    tabelas_com_policies_incompletas = {
        tabela: contagem.get(tabela, 0)
        for tabela in TABELAS_M4
        if contagem.get(tabela, 0) < 4
    }
    assert not tabelas_com_policies_incompletas, (
        f"T-CAL-025: tabelas M4 com menos de 4 policies (esperado: "
        f"SELECT+UPDATE+DELETE+INSERT). Atual: "
        f"{tabelas_com_policies_incompletas}."
    )
