"""RLS policies pras tabelas authz_* + trigger anti-mutation no authz_decisions.

- `authz_perfil`: SELECT permite tenant_id NULL (catálogo global) OU tenant na
  lista; mutação bloqueada (catálogo gerenciado por migration/admin).
- `authz_perfil_acao`: tabela child sem tenant_id direto; herda conceitualmente
  do Perfil pai. Mutação bloqueada em runtime.
- `authz_decisions`: SELECT permite tenant_id NULL (sistema) OU tenant na lista;
  INSERT exige active_tenant batendo (ou NULL pra decisões pré-tenant). Trigger
  PG `authz_anti_update`/`authz_anti_delete` bloqueia UPDATE/DELETE — INV-AUTHZ-002.
"""

# tests-coverage: tests/test_authz_isolamento.py tests/test_authz_audit_imutavel.py

from __future__ import annotations

from django.db import migrations

AUTHZ_PERFIL_POLICY = """
ALTER TABLE authz_perfil ENABLE ROW LEVEL SECURITY;
ALTER TABLE authz_perfil FORCE ROW LEVEL SECURITY;

-- SELECT: catálogo global (tenant_id NULL) sempre visível; específico só na lista
CREATE POLICY authz_perfil_select ON authz_perfil
    FOR SELECT
    USING (
        tenant_id IS NULL
        OR tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))
    );

-- INSERT/UPDATE/DELETE: bloqueio em runtime; só via migration / run_as_system
CREATE POLICY authz_perfil_block_mutation ON authz_perfil
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""

AUTHZ_PERFIL_POLICY_REVERSE = """
DROP POLICY IF EXISTS authz_perfil_block_mutation ON authz_perfil;
DROP POLICY IF EXISTS authz_perfil_select ON authz_perfil;
ALTER TABLE authz_perfil DISABLE ROW LEVEL SECURITY;
"""

# tests-coverage: tests/test_authz_isolamento.py
AUTHZ_PERFIL_ACAO_POLICY = """
ALTER TABLE authz_perfil_acao ENABLE ROW LEVEL SECURITY;
ALTER TABLE authz_perfil_acao FORCE ROW LEVEL SECURITY;

-- SELECT livre — matriz é catálogo global lido por todos.
-- INV-AUTHZ-004 (preventiva, criada 2026-05-18): vazamento zero ENQUANTO todos os
-- perfis tem tenant_id NULL. Quando Wave A criar primeiro perfil tenant-specific,
-- regerar esta policy pra filtrar via EXISTS no perfil pai (ver REGRAS-INEGOCIAVEIS).
CREATE POLICY authz_perfil_acao_select ON authz_perfil_acao
    FOR SELECT
    USING (true);

-- INSERT/UPDATE/DELETE: bloqueio em runtime
CREATE POLICY authz_perfil_acao_block_mutation ON authz_perfil_acao
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""

AUTHZ_PERFIL_ACAO_POLICY_REVERSE = """
DROP POLICY IF EXISTS authz_perfil_acao_block_mutation ON authz_perfil_acao;
DROP POLICY IF EXISTS authz_perfil_acao_select ON authz_perfil_acao;
ALTER TABLE authz_perfil_acao DISABLE ROW LEVEL SECURITY;
"""

AUTHZ_DECISIONS_POLICY = """
ALTER TABLE authz_decisions ENABLE ROW LEVEL SECURITY;
ALTER TABLE authz_decisions FORCE ROW LEVEL SECURITY;

-- SELECT: evento pré-tenant (tenant_id NULL) visível só em run_as_system;
-- evento de tenant visível se tenant na lista
CREATE POLICY authz_decisions_select ON authz_decisions
    FOR SELECT
    USING (
        (tenant_id IS NULL AND current_setting('app.usuario_id', true) = '')
        OR tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ','))
    );

-- INSERT: tenant_id pode ser NULL (decisão pré-tenant ex.: login) OU bater active_tenant
CREATE POLICY authz_decisions_insert ON authz_decisions
    FOR INSERT
    WITH CHECK (
        tenant_id IS NULL
        OR tenant_id = NULLIF(current_setting('app.active_tenant_id', true), '')::uuid
    );

-- UPDATE/DELETE: trigger bloqueia abaixo; deixamos policy permissiva pra trigger ser quem fala (mensagem melhor)
CREATE POLICY authz_decisions_no_update ON authz_decisions
    FOR UPDATE
    USING (true)
    WITH CHECK (true);

CREATE POLICY authz_decisions_no_delete ON authz_decisions
    FOR DELETE
    USING (true);
"""

AUTHZ_DECISIONS_POLICY_REVERSE = """
DROP POLICY IF EXISTS authz_decisions_no_delete ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_no_update ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_insert ON authz_decisions;
DROP POLICY IF EXISTS authz_decisions_select ON authz_decisions;
ALTER TABLE authz_decisions DISABLE ROW LEVEL SECURITY;
"""

TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION authz_decisions_bloqueia_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'authz_decisions e INSERT-only (INV-AUTHZ-002). % bloqueado em trigger PG.',
        TG_OP
    USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER authz_decisions_anti_update
    BEFORE UPDATE ON authz_decisions
    FOR EACH ROW EXECUTE FUNCTION authz_decisions_bloqueia_mutation();

CREATE TRIGGER authz_decisions_anti_delete
    BEFORE DELETE ON authz_decisions
    FOR EACH ROW EXECUTE FUNCTION authz_decisions_bloqueia_mutation();
"""

TRIGGER_REVERSE_SQL = """
DROP TRIGGER IF EXISTS authz_decisions_anti_delete ON authz_decisions;
DROP TRIGGER IF EXISTS authz_decisions_anti_update ON authz_decisions;
DROP FUNCTION IF EXISTS authz_decisions_bloqueia_mutation();
"""


class Migration(migrations.Migration):
    """RLS + trigger anti-mutation pras 3 tabelas authz."""

    dependencies = [
        ("authz", "0001_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=AUTHZ_PERFIL_POLICY,
            reverse_sql=AUTHZ_PERFIL_POLICY_REVERSE,
        ),
        migrations.RunSQL(
            sql=AUTHZ_PERFIL_ACAO_POLICY,
            reverse_sql=AUTHZ_PERFIL_ACAO_POLICY_REVERSE,
        ),
        migrations.RunSQL(
            sql=AUTHZ_DECISIONS_POLICY,
            reverse_sql=AUTHZ_DECISIONS_POLICY_REVERSE,
        ),
        migrations.RunSQL(
            sql=TRIGGER_SQL,
            reverse_sql=TRIGGER_REVERSE_SQL,
        ),
    ]
