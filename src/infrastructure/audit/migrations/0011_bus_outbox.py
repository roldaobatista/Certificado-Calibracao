"""T-CLI-107 — tabela `bus_outbox` (outbox transacional) + RLS + CHECKs.

Padrao outbox transacional cravado em P2 do Marco 1 `clientes`:
INSERT acontece no mesmo `transaction.atomic` do caller, junto com a
gravacao da cadeia hash F-A. Worker drena via FOR UPDATE SKIP LOCKED.

Garantias do banco (defesa em profundidade — chamador NAO pode violar):
- UNIQUE (causation_id, acao): idempotencia.
- CHECK acao: enum semantico em formato slug `dominio.entidade.op[.var]`.
  Bloqueia PII na coluna `acao` (BLOQ-A1 advogado).
- CHECK envelope < 64 KiB: bloqueia disco-cheio (MED-2 tech-lead).
- RLS ENABLE + FORCE com predicate IDENTICO ao de `Auditoria`
  (`multitenant/0004`): BLOQ-A tech-lead.

# tests-coverage: tests/test_bus_outbox_t_cli_107.py
# tests-coverage: tests/test_outbox_worker_t_cli_110.py
# rls-policy: external 0011  -- a policy nasce nesta MESMA migration
"""

from __future__ import annotations

from django.db import migrations, models

# =============================================================
# FORWARD
# =============================================================
FORWARD = """
-- =====================================
-- Constraints adicionais a CreateModel
-- =====================================
ALTER TABLE bus_outbox ADD CONSTRAINT bus_outbox_acao_enum_semantico
    CHECK (
        acao ~ '^[a-z][a-z0-9_]{0,40}(\\.[a-z][a-z0-9_]{0,40}){1,3}$'
        AND length(acao) <= 100
    );

ALTER TABLE bus_outbox ADD CONSTRAINT bus_outbox_envelope_limite_64kb
    CHECK (pg_column_size(envelope_jsonb) < 65536);

-- =====================================
-- RLS — DIVERGENCIA JUSTIFICADA do BLOQ-A tech-lead.
-- # tests-coverage: tests/test_bus_outbox_t_cli_107.py
-- # tests-coverage: tests/test_outbox_worker_t_cli_110.py
--
-- Auditoria (`auditoria_chain_select`) restringe modo_sistema a
-- `tenant_id IS NULL`. Outbox precisa cross-tenant SELECT/UPDATE em
-- modo_sistema pra worker drenar (galinha-e-ovo: nao da pra entrar
-- no contexto sem antes saber o tenant). Trade-off aceito: wrapper
-- unico `run_as_system` + app_user NOBYPASSRLS.
-- =====================================
ALTER TABLE bus_outbox ENABLE ROW LEVEL SECURITY;
ALTER TABLE bus_outbox FORCE ROW LEVEL SECURITY;

CREATE POLICY bus_outbox_tenant_isolation_select ON bus_outbox
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

CREATE POLICY bus_outbox_tenant_isolation_insert ON bus_outbox
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1' AND tenant_id IS NULL)
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );

-- UPDATE: modo_sistema vê tudo (tx-1/tx-2/tx-3 do worker); contexto
-- tenant só vê próprias linhas.
CREATE POLICY bus_outbox_tenant_isolation_update ON bus_outbox
    FOR UPDATE
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    )
    WITH CHECK (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    );

-- DELETE: APENAS modo_sistema (cleanup job — MED-1 tech-lead).
CREATE POLICY bus_outbox_tenant_isolation_delete ON bus_outbox
    FOR DELETE
    USING (current_setting('app.modo_sistema', true) = '1');
"""

REVERSE = """
DROP POLICY IF EXISTS bus_outbox_tenant_isolation_delete ON bus_outbox;
DROP POLICY IF EXISTS bus_outbox_tenant_isolation_update ON bus_outbox;
DROP POLICY IF EXISTS bus_outbox_tenant_isolation_insert ON bus_outbox;
DROP POLICY IF EXISTS bus_outbox_tenant_isolation_select ON bus_outbox;
ALTER TABLE bus_outbox DISABLE ROW LEVEL SECURITY;
ALTER TABLE bus_outbox DROP CONSTRAINT IF EXISTS bus_outbox_envelope_limite_64kb;
ALTER TABLE bus_outbox DROP CONSTRAINT IF EXISTS bus_outbox_acao_enum_semantico;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0010_acessos_ip_hash_textfield"),
        ("multitenant", "0004_audit_hash_chain_por_tenant"),  # require_tenant_ctx()
    ]

    operations = [
        migrations.CreateModel(
            name="BusOutbox",
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
                (
                    "causation_id",
                    models.UUIDField(
                        help_text="UUID que liga o evento a request/comando "
                        "original. Chave de idempotencia.",
                    ),
                ),
                (
                    "acao",
                    models.CharField(
                        help_text="Enum semantico (slug). CHECK constraint " "anti-PII no banco.",
                        max_length=100,
                    ),
                ),
                (
                    "envelope_jsonb",
                    models.JSONField(
                        help_text="Envelope completo sanitizado em escrita. "
                        "CHECK pg_column_size < 64 KiB.",
                    ),
                ),
                (
                    "tenant_id",
                    models.UUIDField(
                        blank=True,
                        db_index=True,
                        help_text="NULL = evento sistema (provisioning, " "manutencao).",
                        null=True,
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "processado_em",
                    models.DateTimeField(
                        blank=True,
                        help_text="NULL = pendente; preenchido pelo worker " "apos dispatch OK.",
                        null=True,
                    ),
                ),
                (
                    "tentativas",
                    models.SmallIntegerField(
                        default=0,
                        help_text="Incrementado em Tx-1 antes do dispatch "
                        "(sobrevive a crash). tentativas >= 5 vira poison "
                        "message — listar_outbox_envenenado mostra.",
                    ),
                ),
                (
                    "ultimo_erro",
                    models.TextField(
                        blank=True,
                        help_text="Sanitizado + truncado 500c por "
                        "sanitizar_erro_para_outbox (BLOQ-A4).",
                        null=True,
                    ),
                ),
            ],
            options={
                "verbose_name": "Linha do outbox (T-CLI-107)",
                "verbose_name_plural": "Bus outbox (fila intermediaria)",
                "db_table": "bus_outbox",
                "ordering": ["criado_em"],
            },
        ),
        migrations.AddConstraint(
            model_name="busoutbox",
            constraint=models.UniqueConstraint(
                fields=("causation_id", "acao"), name="bus_outbox_idempotencia"
            ),
        ),
        migrations.AddIndex(
            model_name="busoutbox",
            index=models.Index(
                fields=["processado_em", "tentativas", "criado_em"],
                name="ix_bus_outbox_drenar",
            ),
        ),
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
