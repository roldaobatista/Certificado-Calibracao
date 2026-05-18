"""Refinamento de `usuario_perfil_tenant` — permite INSERT system.

Mesma logica do refinamento de feature_flags (migration 0002): em `run_as_system`
(tenant_ids vazio) eh legitimo criar perfil novo (admin operation, futuro
management command). Sem isso, factories de teste e fluxos de provisioning
ficam travados.

UPDATE/DELETE continuam bloqueados — perfis se invalidam via valido_ate, nunca
sao apagados.
"""

# tests-coverage: tests/test_isolamento_cross_tenant.py, tests/test_middleware_e2e.py

from __future__ import annotations

from django.db import migrations


REFINA_UPT = """
DROP POLICY IF EXISTS upt_block_mutation ON usuario_perfil_tenant;

-- INSERT: permitido se rodando como system (admin/provisioning)
CREATE POLICY upt_insert_system ON usuario_perfil_tenant
    FOR INSERT
    WITH CHECK (current_setting('app.tenant_ids') = '');

-- UPDATE bloqueado (invalida via valido_ate, nao UPDATE)
CREATE POLICY upt_block_update ON usuario_perfil_tenant FOR UPDATE USING (false);

-- DELETE bloqueado
CREATE POLICY upt_block_delete ON usuario_perfil_tenant FOR DELETE USING (false);
"""

REVERSE_UPT = """
DROP POLICY IF EXISTS upt_block_delete ON usuario_perfil_tenant;
DROP POLICY IF EXISTS upt_block_update ON usuario_perfil_tenant;
DROP POLICY IF EXISTS upt_insert_system ON usuario_perfil_tenant;

CREATE POLICY upt_block_mutation ON usuario_perfil_tenant
    FOR ALL
    USING (false)
    WITH CHECK (false);
"""


class Migration(migrations.Migration):

    dependencies = [
        ("multitenant", "0002_fail_loud_e_flag_global"),
    ]

    operations = [
        migrations.RunSQL(sql=REFINA_UPT, reverse_sql=REVERSE_UPT),
    ]
