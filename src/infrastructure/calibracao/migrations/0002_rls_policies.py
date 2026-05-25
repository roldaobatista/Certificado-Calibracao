"""T-CAL-002 - RLS policies pattern v2 (ADR-0002 §6).

Cobertura:
- INV-TENANT-001/002/003: SELECT/UPDATE/DELETE/INSERT scoped por tenant
  via `app.tenant_ids` (multi-tenant role) + `app.active_tenant_id`
  (INSERT — tenant unico na sessao). Padrao identico ao M3.

NAO cobre nesta migration (ficam em T-CAL-003+):
- numero_exibido populado via trigger BEFORE INSERT (PG nao aceita
  GENERATED STORED com EXTRACT — STABLE not IMMUTABLE; ano calculado
  na hora do insert basta para o caso de uso). T-CAL-003.
- Trigger anti-mutation pos `aprovada` (INV-CAL-WORM-001) — T-CAL-003.
- UNIQUE composto leitura + padrao_usado (ADR-0065 + INV-CAL-CONC-001/002)
  — entram nas migrations das entidades Leitura/PadraoUsado.
- CHECK constraint composta analise_critica_pedido (recepcao avulsa
  XOR atividade_os_id) — T-CAL-007 (depois que entidades base ficarem).

# tests-coverage: tests/regressao/test_inv_cal_rls_calibracao.py (T-CAL-145)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- calibracao - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE calibracao ENABLE ROW LEVEL SECURITY;
ALTER TABLE calibracao FORCE ROW LEVEL SECURITY;

CREATE POLICY calibracao_tenant_isolation_select ON calibracao
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY calibracao_tenant_isolation_update ON calibracao
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY calibracao_tenant_isolation_delete ON calibracao
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY calibracao_tenant_isolation_insert ON calibracao
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

REVERSE = """
DROP POLICY IF EXISTS calibracao_tenant_isolation_insert ON calibracao;
DROP POLICY IF EXISTS calibracao_tenant_isolation_delete ON calibracao;
DROP POLICY IF EXISTS calibracao_tenant_isolation_update ON calibracao;
DROP POLICY IF EXISTS calibracao_tenant_isolation_select ON calibracao;
ALTER TABLE calibracao DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("calibracao", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
