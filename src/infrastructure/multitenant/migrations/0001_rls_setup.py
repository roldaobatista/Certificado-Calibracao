"""Habilita RLS nas tabelas com tenant_id + cria policies v2 (ADR-0002 §6).

Depende de:
- audit.0001_initial (tabela `auditoria`)
- feature_flag.0001_initial (tabela `feature_flags`)
- usuario.0001_initial (tabela `usuario_perfil_tenant`)

NAO aplica RLS em `tenants` nem `usuarios` (SHARED ACROSS TENANTS).
"""

# tests-coverage: tests/test_isolamento_cross_tenant.py

from __future__ import annotations

from django.db import migrations


# =============================================================
# Policy padrao v2 (ADR-0002 §6) — lista de tenants, sem fallback permissivo.
# SET sem o `true` no current_setting() => falha duro se nao setado, em vez
# de vazar.
# =============================================================
RLS_POLICY_TEMPLATE = """
ALTER TABLE {tabela} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {tabela} FORCE ROW LEVEL SECURITY;

-- SELECT/UPDATE/DELETE: linha visivel se tenant_id estiver na lista permitida
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

-- INSERT: sempre grava no active_tenant_id (nao livre — INV-AUTHZ-003)
CREATE POLICY {tabela}_tenant_isolation_insert ON {tabela}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

RLS_POLICY_REVERSE = """
DROP POLICY IF EXISTS {tabela}_tenant_isolation_insert ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_delete ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_update ON {tabela};
DROP POLICY IF EXISTS {tabela}_tenant_isolation_select ON {tabela};
ALTER TABLE {tabela} DISABLE ROW LEVEL SECURITY;
"""


# =============================================================
# Policy especial pra `usuario_perfil_tenant` — usa usuario_id (bootstrap).
# Middleware precisa LER essa tabela ANTES de saber a lista de tenants;
# por isso a policy aqui depende de `app.usuario_id`, nao `app.tenant_ids`.
# =============================================================
USUARIO_PERFIL_POLICY = """
ALTER TABLE usuario_perfil_tenant ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuario_perfil_tenant FORCE ROW LEVEL SECURITY;

-- SELECT: usuario ve apenas seus proprios perfis (bootstrap do middleware)
CREATE POLICY upt_self_select ON usuario_perfil_tenant
    FOR SELECT
    USING (usuario_id::text = current_setting('app.usuario_id'));

-- INSERT/UPDATE/DELETE: so via app_migrator OU via codigo de provisioning
-- explicitamente em `run_as_system()`. Em runtime regular, ninguem altera.
-- Bloqueio dataado de defesa pre-AuthorizationProvider (Marco F-B refina).
CREATE POLICY upt_block_mutation ON usuario_perfil_tenant
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""

USUARIO_PERFIL_POLICY_REVERSE = """
DROP POLICY IF EXISTS upt_block_mutation ON usuario_perfil_tenant;
DROP POLICY IF EXISTS upt_self_select ON usuario_perfil_tenant;
ALTER TABLE usuario_perfil_tenant DISABLE ROW LEVEL SECURITY;
"""


# =============================================================
# Policy especial pra feature_flags — tenant_id pode ser NULL (flag global).
# =============================================================
FEATURE_FLAGS_POLICY = """
ALTER TABLE feature_flags ENABLE ROW LEVEL SECURITY;
ALTER TABLE feature_flags FORCE ROW LEVEL SECURITY;

-- SELECT: flag global (tenant_id NULL) eh sempre visivel; flag por-tenant
-- so se tenant_id estiver na lista permitida.
CREATE POLICY ff_select_global_or_tenant ON feature_flags
    FOR SELECT
    USING (
        tenant_id IS NULL
        OR tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))
    );

-- INSERT/UPDATE/DELETE: so via app_migrator (provisioning de plano) ou via
-- run_as_system. Em runtime regular, ninguem altera feature flag.
CREATE POLICY ff_block_mutation ON feature_flags
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""

FEATURE_FLAGS_POLICY_REVERSE = """
DROP POLICY IF EXISTS ff_block_mutation ON feature_flags;
DROP POLICY IF EXISTS ff_select_global_or_tenant ON feature_flags;
ALTER TABLE feature_flags DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    """RLS policies v2 — defesa em profundidade no nivel do banco."""

    initial = True
    dependencies = [
        ("audit", "0001_initial"),
        ("feature_flag", "0001_initial"),
        ("usuario", "0001_initial"),
    ]

    operations = [
        # Tabela auditoria — policy padrao v2 (tem tenant_id NOT NULL? — sim, mas
        # campo aceita NULL pra eventos globais; usuarios so veem seus tenants
        # mais eventos globais? Decisao Marco 4: eventos globais visiveis so via
        # `run_as_system`. Por enquanto policy padrao bloqueia events com
        # tenant_id NULL pra usuarios normais — comportamento desejado).
        migrations.RunSQL(
            sql=RLS_POLICY_TEMPLATE.format(tabela="auditoria"),
            reverse_sql=RLS_POLICY_REVERSE.format(tabela="auditoria"),
        ),
        # Tabela usuario_perfil_tenant — policy especial baseada em usuario_id
        migrations.RunSQL(
            sql=USUARIO_PERFIL_POLICY,
            reverse_sql=USUARIO_PERFIL_POLICY_REVERSE,
        ),
        # Tabela feature_flags — policy hibrida (NULL global + lista)
        migrations.RunSQL(
            sql=FEATURE_FLAGS_POLICY,
            reverse_sql=FEATURE_FLAGS_POLICY_REVERSE,
        ),
    ]
