"""Policies UPDATE/DELETE permissivas em acessos_dados_cliente — trigger barra.

Sem policy UPDATE/DELETE, RLS silenciosamente bloqueia. Queremos que a query
chegue no trigger anti-mutation pra ter mensagem clara de violacao (INV-013).
Mesmo pattern de authz_decisions.
"""

# tests-coverage: tests/test_clientes_us_cli_002_visao360.py

from __future__ import annotations

from django.db import migrations

CREATE_SQL = """
CREATE POLICY acessos_no_update ON acessos_dados_cliente
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

CREATE POLICY acessos_no_delete ON acessos_dados_cliente
    FOR DELETE
    USING (true);
"""

DROP_SQL = """
DROP POLICY IF EXISTS acessos_no_delete ON acessos_dados_cliente;
DROP POLICY IF EXISTS acessos_no_update ON acessos_dados_cliente;
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0005_acessos_constraints_e_trigger")]
    operations = [migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL)]
