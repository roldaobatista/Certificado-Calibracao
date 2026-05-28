"""T-PAD-016 — GRANT app_user nas 6 tabelas M5 (analogo SEG-CAL-06 do M4).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explicito, app_user (role da web app) NAO tem privilege em INSERT/SELECT/
UPDATE/DELETE — RLS bloqueia DEPOIS, mas faltaria privilege antes. Em test
funciona porque OWNER=app_user (memoria feedback_test_db_owner_app_user).

DELETE permanece bloqueado em PROD pelos triggers WORM/INV-SOFT-002 da
migration 0003 (GRANT concede o opcode; trigger nega). UPDATE de campos
protegidos idem (INV-PAD-006 GUC + WORM).

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS_M5 = (
    "padrao_metrologico",
    "recal_externo_padrao",
    "verificacao_intermediaria",
    "intercomparacao_pt",
    "analise_carta_controle",
    "vinculo_auxiliar",
)


def _grants() -> str:
    return "\n".join(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;"
        for t in TABELAS_M5
    )


def _revokes() -> str:
    return "\n".join(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;"
        for t in TABELAS_M5
    )


SQL_FORWARD = f"""
-- T-PAD-016: GRANT em 6 tabelas M5 para app_user (PROD OWNER=app_migrator).
{_grants()}
"""

SQL_REVERSE = f"""
{_revokes()}
"""


class Migration(migrations.Migration):
    dependencies = [
        ("padroes", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
