"""T-CT-026 — GRANT em todas as tabelas do caixa_tecnico para app_user.

Migrations rodam como app_migrator (DDL). O app Django roda como
app_user (DML). GRANT SELECT/INSERT/UPDATE/DELETE em PROD.

Em test, OWNER=app_user → GRANT não bloqueia; ainda assim declarado
para paridade ambiente (molde contas_receber/0004_grants_app_user).

Nota: DELETE físico é bloqueado pelos triggers de 0003 em PROD;
      em test (OWNER=app_user) o trigger executa normalmente.

# policy-test-coverage: skip -- GRANT apenas, sem CREATE POLICY nova de RLS
"""

from django.db import migrations

_TABELAS = [
    "caixa_tecnico",
    "adiantamento_caixa",
    "despesa_caixa",
    "prestacao_contas_caixa",
    "politica_caixa",
    "consentimento_gps_colaborador",
]

_SQL_GRANTS = "\n".join(
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {t} TO app_user;" for t in _TABELAS
)

_SQL_REVOKE = "\n".join(
    f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {t} FROM app_user;" for t in _TABELAS
)


class Migration(migrations.Migration):
    dependencies = [
        ("caixa_tecnico", "0004_constraints"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_SQL_GRANTS,
            reverse_sql=_SQL_REVOKE,
        ),
    ]
