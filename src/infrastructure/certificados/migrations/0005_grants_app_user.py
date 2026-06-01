"""T-CER-024 — GRANT app_user nas 2 tabelas novas da reconciliação (análogo M7 0004).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT explícito,
app_user (role da web app) não tem privilege. Em test funciona porque OWNER=app_user
(memória feedback_test_db_owner_app_user). DELETE/UPDATE permanecem bloqueados pelos
triggers WORM da 0004 (GRANT concede o opcode; trigger nega).

# rls-policy: external 0003_rls_reconciliacao (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = ("ponto_reconciliado", "analise_reconciliacao_cert")

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)
SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("certificados", "0004_triggers_worm_reconciliacao"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
