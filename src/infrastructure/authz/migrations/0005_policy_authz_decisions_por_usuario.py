"""FB-C3 — reescreve policy authz_decisions: pré-tenant POR-USUÁRIO.

Regressão FB-C3: a policy 0002 liberava a cadeia pré-tenant (`tenant_id
NULL`) só com `current_setting('app.usuario_id')=''` — proxy frágil de
"sistema". Mas decisão authz pré-tenant autenticada (login, "listar meus
tenants") roda com `app.usuario_id` SETADO → o helper de cadeia não enxergava
o elo anterior → cadeia pré-tenant bifurcava silenciosamente (FB-C1⇄FB-C3
acoplados).

Correção (review tech-lead — design FB-C1+C3 conjunto):
- `modo_sistema='1'` (sinal canônico FA-C1) substitui o proxy `usuario_id=''`
  → worker tenant sem usuário NÃO vê mais pré-tenant alheio.
- Cadeia pré-tenant POR-USUÁRIO: usuário só lê/encadeia as PRÓPRIAS decisões
  pré-tenant (a decisão authz pré-tenant tem dono — ≠ cadeia sistema audit).
- SQL vem do builder ÚNICO `rls_templates.policies_authz_decisions()` (não
  mais inline na migration — regressão #6 da rodada 1).

DROP-then-CREATE idempotente; reverse recria as MESMAS (não regride a
robustez — padrão FA-A2). Trigger PG anti-mutation (0002) INTACTO.

# tests-coverage: tests/test_authz_cadeia_pre_tenant.py tests/test_authz_isolamento.py
"""

from __future__ import annotations

from django.db import migrations

from src.infrastructure.multitenant.rls_templates import (
    policies_authz_decisions,
    reverse_policies_authz_decisions,
)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("authz", "0004_authzdecision_sequencia"),
    ]

    operations = [
        migrations.RunSQL(
            sql=policies_authz_decisions(),
            reverse_sql=reverse_policies_authz_decisions(),
        ),
    ]
