"""SEG-CAL-06 conserto P5 (2026-05-27) — GRANT app_user nas 23 tabelas M4.

# metrologia-classificacao: IQ  (GRANT puro — nao altera schema nem motor)
# replay-fixture: none
# audit-immutability: skip -- GRANT na tabela auditavel evento_de_calibracao nao toca trigger imutavel
# rls-policy: external 0002 (RLS ja aplicada em 0002_rls_policies + 0009/0010/0011)

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explicito, app_user (role da web app) NAO tem privilege em INSERT/SELECT/
UPDATE/DELETE nas 23 tabelas M4 — RLS bloqueia DEPOIS, mas faltaria
privilege antes. Em test funciona porque OWNER=app_user (memoria
feedback_test_db_owner_app_user 2026-05-24).

Migration concede GRANT SELECT, INSERT, UPDATE, DELETE em todas as tabelas
calibracao para a role `app_user`. DELETE permanece bloqueado em PROD via
triggers PG WORM nas tabelas append-only (evento_de_calibracao, leitura,
leitura_correcao, padrao_usado) — GRANT permite o opcode, trigger nega.

Justifica nao-aplicar GRANT TRUNCATE: nao precisa em runtime; admin direto
no PG executa via psql como app_migrator.
"""

from __future__ import annotations

from django.db import migrations

# 23 tabelas calibracao (db_table das classes em models.py + evento_de_calibracao
# da migration 0009). Lista canonica; nao usar wildcards.
TABELAS_M4 = (
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
    "laboratorio_subcontratado",
    "aceite_subcontratacao",
    "avaliacao_periodica_subcontratado",
    "aceite_regra_decisao",
    "override_regra_decisao_cliente",
    "reclamacao_calibracao",
    "consentimento_contato_tecnico_cliente",
    "consentimento_foto_recusado",
    "evento_backup_metrologico",
)


def _gerar_grants() -> str:
    return "\n".join(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;"
        for t in TABELAS_M4
    )


def _gerar_revokes() -> str:
    return "\n".join(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;"
        for t in TABELAS_M4
    )


SQL_FORWARD = f"""
-- SEG-CAL-06: GRANT em 23 tabelas M4 para app_user.
-- Em test (OWNER=app_user) ja funciona; em PROD (OWNER=app_migrator) sem
-- GRANT a web app falha em INSERT/SELECT antes mesmo de chegar na RLS.
{_gerar_grants()}
"""

SQL_REVERSE = f"""
{_gerar_revokes()}
"""


class Migration(migrations.Migration):

    dependencies = [
        ("calibracao", "0013_seed_authz_calibracao"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
