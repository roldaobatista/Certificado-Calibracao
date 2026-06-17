"""T-AGE-026 — GRANT app_user nas tabelas agenda (análogo contas_receber/0004).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. Em test funciona porque
OWNER=app_user (memória feedback_test_db_owner_app_user).

Tabelas INSERT-only (registro_no_show, evento_auditoria_agenda,
regime_jornada_colaborador): triggers 0004 negam UPDATE/DELETE em prod.
Concedemos SELECT, INSERT, UPDATE, DELETE para manter simetria com o padrão
do projeto (trigger nega UPDATE/DELETE; em test OWNER=app_user supre).

# rls-policy: external 0002_rls_policies (GRANT puro — não cria tabela)
# audit-immutability: skip -- GRANT puro não toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

_TABELAS = [
    "evento_agenda",
    "recorrencia_agenda",
    "registro_no_show",
    "capacidade_tecnico",
    "feriado",
    "evento_auditoria_agenda",
    "regime_jornada_colaborador",
]

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in _TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in _TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0004_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
