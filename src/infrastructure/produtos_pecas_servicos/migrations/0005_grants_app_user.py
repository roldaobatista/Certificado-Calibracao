"""T-PPS-021 — GRANT app_user nas 5 tabelas (molde 0005 da frente #1).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. DELETE de versão/linha
permanece bloqueado pelos triggers 0003 (GRANT concede o opcode; trigger nega).

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "item_catalogo",
    "item_catalogo_versao",
    "kit_composicao",
    "tabela_preco",
    "linha_tabela_preco",
)

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0004_exclusions"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
