"""T-CR-023 — RLS policies pattern v2 (ADR-0002 §6) nas tabelas contas-receber.

Cobertura (INV-TENANT-001/002/003 — idêntico a M3..M9 + fiscal):
- SELECT/UPDATE/DELETE scoped por `app.tenant_ids` (multi-tenant role).
- INSERT scoped por `app.active_tenant_id` (tenant único na sessão).
- ENABLE + FORCE ROW LEVEL SECURITY (roles NOBYPASSRLS — ADR-0002).

Tabelas cobertas: titulo_receber, pagamento_titulo, override_bloqueio.
(parcela_titulo tem tenant_id mas não é agregado raiz com acesso REST direto;
cobrimos mesmo assim para defesa em profundidade.)

NÃO cobre nesta migration (fica em 0003_triggers_worm):
- Campos probatórios imutáveis + block-delete — WORM Padrão B.
- INSERT-only em pagamento_titulo e override_bloqueio.
- Trigger perfil_no_evento fallback COALESCE (R4).

# tests-coverage: tests/test_contas_receber_schema_fatia1b.py
# (cobertura RLS happy + UNHAPPY cross-tenant) + management/commands/validar_contas_receber.py
"""

from __future__ import annotations

from django.db import migrations

_TABELAS_COM_TENANT = [
    "titulo_receber",
    "parcela_titulo",
    "pagamento_titulo",
    "override_bloqueio",
]


def _rls_forward(tabela: str) -> str:
    return f"""
-- =============================================================
-- {tabela} - RLS pattern v2 (ADR-0002 §6)
-- =============================================================
ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;

CREATE POLICY {tabela}_tenant_isolation_select ON {tabela}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_update ON {tabela}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_delete ON {tabela}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {tabela}_tenant_isolation_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""


def _rls_reverse(tabela: str) -> str:
    return f"""
DROP POLICY IF EXISTS {tabela}_tenant_isolation_insert ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_delete ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_update ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_select ON {tabela};
ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;
"""


FORWARD = "\n".join(_rls_forward(t) for t in _TABELAS_COM_TENANT)
REVERSE = "\n".join(_rls_reverse(t) for t in _TABELAS_COM_TENANT)


class Migration(migrations.Migration):
    dependencies = [
        ("contas_receber", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
