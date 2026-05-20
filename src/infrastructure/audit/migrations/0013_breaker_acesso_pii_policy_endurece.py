"""T-CLI-104 — endurece policy INSERT do `breaker_acesso_pii_evento`.

Auditor SEGURANÇA FAIL 1 (2026-05-20): a policy INSERT permitia
qualquer `tenant_id` sob `modo_sistema='1'`. Wrapper aceitava
`tenant_id` como argumento Python sem validar contra o contexto
ativo — qualquer caller forjaria evento atribuido a tenant alheio.

Correção: WITH CHECK exige SEMPRE `tenant_id = app.active_tenant_id`
(sem ramo permissivo "modo_sistema -> qualquer tenant_id"). O wrapper
seta `app.active_tenant_id` via SET LOCAL na transação explícita —
ver `breaker.py::_gravar_evento_breaker`.

# tests-coverage: tests/test_breaker_acesso_pii_t_cli_104.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- # tests-coverage: tests/test_breaker_acesso_pii_t_cli_104.py
DROP POLICY IF EXISTS breaker_acesso_pii_insert ON breaker_acesso_pii_evento;

CREATE POLICY breaker_acesso_pii_insert ON breaker_acesso_pii_evento
    FOR INSERT
    WITH CHECK (
        tenant_id::text = current_setting('app.active_tenant_id')
    );
"""

REVERSE = """
DROP POLICY IF EXISTS breaker_acesso_pii_insert ON breaker_acesso_pii_evento;

CREATE POLICY breaker_acesso_pii_insert ON breaker_acesso_pii_evento
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1')
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0012_breaker_acesso_pii_evento"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
