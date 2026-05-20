"""T-CLI-104 — tabela `breaker_acesso_pii_evento` (circuit breaker observado).

Cada chamada de `registrar_acesso_dados_cliente_com_breaker` grava UM
evento aqui (ok=True OU ok=False), via conexao paralela autocommit
`breaker_writer` — sobrevive ao rollback do request HTTP quando a
gravacao principal falha (fail-loud preservado).

Sliding window 5min + threshold OR `(pct >= 0.1% AND total >= 1000)
OR (falhas_absolutas >= 3)` avaliada pelo management command
`avaliar_circuit_breaker_acesso_pii` (Wave A pluga em cron).

Retencao: 7 dias (matriz §2). Cleanup job Wave A.

# tests-coverage: tests/test_breaker_acesso_pii_t_cli_104.py
# rls-policy: external 0012
"""

from __future__ import annotations

from django.db import migrations, models

FORWARD = """
-- =====================================
-- RLS — divergencia justificada (igual ao bus_outbox):
-- modo_sistema vê tudo pra command avaliar cross-tenant.
-- # tests-coverage: tests/test_breaker_acesso_pii_t_cli_104.py
-- =====================================
ALTER TABLE breaker_acesso_pii_evento ENABLE ROW LEVEL SECURITY;
ALTER TABLE breaker_acesso_pii_evento FORCE ROW LEVEL SECURITY;

CREATE POLICY breaker_acesso_pii_select ON breaker_acesso_pii_evento
    FOR SELECT
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    );

CREATE POLICY breaker_acesso_pii_insert ON breaker_acesso_pii_evento
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1')
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );

-- DELETE so em modo_sistema (cleanup job futuro)
CREATE POLICY breaker_acesso_pii_delete ON breaker_acesso_pii_evento
    FOR DELETE
    USING (current_setting('app.modo_sistema', true) = '1');
"""

REVERSE = """
DROP POLICY IF EXISTS breaker_acesso_pii_delete ON breaker_acesso_pii_evento;
DROP POLICY IF EXISTS breaker_acesso_pii_insert ON breaker_acesso_pii_evento;
DROP POLICY IF EXISTS breaker_acesso_pii_select ON breaker_acesso_pii_evento;
ALTER TABLE breaker_acesso_pii_evento DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0011_bus_outbox"),
        ("multitenant", "0004_audit_hash_chain_por_tenant"),
    ]

    operations = [
        migrations.CreateModel(
            name="BreakerAcessoPIIEvento",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=__import__("uuid").uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("ts", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("ok", models.BooleanField()),
            ],
            options={
                "db_table": "breaker_acesso_pii_evento",
                "verbose_name": "Evento do breaker AcessoDadosCliente (T-CLI-104)",
                "verbose_name_plural": "Eventos do breaker AcessoDadosCliente",
                "ordering": ["-ts"],
            },
        ),
        migrations.AddIndex(
            model_name="breakeracessopiievento",
            index=models.Index(
                fields=["tenant_id", "-ts"],
                name="ix_breaker_acesso_pii_t_ts",
            ),
        ),
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
