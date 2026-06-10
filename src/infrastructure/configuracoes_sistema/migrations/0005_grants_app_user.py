"""T-CFG-025 — GRANT app_user nas 5 tabelas (análogo fiscal 0004 / SEG-CAL-06).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. Em test funciona porque
OWNER=app_user (memória feedback_test_db_owner_app_user).

DELETE de `imposto` permanece bloqueado pelo trigger `imposto_block_delete`
(0003); decremento de série pelo `serie_documento_inv028_check`; DELETE de
número confirmado pelo `numero_doc_reservado_block_delete_confirmado`. GRANT
concede o opcode; trigger nega.

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "empresa",
    "filial",
    "imposto",
    "serie_documento",
    "numero_documento_reservado",
)

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("configuracoes_sistema", "0004_exclusion_imposto"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
