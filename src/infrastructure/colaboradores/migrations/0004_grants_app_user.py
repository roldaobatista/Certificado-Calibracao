"""T-COL-024 — GRANT app_user nas tabelas do módulo colaboradores.

Em PROD, migrations rodam como app_migrator (OWNER=app_migrator). Sem GRANT
explícito, app_user (role da web app) não tem privilege.

Política por tabela:
  - colaborador, colaborador_papel, colaborador_habilidade, colaborador_documento:
      SELECT, INSERT, UPDATE, DELETE — tabelas-tenant com RLS guarda isolamento.
  - catalogo_habilidade: SELECT apenas — tabela global read-only;
      INSERT exclusivo via migration de seed (0006_seed_catalogo_habilidade).

# rls-policy: external 0002_rls_policies (GRANT puro — não cria tabela)
# audit-immutability: skip -- GRANT puro não toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

TABELAS_TENANT = (
    "colaborador",
    "colaborador_papel",
    "colaborador_habilidade",
    "colaborador_documento",
)

# SQL fixo com literais de nome de tabela (sem input externo — S608 falso positivo de análise estática).
SQL_FORWARD = """
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_papel TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_habilidade TO app_user;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_documento TO app_user;
GRANT SELECT ON TABLE catalogo_habilidade TO app_user;
"""

SQL_REVERSE = """
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador FROM app_user;
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_papel FROM app_user;
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_habilidade FROM app_user;
REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE colaborador_documento FROM app_user;
REVOKE SELECT ON TABLE catalogo_habilidade FROM app_user;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("colaboradores", "0003_trigger_defensivo"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
