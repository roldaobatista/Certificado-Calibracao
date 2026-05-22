"""T-EQP-042+043+046 (US-EQP-005 AC-EQP-005-1+2+5 / P-EQP-S9 / P-EQP-R8)
— tabela `equipamentos_sucatamento` + RLS pattern v2 + trigger PG
imutabilidade pos-INSERT.

Sucatamento e estado terminal. Tabela 1:1 com Equipamento.

INV-INT-002 (estado terminal): trigger `transicao_status_permitida` em
migration 0002 ja bloqueia transicoes invalidas (`sucata→extraviado`
e a unica excecao). Nao precisa de novo trigger de status aqui.

Imutabilidade: registro de sucatamento NUNCA muda apos INSERT. Trigger
`sucatamento_imutavel_pos_insert` bloqueia TODO UPDATE.

CHECK `ck_sucatamento_cert_vigente_exige_dupla_confirmacao` (Django
CheckConstraint ja no Meta) cobre P-EQP-R8/AC-EQP-005-2.

# tests-coverage: tests/test_equipamentos_sucatar_t_eqp_042_046.py
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

RLS_FORWARD = """
ALTER TABLE equipamentos_sucatamento ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_sucatamento FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_sucatamento_tenant_isolation_select ON equipamentos_sucatamento
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_sucatamento_tenant_isolation_update ON equipamentos_sucatamento
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_sucatamento_tenant_isolation_delete ON equipamentos_sucatamento
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_sucatamento_tenant_isolation_insert ON equipamentos_sucatamento
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- T-EQP-042 — trigger imutabilidade pos-INSERT.
-- Sucatamento e terminal; nenhum campo pode mudar pos-INSERT.
-- =============================================================
CREATE OR REPLACE FUNCTION sucatamento_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'T-EQP-042: sucatamento e terminal e imutavel pos-INSERT (AC-EQP-005-3).';
END;
$body$;

CREATE TRIGGER sucatamento_imutavel_trg
    BEFORE UPDATE ON equipamentos_sucatamento
    FOR EACH ROW
    EXECUTE FUNCTION sucatamento_imutavel_check();
"""

RLS_REVERSE = """
DROP TRIGGER IF EXISTS sucatamento_imutavel_trg ON equipamentos_sucatamento;
DROP FUNCTION IF EXISTS sucatamento_imutavel_check();
DROP POLICY IF EXISTS equipamentos_sucatamento_tenant_isolation_insert ON equipamentos_sucatamento;
DROP POLICY IF EXISTS equipamentos_sucatamento_tenant_isolation_delete ON equipamentos_sucatamento;
DROP POLICY IF EXISTS equipamentos_sucatamento_tenant_isolation_update ON equipamentos_sucatamento;
DROP POLICY IF EXISTS equipamentos_sucatamento_tenant_isolation_select ON equipamentos_sucatamento;
ALTER TABLE equipamentos_sucatamento DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0016_resolver_qr_publico_tenant_lookup'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipamentoSucatamento',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('justificativa_hash', models.CharField(help_text='HMAC-SHA256 da justificativa em claro (>=30 chars + anti-PII) com salt do tenant. Texto cru NUNCA persistido.', max_length=128)),
                ('tem_cert_vigente_no_momento', models.BooleanField(help_text='Captura snapshot do estado de certificado no momento do sucatamento (AC-EQP-005-2). Determina se evento extra `equipamento.sucateado_com_cert_vigente` foi disparado + se `confirmacao_dupla=True` era obrigatorio.')),
                ('confirmacao_dupla', models.BooleanField(help_text='AC-EQP-005-2 — True OBRIGATORIO quando tem_cert_vigente_no_momento=True. Valida que UI exibiu o modal + usuario confirmou ciencia.')),
                ('texto_modal_versao_id', models.CharField(default='v1.0-2026-05-23', help_text='Versao do texto canonico do modal exibido (P-EQP-S9). `template-notificacao-sucatamento.md` v1.0; Marco 2 default `v1.0-2026-05-23`; Wave A: tabela `TextoModalSucatamentoVersao`.', max_length=30)),
                ('ciencia_validade_tecnica_registrada', models.BooleanField(default=False, help_text='P-EQP-R8 / AC-EQP-005-5 — True OBRIGATORIO quando tem_cert_vigente_no_momento=True. Confirma ciencia da validade tecnica do certificado emitido (ISO 17025 §7.1.1).')),
                ('sucateado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('equipamento', models.OneToOneField(help_text='OneToOne — sucatamento e terminal e unico por equipamento.', on_delete=django.db.models.deletion.PROTECT, related_name='sucatamento', to='equipamentos.equipamento')),
                ('sucateado_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sucatamentos_solicitados', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sucatamentos_equipamento', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Sucatamento de equipamento',
                'verbose_name_plural': 'Sucatamentos de equipamentos',
                'db_table': 'equipamentos_sucatamento',
                'ordering': ['-sucateado_em'],
                'indexes': [models.Index(fields=['tenant', '-sucateado_em'], name='equipamento_tenant__2a5597_idx')],
                'constraints': [models.CheckConstraint(condition=models.Q(('tem_cert_vigente_no_momento', False), models.Q(('tem_cert_vigente_no_momento', True), ('confirmacao_dupla', True), ('ciencia_validade_tecnica_registrada', True)), _connector='OR'), name='ck_sucatamento_cert_vigente_exige_dupla_confirmacao')],
            },
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
    ]
