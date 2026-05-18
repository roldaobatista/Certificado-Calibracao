"""UNIQUE INDEX parcial em clientes(tenant_id, tipo_pessoa, documento) WHERE deletado_em IS NULL.

R4 advogado US-CLI-005: Django UniqueConstraint nao suporta WHERE parcial nativo.
Sem isso, dedup INV-024 quebraria depois do soft-delete (qs default filtra
deletado, dedup nao ve perdedor, duplicata silenciosa).
"""

# rls-policy: external none -- esta migration NAO cria tabela com tenant_id; so adiciona INDEX
# tests-coverage: tests/test_clientes_us_cli_005_dedup.py

from __future__ import annotations

from django.db import migrations


CREATE_SQL = """
CREATE UNIQUE INDEX uq_cliente_doc_ativo
    ON clientes (tenant_id, tipo_pessoa, documento)
    WHERE deletado_em IS NULL;
"""

DROP_SQL = """
DROP INDEX IF EXISTS uq_cliente_doc_ativo;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0005_soft_delete"),
    ]
    operations = [
        migrations.RunSQL(sql=CREATE_SQL, reverse_sql=DROP_SQL),
    ]
