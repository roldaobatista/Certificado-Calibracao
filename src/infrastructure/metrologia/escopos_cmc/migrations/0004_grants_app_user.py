"""T-ECMC-014 — GRANT app_user nas 2 tabelas M6 (análogo SEG-CAL-06 / T-PAD-016).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege em INSERT/SELECT/
UPDATE/DELETE. Em test funciona porque OWNER=app_user (memória
feedback_test_db_owner_app_user).

DELETE permanece bloqueado em PROD pelo trigger escopo_cmc_block_delete
(INV-SOFT-002, migration 0003); UPDATE de campo metrológico de CONFIRMADO idem
(escopo_cmc_worm_check). GRANT concede o opcode; trigger nega.

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS_M6 = (
    "escopo_cmc",
    "escopo_extraido",
)


def _grants() -> str:
    return "\n".join(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;"
        for t in TABELAS_M6
    )


def _revokes() -> str:
    return "\n".join(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;"
        for t in TABELAS_M6
    )


SQL_FORWARD = f"""
-- T-ECMC-014: GRANT em 2 tabelas M6 para app_user (PROD OWNER=app_migrator).
{_grants()}
"""

SQL_REVERSE = f"""
{_revokes()}
"""


class Migration(migrations.Migration):
    dependencies = [
        ("escopos_cmc", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
