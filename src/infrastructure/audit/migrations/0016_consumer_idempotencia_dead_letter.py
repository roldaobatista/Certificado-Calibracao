"""ADR-0033 aceito — `consumer_idempotencia` + `dead_letter_events`.

Destrava Marco 3 Fase 4 (T-OS-029..039). Schema canonico cravado em
ADR-0033; INVs INV-BUS-001/002/003 ja em REGRAS-INEGOCIAVEIS.md.

Constraints SQL adicionais (post CreateModel):
- `consumer_idempotencia.consumer_id` regex slug (anti-PII).
- `consumer_idempotencia.resultado` CHECK enum.
- `dead_letter_events.consumer_id` regex slug.
- `dead_letter_events.tentativas` CHECK >= 1.

RLS:
- `consumer_idempotencia` — INSERT/SELECT modo_sistema OR tenant_id ativo;
  UPDATE/DELETE modo_sistema only (TTL job).
- `dead_letter_events` — SELECT cross-modo; INSERT modo_sistema only
  (worker grava); UPDATE modo_sistema only (painel admin Wave A); DELETE NUNCA.

Trigger anti-mutation `dle_anti_mutation_imutaveis` materializa INV-BUS-003.

# tests-coverage: tests/test_consumer_idempotencia_t_bus_001.py (Wave A)
# tests-coverage: tests/test_dead_letter_events_t_bus_002.py (Wave A)
# rls-policy: external 0016 -- policy nasce nesta mesma migration
"""

import uuid

from django.db import migrations, models

FORWARD_CONSTRAINTS_AND_RLS = r"""
ALTER TABLE consumer_idempotencia ADD CONSTRAINT consumer_idemp_id_slug
    CHECK (
        consumer_id ~ '^[a-z][a-z0-9_]{0,40}(\.[a-z][a-z0-9_]{0,40}){0,3}$'
        AND length(consumer_id) <= 120
    );

ALTER TABLE consumer_idempotencia ADD CONSTRAINT consumer_idemp_resultado_enum
    CHECK (resultado IN ('ok','skip','erro_rastreado'));

ALTER TABLE consumer_idempotencia ENABLE ROW LEVEL SECURITY;
ALTER TABLE consumer_idempotencia FORCE ROW LEVEL SECURITY;

CREATE POLICY consumer_idemp_select ON consumer_idempotencia
    FOR SELECT
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            WHEN tenant_id IS NULL
                THEN FALSE
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    );

CREATE POLICY consumer_idemp_insert ON consumer_idempotencia
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1' AND tenant_id IS NULL)
        OR
        (tenant_id IS NOT NULL AND tenant_id::text = current_setting('app.active_tenant_id'))
    );

CREATE POLICY consumer_idemp_update ON consumer_idempotencia
    FOR UPDATE
    USING (current_setting('app.modo_sistema', true) = '1')
    WITH CHECK (current_setting('app.modo_sistema', true) = '1');

CREATE POLICY consumer_idemp_delete ON consumer_idempotencia
    FOR DELETE
    USING (current_setting('app.modo_sistema', true) = '1');

ALTER TABLE dead_letter_events ADD CONSTRAINT dle_consumer_id_slug
    CHECK (
        consumer_id ~ '^[a-z][a-z0-9_]{0,40}(\.[a-z][a-z0-9_]{0,40}){0,3}$'
        AND length(consumer_id) <= 120
    );

ALTER TABLE dead_letter_events ADD CONSTRAINT dle_tentativas_min
    CHECK (tentativas >= 1);

ALTER TABLE dead_letter_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE dead_letter_events FORCE ROW LEVEL SECURITY;

CREATE POLICY dle_select ON dead_letter_events
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

CREATE POLICY dle_insert ON dead_letter_events
    FOR INSERT
    WITH CHECK (current_setting('app.modo_sistema', true) = '1');

CREATE POLICY dle_update ON dead_letter_events
    FOR UPDATE
    USING (current_setting('app.modo_sistema', true) = '1')
    WITH CHECK (current_setting('app.modo_sistema', true) = '1');

CREATE POLICY dle_delete ON dead_letter_events
    FOR DELETE
    USING (FALSE);

CREATE OR REPLACE FUNCTION dle_block_imutaveis()
RETURNS trigger AS $$
BEGIN
    IF NEW.consumer_id IS DISTINCT FROM OLD.consumer_id
       OR NEW.event_id IS DISTINCT FROM OLD.event_id
       OR NEW.event_name IS DISTINCT FROM OLD.event_name
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.payload IS DISTINCT FROM OLD.payload
       OR NEW.erro_classe IS DISTINCT FROM OLD.erro_classe
       OR NEW.erro_mensagem IS DISTINCT FROM OLD.erro_mensagem
       OR NEW.erro_stack IS DISTINCT FROM OLD.erro_stack
       OR NEW.tentativas IS DISTINCT FROM OLD.tentativas
       OR NEW.primeira_tentativa IS DISTINCT FROM OLD.primeira_tentativa
       OR NEW.ultima_tentativa IS DISTINCT FROM OLD.ultima_tentativa
    THEN
        RAISE EXCEPTION 'INV-BUS-003: dead_letter_events e append-only operacional — '
                        'so status, resolucao_nota, resolvido_em, resolvido_por_id '
                        'podem ser atualizados.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER dle_anti_mutation_imutaveis
    BEFORE UPDATE ON dead_letter_events
    FOR EACH ROW EXECUTE FUNCTION dle_block_imutaveis();
"""

REVERSE_CONSTRAINTS_AND_RLS = r"""
DROP TRIGGER IF EXISTS dle_anti_mutation_imutaveis ON dead_letter_events;
DROP FUNCTION IF EXISTS dle_block_imutaveis();
DROP POLICY IF EXISTS dle_delete ON dead_letter_events;
DROP POLICY IF EXISTS dle_update ON dead_letter_events;
DROP POLICY IF EXISTS dle_insert ON dead_letter_events;
DROP POLICY IF EXISTS dle_select ON dead_letter_events;
ALTER TABLE dead_letter_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE dead_letter_events DROP CONSTRAINT IF EXISTS dle_tentativas_min;
ALTER TABLE dead_letter_events DROP CONSTRAINT IF EXISTS dle_consumer_id_slug;

DROP POLICY IF EXISTS consumer_idemp_delete ON consumer_idempotencia;
DROP POLICY IF EXISTS consumer_idemp_update ON consumer_idempotencia;
DROP POLICY IF EXISTS consumer_idemp_insert ON consumer_idempotencia;
DROP POLICY IF EXISTS consumer_idemp_select ON consumer_idempotencia;
ALTER TABLE consumer_idempotencia DISABLE ROW LEVEL SECURITY;
ALTER TABLE consumer_idempotencia DROP CONSTRAINT IF EXISTS consumer_idemp_resultado_enum;
ALTER TABLE consumer_idempotencia DROP CONSTRAINT IF EXISTS consumer_idemp_id_slug;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0015_op_tratamento_documento_hash_hmac'),
        ('multitenant', '0004_audit_hash_chain_por_tenant'),  # require_tenant_ctx()
    ]

    operations = [
        migrations.CreateModel(
            name='ConsumerIdempotencia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('consumer_id', models.CharField(max_length=120)),
                ('event_id', models.UUIDField()),
                ('tenant_id', models.UUIDField(blank=True, db_index=True, null=True)),
                ('processado_em', models.DateTimeField(auto_now_add=True)),
                ('resultado', models.CharField(max_length=16)),
            ],
            options={
                'verbose_name': 'Marca de idempotencia de consumer',
                'verbose_name_plural': 'Marcas de idempotencia de consumer',
                'db_table': 'consumer_idempotencia',
                'indexes': [models.Index(fields=['tenant_id', 'processado_em'], name='idx_cons_idemp_tenant_dt')],
                'constraints': [models.UniqueConstraint(fields=('consumer_id', 'event_id'), name='pk_consumer_idemp')],
            },
        ),
        migrations.CreateModel(
            name='DeadLetterEvent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('consumer_id', models.CharField(max_length=120)),
                ('event_id', models.UUIDField()),
                ('event_name', models.CharField(max_length=120)),
                ('tenant_id', models.UUIDField(db_index=True)),
                ('payload', models.JSONField()),
                ('erro_classe', models.CharField(max_length=180)),
                ('erro_mensagem', models.TextField()),
                ('erro_stack', models.TextField(blank=True, default='')),
                ('tentativas', models.IntegerField()),
                ('primeira_tentativa', models.DateTimeField()),
                ('ultima_tentativa', models.DateTimeField()),
                ('status', models.CharField(choices=[('aberto', 'Aberto'), ('reprocessar', 'Reprocessar'), ('descartado', 'Descartado'), ('resolvido', 'Resolvido')], default='aberto', max_length=16)),
                ('resolucao_nota', models.TextField(blank=True, default='')),
                ('resolvido_em', models.DateTimeField(blank=True, null=True)),
                ('resolvido_por_id', models.UUIDField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Dead letter event',
                'verbose_name_plural': 'Dead letter events',
                'db_table': 'dead_letter_events',
                'indexes': [models.Index(fields=['status', 'ultima_tentativa'], name='idx_dle_status_dt'), models.Index(fields=['consumer_id'], name='idx_dle_consumer')],
            },
        ),
        migrations.RunSQL(FORWARD_CONSTRAINTS_AND_RLS, reverse_sql=REVERSE_CONSTRAINTS_AND_RLS),
    ]
