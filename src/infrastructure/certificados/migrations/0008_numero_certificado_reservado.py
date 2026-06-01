"""T-CER-031/032 — tabela `numero_certificado_reservado` + RLS + grants + triggers.

Número VISÍVEL sem buracos (NIT-DICLA-021 / INV-CER-NUM-001) por (tenant, tipo, ano).
Reserva TTL 5min (T-CER-031) com 3 triggers (T-CER-032):
  1. CONSECUTIVIDADE no INSERT — `sequencial <= max(seq)+1` (não pula → buraco proibido);
  2. CONFIRMAÇÃO one-shot + chave (tenant/tipo/ano/sequencial) imutável no UPDATE;
  3. BLOQUEIO de DELETE de número CONFIRMADO (cancelamento PRESERVA o número, não
     devolve à sequência); reservas não-confirmadas (expiradas) podem ser liberadas.

RLS v2 (ADR-0002 §6) + GRANT app_user na MESMA migration (migration-rls-check). A
reserva-de-número-visível é peça NOVA do M8 (M4 só tinha sequence global).

# metrologia-classificacao: IQ
# replay-fixture: none
# audit-immutability: triggers de numeracao do certificado (nao tocam cadeia de auditoria nem o trigger INV-025 de equipamento)
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models

_TAB = "numero_certificado_reservado"

RLS_FORWARD = f"""
ALTER TABLE {_TAB} ENABLE ROW LEVEL SECURITY;
ALTER TABLE {_TAB} FORCE ROW LEVEL SECURITY;

CREATE POLICY {_TAB}_tenant_isolation_select ON {_TAB}
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {_TAB}_tenant_isolation_update ON {_TAB}
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {_TAB}_tenant_isolation_delete ON {_TAB}
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY {_TAB}_tenant_isolation_insert ON {_TAB}
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

RLS_REVERSE = f"""
DROP POLICY IF EXISTS {_TAB}_tenant_isolation_insert ON {_TAB};
DROP POLICY IF EXISTS {_TAB}_tenant_isolation_delete ON {_TAB};
DROP POLICY IF EXISTS {_TAB}_tenant_isolation_update ON {_TAB};
DROP POLICY IF EXISTS {_TAB}_tenant_isolation_select ON {_TAB};
ALTER TABLE {_TAB} DISABLE ROW LEVEL SECURITY;
"""

GRANT_FORWARD = f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE {_TAB} TO app_user;"
GRANT_REVERSE = f"REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLE {_TAB} FROM app_user;"

TRIGGERS_FORWARD = """
-- 1. Consecutividade no INSERT (sem buraco — NIT-DICLA-021 / INV-CER-NUM-001).
CREATE OR REPLACE FUNCTION numero_cert_reservado_consecutivo_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE max_seq integer;
BEGIN
    IF NEW.sequencial < 1 THEN
        RAISE EXCEPTION 'INV-CER-NUM-001: sequencial de certificado deve ser >= 1 (recebeu %).', NEW.sequencial;
    END IF;
    SELECT COALESCE(MAX(sequencial), 0) INTO max_seq
    FROM numero_certificado_reservado
    WHERE tenant_id = NEW.tenant_id AND tipo = NEW.tipo AND ano = NEW.ano;
    IF NEW.sequencial > max_seq + 1 THEN
        RAISE EXCEPTION
            'INV-CER-NUM-001: numero de certificado fora de sequencia consecutiva (seq=% > max+1=%) — buraco visivel proibido (NIT-DICLA-021).',
            NEW.sequencial, max_seq + 1;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER numero_cert_reservado_consecutivo_check_trg
    BEFORE INSERT ON numero_certificado_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_cert_reservado_consecutivo_check();

-- 2. Confirmacao one-shot + chave imutavel no UPDATE.
CREATE OR REPLACE FUNCTION numero_cert_reservado_confirma_one_shot()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.confirmado AND NOT NEW.confirmado THEN
        RAISE EXCEPTION 'INV-CER-NUM-001: confirmacao de numero de certificado e one-shot (nao reverte).';
    END IF;
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.tipo IS DISTINCT FROM OLD.tipo
       OR NEW.ano IS DISTINCT FROM OLD.ano
       OR NEW.sequencial IS DISTINCT FROM OLD.sequencial THEN
        RAISE EXCEPTION 'INV-CER-NUM-001: chave (tenant/tipo/ano/sequencial) do numero reservado e imutavel.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER numero_cert_reservado_confirma_one_shot_trg
    BEFORE UPDATE ON numero_certificado_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_cert_reservado_confirma_one_shot();

-- 3. Bloqueio de DELETE de numero CONFIRMADO (cancelamento PRESERVA o numero).
CREATE OR REPLACE FUNCTION numero_cert_reservado_block_delete_confirmado()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.confirmado THEN
        RAISE EXCEPTION
            'INV-CER-NUM-001: numero de certificado confirmado nao pode ser deletado nem reusado (cancelamento PRESERVA o numero — NIT-DICLA-021).';
    END IF;
    RETURN OLD;
END;
$body$;

CREATE TRIGGER numero_cert_reservado_block_delete_confirmado_trg
    BEFORE DELETE ON numero_certificado_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_cert_reservado_block_delete_confirmado();
"""

TRIGGERS_REVERSE = """
DROP TRIGGER IF EXISTS numero_cert_reservado_block_delete_confirmado_trg ON numero_certificado_reservado;
DROP FUNCTION IF EXISTS numero_cert_reservado_block_delete_confirmado();
DROP TRIGGER IF EXISTS numero_cert_reservado_confirma_one_shot_trg ON numero_certificado_reservado;
DROP FUNCTION IF EXISTS numero_cert_reservado_confirma_one_shot();
DROP TRIGGER IF EXISTS numero_cert_reservado_consecutivo_check_trg ON numero_certificado_reservado;
DROP FUNCTION IF EXISTS numero_cert_reservado_consecutivo_check();
"""


class Migration(migrations.Migration):

    dependencies = [
        ('certificados', '0007_certificado_numero_seq'),
        ('tenant', '0010_remove_tenantperfilhistorico_tph_tenant_recente_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='NumeroCertificadoReservado',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tipo', models.CharField(default='CERTIFICADO', help_text='Discriminador de sequência (1 sequência por tenant+ano).', max_length=20)),
                ('ano', models.IntegerField(db_index=True)),
                ('sequencial', models.IntegerField(help_text='N do <SLUG>-<YYYY>-<NNNNNN> (sem buracos).')),
                ('reservado_em', models.DateTimeField(auto_now_add=True)),
                ('ttl_expira_em', models.DateTimeField(help_text='Reserva não-confirmada expira aqui (T-CER-031 — 5min).')),
                ('confirmado', models.BooleanField(default=False, help_text='True na confirmação one-shot (transação da emissão).')),
                ('correlation_id', models.UUIDField(default=uuid.uuid4)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='numeros_certificado_reservados', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Número de certificado reservado',
                'verbose_name_plural': 'Números de certificado reservados',
                'db_table': 'numero_certificado_reservado',
                'ordering': ['tenant', 'tipo', 'ano', 'sequencial'],
                'indexes': [models.Index(fields=['tenant', 'tipo', 'ano'], name='ix_num_cert_reservado_chave')],
                'constraints': [models.UniqueConstraint(fields=('tenant', 'tipo', 'ano', 'sequencial'), name='uq_num_cert_reservado')],
            },
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
        migrations.RunSQL(sql=GRANT_FORWARD, reverse_sql=GRANT_REVERSE),
        migrations.RunSQL(sql=TRIGGERS_FORWARD, reverse_sql=TRIGGERS_REVERSE),
    ]
