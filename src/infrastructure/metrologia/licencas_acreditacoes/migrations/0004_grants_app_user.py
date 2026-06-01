"""T-LIC-020 — GRANT app_user nas 5 tabelas M9 (análogo SEG-CAL-06 / T-ECMC-014).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT explícito,
app_user (role da web app) não tem privilege. Em test funciona porque OWNER=app_user
(memória feedback_test_db_owner_app_user).

DELETE permanece bloqueado em PROD pelos triggers WORM (migration 0003) onde aplicável;
GRANT concede o opcode, trigger nega (defesa em profundidade).

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS_M9 = (
    "documento_regulatorio",
    "revisao_documento",
    "alerta_vencimento",
    "bloqueio_operacional",
    "evento_emergencial_licenca",
)


def _grants() -> str:
    return "\n".join(
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;"
        for t in TABELAS_M9
    )


def _revokes() -> str:
    return "\n".join(
        f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;"
        for t in TABELAS_M9
    )


SQL_FORWARD = f"""
-- T-LIC-020: GRANT em 5 tabelas M9 para app_user (PROD OWNER=app_migrator).
{_grants()}
"""

SQL_REVERSE = f"""
{_revokes()}
"""


class Migration(migrations.Migration):
    dependencies = [
        ("licencas_acreditacoes", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
