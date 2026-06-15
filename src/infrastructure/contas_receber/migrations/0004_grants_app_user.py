"""T-CR-025 — GRANT app_user nas tabelas contas-receber (análogo fiscal 0004 / SEG-CAL-06).

Em PROD migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege. Em test funciona porque
OWNER=app_user (memória feedback_test_db_owner_app_user).

DELETE permanece bloqueado em PROD pelo trigger `titulo_receber_block_delete`
(0003); UPDATE de campo probatório idem (`..._worm_check`). GRANT concede o
opcode; trigger nega.

`pagamento_titulo` e `override_bloqueio`: apenas INSERT (UPDATE/DELETE bloqueados
pelos triggers block-update/delete do 0003 — INSERT-only puro). Concedemos
SELECT, INSERT, UPDATE, DELETE para manter simetria com o padrão do projeto
(trigger nega UPDATE/DELETE em prod; em test OWNER=app_user supre).

# rls-policy: external 0002_rls_policies (GRANT puro — nao cria tabela)
# audit-immutability: skip -- GRANT puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

_TABELAS = [
    "titulo_receber",
    "parcela_titulo",
    "pagamento_titulo",
    "override_bloqueio",
]

SQL_FORWARD = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in _TABELAS
)

SQL_REVERSE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in _TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("contas_receber", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
