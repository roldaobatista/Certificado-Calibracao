"""T-CT-025 — Constraints parciais do caixa_tecnico.

2 constraints parciais em despesa_caixa:

(1) UNIQUE(tenant_id, foto_hash) WHERE estado NOT IN ('rejeitada', 'cancelada')
    Anti-duplicata de foto por tenant nos estados ativos (INV-CT-FOTO-DEDUP-001 / D-CT-4).
    tenant_id como 1ª coluna (plano de execução por tenant — plan R12).
    Fotos idênticas em tenants diferentes coexistem (constraint é por tenant).

(2) UNIQUE(tenant_id, client_offline_id) WHERE client_offline_id <> ''
    Idempotência offline: replay não duplica (D-CT-5 / INV-CT-OFFLINE-001).
    tenant_id como 1ª coluna; exclui '' (não-offline).

Molde: contas_receber/0004_constraints (UNIQUE parcial com tenant_id 1ª coluna).
"""

from django.db import migrations

_SQL_CONSTRAINTS = """
-- (1) Anti-duplicata de foto por tenant nos estados ativos
CREATE UNIQUE INDEX uq_ct_despesa_foto_hash_ativa
    ON despesa_caixa (tenant_id, foto_hash)
    WHERE estado NOT IN ('rejeitada', 'cancelada');

-- (2) Idempotência offline por tenant
CREATE UNIQUE INDEX uq_ct_despesa_offline_id
    ON despesa_caixa (tenant_id, client_offline_id)
    WHERE client_offline_id <> '';
"""

_SQL_CONSTRAINTS_REVERSO = """
DROP INDEX IF EXISTS uq_ct_despesa_foto_hash_ativa;
DROP INDEX IF EXISTS uq_ct_despesa_offline_id;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("caixa_tecnico", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_SQL_CONSTRAINTS,
            reverse_sql=_SQL_CONSTRAINTS_REVERSO,
        ),
    ]
