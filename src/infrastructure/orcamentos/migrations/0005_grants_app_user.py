"""T-ORC-024b — GRANT app_user nas 7 tabelas (molde precificacao/0005).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explicito, app_user (role da web app, NOBYPASSRLS) nao tem privilege. O GRANT
concede o opcode; a RLS (0002) escopa por tenant e os triggers WORM (0003) +
estado-terminal (0004) negam a mutacao indevida.

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "orcamento",
    "versao_orcamento",
    "item_orcamento",
    "orcamento_link_publico",
    "orcamento_aprovacao",
    "analise_critica_orcamento",
    "template_orcamento",
)

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0004_constraints"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
