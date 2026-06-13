"""T-PRC-025 — GRANT app_user nas 7 tabelas (molde 0005 da frente #2).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. DELETE de regra
permanece bloqueado pelos triggers 0003 (GRANT concede o opcode; trigger nega).

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS = (
    "regra_formacao_preco",
    "perfil_composicao_preco",
    "faixa_aprovacao_desconto",
    "pedido_aprovacao_desconto",
    "justificativa_decisao_desconto",
    "vinculo_tabela_preco_cliente",
    "parametros_precificacao_tenant",
)

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("precificacao", "0004_exclusions"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
