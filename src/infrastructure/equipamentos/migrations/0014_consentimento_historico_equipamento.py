"""T-EQP-039 (US-EQP-004 AC-EQP-004-6 / P-EQP-R6) — tabela
`equipamentos_consentimento_historico` + RLS pattern v2 + trigger PG
imutabilidade pos-insert.

Tabela dedicada de consentimento granular do cedente (3 niveis: nada/
resumo/completo). 1 registro por transferencia efetivada. Revogacao
posterior (T-EQP-041) muta APENAS 4 campos (`revogado_em`,
`revogado_por_id`, `revogado_justificativa_hash`, `revogado_via`) e
e one-shot — segunda revogacao bloqueada por trigger.

Trigger PG `consentimento_historico_imutavel_pos_insert`:
- Bloqueia UPDATE em qualquer campo CORE (12 campos imutaveis listados
  abaixo).
- Quando `OLD.revogado_em IS NOT NULL`: bloqueia TODA mutacao (revogar
  novamente nao faz sentido — reconceder exige nova transferencia).

# tests-coverage: tests/test_equipamentos_consentimento_historico_t_eqp_039_041.py
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

RLS_FORWARD = """
-- =============================================================
-- RLS pattern v2 (ADR-0002 sec.6) — igual equipamentos.0012
-- =============================================================
ALTER TABLE equipamentos_consentimento_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_consentimento_historico FORCE ROW LEVEL SECURITY;

CREATE POLICY consent_hist_tenant_isolation_select ON equipamentos_consentimento_historico
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY consent_hist_tenant_isolation_update ON equipamentos_consentimento_historico
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY consent_hist_tenant_isolation_delete ON equipamentos_consentimento_historico
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY consent_hist_tenant_isolation_insert ON equipamentos_consentimento_historico
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- T-EQP-039 — trigger imutabilidade pos-insert.
-- 12 campos CORE imutaveis. Apenas 4 campos de revogacao podem mutar
-- (one-shot — segunda revogacao bloqueada).
-- =============================================================
CREATE OR REPLACE FUNCTION consent_hist_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- 12 campos CORE NUNCA podem mudar pos-INSERT.
    IF (
           NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
        OR NEW.equipamento_id IS DISTINCT FROM OLD.equipamento_id
        OR NEW.transferencia_origem_id IS DISTINCT FROM OLD.transferencia_origem_id
        OR NEW.cedente_cliente_id IS DISTINCT FROM OLD.cedente_cliente_id
        OR NEW.nivel IS DISTINCT FROM OLD.nivel
        OR NEW.concedido_por_id IS DISTINCT FROM OLD.concedido_por_id
        OR NEW.concedido_em IS DISTINCT FROM OLD.concedido_em
        OR NEW.via_concessao IS DISTINCT FROM OLD.via_concessao
        OR NEW.id IS DISTINCT FROM OLD.id
    ) THEN
        RAISE EXCEPTION
            'T-EQP-039: consentimento historico tem campos CORE imutaveis pos-INSERT (P-EQP-R6).';
    END IF;

    -- Revogacao e one-shot. Se ja foi revogado, NADA pode mudar.
    IF OLD.revogado_em IS NOT NULL AND (
           NEW.revogado_em IS DISTINCT FROM OLD.revogado_em
        OR NEW.revogado_por_id IS DISTINCT FROM OLD.revogado_por_id
        OR NEW.revogado_justificativa_hash IS DISTINCT FROM OLD.revogado_justificativa_hash
        OR NEW.revogado_via IS DISTINCT FROM OLD.revogado_via
    ) THEN
        RAISE EXCEPTION
            'T-EQP-041: consentimento ja revogado — re-revogar bloqueado (one-shot).';
    END IF;

    RETURN NEW;
END;
$body$;

CREATE TRIGGER consent_hist_imutavel_trg
    BEFORE UPDATE ON equipamentos_consentimento_historico
    FOR EACH ROW
    EXECUTE FUNCTION consent_hist_imutavel_check();
"""

RLS_REVERSE = """
DROP TRIGGER IF EXISTS consent_hist_imutavel_trg ON equipamentos_consentimento_historico;
DROP FUNCTION IF EXISTS consent_hist_imutavel_check();
DROP POLICY IF EXISTS consent_hist_tenant_isolation_insert ON equipamentos_consentimento_historico;
DROP POLICY IF EXISTS consent_hist_tenant_isolation_delete ON equipamentos_consentimento_historico;
DROP POLICY IF EXISTS consent_hist_tenant_isolation_update ON equipamentos_consentimento_historico;
DROP POLICY IF EXISTS consent_hist_tenant_isolation_select ON equipamentos_consentimento_historico;
ALTER TABLE equipamentos_consentimento_historico DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0013_seed_authz_transferir'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ConsentimentoHistoricoEquipamento',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('cedente_cliente_id', models.UUIDField(blank=True, help_text='Snapshot do cedente no momento da concessao. NULL quando equipamento ja era orfao (cedente eliminado por LGPD antes da transferencia — caso raro).', null=True)),
                ('nivel', models.CharField(choices=[('nada', 'Nada — apenas dados pos-transferencia'), ('resumo', 'Resumo — ultima calibracao + ultima versao'), ('completo', 'Completo — historico inteiro')], help_text='3 niveis: nada/resumo/completo (P-EQP-R6).', max_length=20)),
                ('concedido_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('via_concessao', models.CharField(choices=[('presencial_atendente', 'Presencial via atendente (fraca — exige cap de risco GATE-EQP-S5)'), ('contrato_fisico_digitalizado', 'Contrato fisico digitalizado'), ('portal_cliente_otp', 'Portal do cliente (OTP — Wave B+ GATE-EQP-3)')], help_text='Mesma via do aceite_cedente da TransferenciaEquipamentoAceite (consistencia auditavel).', max_length=40)),
                ('revogado_em', models.DateTimeField(blank=True, null=True)),
                ('revogado_justificativa_hash', models.CharField(blank=True, default='', help_text='HMAC-SHA256 da justificativa em claro com salt do tenant. Texto cru NUNCA persistido (mesma regra `motivo_detalhe` da transferencia).', max_length=128)),
                ('revogado_via', models.CharField(blank=True, choices=[('presencial_atendente', 'Presencial via atendente (fraca — exige cap de risco GATE-EQP-S5)'), ('contrato_fisico_digitalizado', 'Contrato fisico digitalizado'), ('portal_cliente_otp', 'Portal do cliente (OTP — Wave B+ GATE-EQP-3)')], default='', max_length=40)),
                ('concedido_por', models.ForeignKey(help_text='Atendente/admin que processou o aceite presencialmente (Marco 2 dogfooding). Portal-cliente OTP (Wave B+ GATE-EQP-3) gravara o proprio usuario do cedente.', on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_historico_concedidos', to=settings.AUTH_USER_MODEL)),
                ('equipamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_historico', to='equipamentos.equipamento')),
                ('revogado_por', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_historico_revogados', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_historico_equipamento', to='tenant.tenant')),
                ('transferencia_origem', models.ForeignKey(db_constraint=False, help_text='Transferencia que originou este consentimento (1:1 logico). db_constraint=False por consistencia com FKs cliente_atual (RLS no banco).', on_delete=django.db.models.deletion.PROTECT, related_name='consentimentos_historico', to='equipamentos.transferenciaequipamentoaceite')),
            ],
            options={
                'verbose_name': 'Consentimento historico de equipamento',
                'verbose_name_plural': 'Consentimentos historicos de equipamentos',
                'db_table': 'equipamentos_consentimento_historico',
                'ordering': ['-concedido_em'],
                'indexes': [
                    models.Index(fields=['tenant', 'equipamento', '-concedido_em'], name='equipamento_tenant__e17c72_idx'),
                    models.Index(fields=['transferencia_origem'], name='equipamento_transfe_a989c0_idx'),
                ],
                'constraints': [
                    models.UniqueConstraint(
                        condition=models.Q(('revogado_em__isnull', True)),
                        fields=('transferencia_origem',),
                        name='uq_consent_hist_ativo_por_transferencia',
                    ),
                ],
            },
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
        migrations.AlterField(
            model_name='transferenciaequipamentoaceite',
            name='aceite_cedente',
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Schema: {tipo: ViaAceiteTransferencia, usuario_id_atendente: "
                    "UUID, observacao: str, consentimento_historico_expresso: bool, "
                    "nivel_consentimento_historico: 'nada'|'resumo'|'completo'?}. "
                    "{} antes do aceite ser registrado. T-EQP-039: nivel granular "
                    "(P-EQP-R6) — quando ausente, deriva via "
                    "`consentimento_historico_expresso` (True=completo / False=nada)."
                ),
            ),
        ),
    ]
