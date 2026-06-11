"""T-PPS-041 — GRANT app_user nas 2 tabelas de staging (molde 0005).

DELETE é legítimo aqui (TTL 90d elimina lotes antigos — ADV-PPS-06); staging
não tem trigger WORM.

# rls-policy: external 0008_rls_staging (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "importacao_catalogo",
    "importacao_catalogo_linha",
)

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0008_rls_staging"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
