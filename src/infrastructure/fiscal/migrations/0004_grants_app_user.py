"""T-FIS-020 — GRANT app_user na tabela fiscal (análogo M6 0004 / SEG-CAL-06).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. Em test funciona porque
OWNER=app_user (memória feedback_test_db_owner_app_user).

DELETE permanece bloqueado em PROD pelo trigger `nota_fiscal_servico_block_delete`
(INV-FIS-008, 0003); UPDATE de campo probatório idem (`..._worm_check`). GRANT
concede o opcode; trigger nega.

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELA = "nota_fiscal_servico"

SQL_FORWARD = f"""
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {TABELA} TO app_user;
"""

SQL_REVERSE = f"""
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {TABELA} FROM app_user;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
