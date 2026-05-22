"""T-EQP-051 (US-EQP-006 AC-EQP-006-4 / ISO 17025 cl. 7.4.5) — tabela
`equipamentos_devolucao` + RLS pattern v2 + trigger PG imutabilidade
pos-INSERT (devolucao e terminal).

Devolucao 1:1 com EquipamentoRecebimento (encerra o ciclo do
laboratorio). Re-recebimento futuro cria NOVO EquipamentoRecebimento.

Imutabilidade: nenhum campo pode mudar pos-INSERT (CPC art. 411 III +
RAT-EQP-FOTO + termo_aceite_hash defende contra adulteracao).

# tests-coverage: tests/test_equipamentos_devolver_t_eqp_051.py
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

RLS_FORWARD = """
ALTER TABLE equipamentos_devolucao ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_devolucao FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_devolucao_tenant_isolation_select ON equipamentos_devolucao
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_tenant_isolation_update ON equipamentos_devolucao
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_tenant_isolation_delete ON equipamentos_devolucao
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_tenant_isolation_insert ON equipamentos_devolucao
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- T-EQP-051 — trigger imutabilidade pos-INSERT.
-- Devolucao e terminal; nenhum campo pode mudar.
-- =============================================================
CREATE OR REPLACE FUNCTION devolucao_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'T-EQP-051: devolucao e terminal e imutavel pos-INSERT (ISO 17025 cl. 7.4.5).';
END;
$body$;

CREATE TRIGGER devolucao_imutavel_trg
    BEFORE UPDATE ON equipamentos_devolucao
    FOR EACH ROW
    EXECUTE FUNCTION devolucao_imutavel_check();
"""

RLS_REVERSE = """
DROP TRIGGER IF EXISTS devolucao_imutavel_trg ON equipamentos_devolucao;
DROP FUNCTION IF EXISTS devolucao_imutavel_check();
DROP POLICY IF EXISTS equipamentos_devolucao_tenant_isolation_insert ON equipamentos_devolucao;
DROP POLICY IF EXISTS equipamentos_devolucao_tenant_isolation_delete ON equipamentos_devolucao;
DROP POLICY IF EXISTS equipamentos_devolucao_tenant_isolation_update ON equipamentos_devolucao;
DROP POLICY IF EXISTS equipamentos_devolucao_tenant_isolation_select ON equipamentos_devolucao;
ALTER TABLE equipamentos_devolucao DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0020_seed_authz_receber'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipamentoDevolucao',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('condicao_visual_devolucao', models.CharField(choices=[('integro', 'Integro'), ('amassado', 'Amassado'), ('lacre_violado', 'Lacre violado'), ('contaminado', 'Contaminado'), ('sem_acessorios', 'Sem acessorios'), ('outros', 'Outros')], help_text='Reusa enum CondicaoVisualChegada (mesmo escopo) — registra estado fisico na devolucao (RAT-EQP-FOTO protecao bilateral).', max_length=30)),
                ('foto_storage_key', models.CharField(help_text='Marco 2 dogfooding: obrigatoria sempre. Wave A: opcional em perfil B/C/D. Imutavel via trigger PG.', max_length=64)),
                ('foto_sha256', models.CharField(help_text='SHA-256 hex do binario pos-EXIF-strip. Imutavel pos-INSERT.', max_length=64)),
                ('termo_devolucao_versao_id', models.CharField(default='v1.0-2026-05-23', help_text='Versao do texto canonico do termo (CPC art. 411 III). `termo-devolucao.md` v1.0; Marco 2 default; Wave A: tabela `TermoDevolucaoVersao` com bumps.', max_length=30)),
                ('termo_aceite_hash', models.CharField(help_text='HMAC-SHA256 com salt tenant de `{texto_termo}|{usuario_id}|{ip_hash}|{aceite_em_iso}`. Defesa anti-adulteracao + prova de aceite.', max_length=128)),
                ('devolvido_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('devolvido_por', models.ForeignKey(help_text='Atendente/almoxarife que processou a devolucao. Em portal-cliente OTP Wave B+ pode ser o proprio cliente.', on_delete=django.db.models.deletion.PROTECT, related_name='devolucoes_registradas', to=settings.AUTH_USER_MODEL)),
                ('recebimento', models.OneToOneField(help_text='OneToOne — uma devolucao encerra um recebimento. Re-recebimento futuro cria novo EquipamentoRecebimento.', on_delete=django.db.models.deletion.PROTECT, related_name='devolucao', to='equipamentos.equipamentorecebimento')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devolucoes_equipamento', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Devolucao de equipamento',
                'verbose_name_plural': 'Devolucoes de equipamentos',
                'db_table': 'equipamentos_devolucao',
                'ordering': ['-devolvido_em'],
                'indexes': [models.Index(fields=['tenant', '-devolvido_em'], name='equipamento_tenant__ec0665_idx')],
            },
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
    ]
