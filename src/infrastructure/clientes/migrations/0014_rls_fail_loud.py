"""FA-A2 — regenera policies RLS de `clientes` com fail-loud.

`clientes/0002` nasceu com `current_setting('app.tenant_ids')` CRU: em
contexto vazio devolve `''` → policy "vê 0 linhas" SILENCIOSA em vez de
RAISE (furo de robustez — ADR-0002 §6). Esta migration troca SELECT/UPDATE/
DELETE de `clientes` para `require_tenant_ctx()` (RAISE 42501 se contexto
vazio), via o template único `multitenant/rls_templates.py`. INSERT mantém
`active_tenant_id::uuid` (fail-loud via 22P02; precedente multitenant/0002).

reverse NÃO volta ao cru (R2 review tech-lead): recria ainda fail-loud — só
não regride robustez num caminho que testes forward-only não exercitam.

# rls-policy: external 0002_rls_policies
# tests-coverage: tests/test_clientes_rls_fail_loud.py
"""

from __future__ import annotations

from django.db import migrations

from src.infrastructure.multitenant.rls_templates import (
    policies_isolamento_tenant,
    reverse_policies_isolamento_tenant,
)


class Migration(migrations.Migration):
    # Dependência DUPLA explícita (R5 review tech-lead): além da última de
    # clientes, depende de multitenant/0002 que cria require_tenant_ctx().
    # Sem isso, migrate from-scratch pode aplicar esta antes → function
    # require_tenant_ctx() does not exist.
    dependencies = [
        ("clientes", "0013_seed_authz_importar"),
        ("multitenant", "0002_fail_loud_e_flag_global"),
    ]

    operations = [
        migrations.RunSQL(
            sql=policies_isolamento_tenant("clientes"),
            reverse_sql=reverse_policies_isolamento_tenant("clientes"),
        ),
    ]
