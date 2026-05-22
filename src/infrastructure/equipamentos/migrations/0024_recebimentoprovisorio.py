"""T-EQP-053 (US-EQP-006 AC-EQP-006-6 / INV-EQP-PROV-001 / P-EQP-R9 /
Caminho A Roldao) — tabela `equipamentos_recebimento_provisorio` +
`equipamentos_recebimento_provisorio_foto` + RLS pattern v2 + trigger
PG imutabilidade pos-INSERT (3 campos podem mutar 1 vez).

`RecebimentoProvisorio` e SEPARADO de `Equipamento` ate ser promovido
(equipamento chegou ao laboratorio sem cadastro completo). TTL D+7;
job marca como expirado_descartado.

# tests-coverage: tests/test_equipamentos_provisorio_t_eqp_053.py
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

RLS_FORWARD = """
ALTER TABLE equipamentos_recebimento_provisorio ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_recebimento_provisorio FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_recebimento_provisorio_tenant_isolation_select ON equipamentos_recebimento_provisorio
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_tenant_isolation_update ON equipamentos_recebimento_provisorio
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_tenant_isolation_delete ON equipamentos_recebimento_provisorio
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_tenant_isolation_insert ON equipamentos_recebimento_provisorio
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

ALTER TABLE equipamentos_recebimento_provisorio_foto ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_recebimento_provisorio_foto FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_recebimento_provisorio_foto_tenant_isolation_select ON equipamentos_recebimento_provisorio_foto
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_foto_tenant_isolation_update ON equipamentos_recebimento_provisorio_foto
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_foto_tenant_isolation_delete ON equipamentos_recebimento_provisorio_foto
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_provisorio_foto_tenant_isolation_insert ON equipamentos_recebimento_provisorio_foto
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- T-EQP-053 — trigger imutabilidade pos-INSERT.
-- 10 campos CORE imutaveis; 3 campos podem mutar 1 vez
-- (status pendente -> promovido/expirado, equipamento_promovido_id,
-- promovido_em). Apos cruzar terminal (promovido/expirado), nada muda.
-- =============================================================
CREATE OR REPLACE FUNCTION recebimento_provisorio_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos CORE NUNCA mudam.
    IF (
           NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
        OR NEW.id IS DISTINCT FROM OLD.id
        OR NEW.tag_provisoria IS DISTINCT FROM OLD.tag_provisoria
        OR NEW.descricao_estimada IS DISTINCT FROM OLD.descricao_estimada
        OR NEW.condicao_visual_chegada IS DISTINCT FROM OLD.condicao_visual_chegada
        OR NEW.foto_storage_key IS DISTINCT FROM OLD.foto_storage_key
        OR NEW.foto_sha256 IS DISTINCT FROM OLD.foto_sha256
        OR NEW.recebido_por_id IS DISTINCT FROM OLD.recebido_por_id
        OR NEW.data_recebimento IS DISTINCT FROM OLD.data_recebimento
        OR NEW.ttl_expira_em IS DISTINCT FROM OLD.ttl_expira_em
    ) THEN
        RAISE EXCEPTION
            'T-EQP-053: provisorio tem campos CORE imutaveis pos-INSERT.';
    END IF;
    -- Status terminal (promovido / expirado_descartado) — nada pode mudar.
    IF OLD.status IN ('promovido', 'expirado_descartado') AND (
           NEW.status IS DISTINCT FROM OLD.status
        OR NEW.equipamento_promovido_id IS DISTINCT FROM OLD.equipamento_promovido_id
        OR NEW.promovido_em IS DISTINCT FROM OLD.promovido_em
    ) THEN
        RAISE EXCEPTION
            'T-EQP-053: provisorio em estado terminal (%) — re-mutacao bloqueada.',
            OLD.status;
    END IF;
    -- Matriz de transicao do status: pendente -> {promovido, expirado_descartado}.
    IF NEW.status IS DISTINCT FROM OLD.status THEN
        IF OLD.status = 'pendente_promocao' AND NEW.status NOT IN
            ('promovido', 'expirado_descartado') THEN
            RAISE EXCEPTION
                'T-EQP-053: provisorio status pendente_promocao -> % invalido.',
                NEW.status;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER recebimento_provisorio_imutavel_trg
    BEFORE UPDATE ON equipamentos_recebimento_provisorio
    FOR EACH ROW
    EXECUTE FUNCTION recebimento_provisorio_imutavel_check();
"""

RLS_REVERSE = """
DROP TRIGGER IF EXISTS recebimento_provisorio_imutavel_trg ON equipamentos_recebimento_provisorio;
DROP FUNCTION IF EXISTS recebimento_provisorio_imutavel_check();
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_foto_tenant_isolation_insert ON equipamentos_recebimento_provisorio_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_foto_tenant_isolation_delete ON equipamentos_recebimento_provisorio_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_foto_tenant_isolation_update ON equipamentos_recebimento_provisorio_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_foto_tenant_isolation_select ON equipamentos_recebimento_provisorio_foto;
ALTER TABLE equipamentos_recebimento_provisorio_foto DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_tenant_isolation_insert ON equipamentos_recebimento_provisorio;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_tenant_isolation_delete ON equipamentos_recebimento_provisorio;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_tenant_isolation_update ON equipamentos_recebimento_provisorio;
DROP POLICY IF EXISTS equipamentos_recebimento_provisorio_tenant_isolation_select ON equipamentos_recebimento_provisorio;
ALTER TABLE equipamentos_recebimento_provisorio DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0023_seed_authz_devolver'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RecebimentoProvisorio',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('tag_provisoria', models.CharField(help_text="TAG temporaria operacional (ex: 'PROV-2026-05-23-001'). NAO precisa ser unica entre tenants nem entre provisorios — a promocao gera TAG canonica em Equipamento.tag (INV-049).", max_length=50)),
                ('descricao_estimada', models.CharField(help_text="Descricao livre informada pelo operador no recebimento provisorio (ex: 'Balanca digital marca incerta cap 30kg'). Anti-PII (mesmo padrao localizacao_fisica).", max_length=200)),
                ('condicao_visual_chegada', models.CharField(choices=[('integro', 'Integro'), ('amassado', 'Amassado'), ('lacre_violado', 'Lacre violado'), ('contaminado', 'Contaminado'), ('sem_acessorios', 'Sem acessorios'), ('outros', 'Outros')], max_length=30)),
                ('foto_storage_key', models.CharField(help_text='Obrigatoria sempre — defesa contra cliente reclamar dano pos-entrega.', max_length=64)),
                ('foto_sha256', models.CharField(help_text='SHA-256 hex do binario pos-EXIF-strip. Imutavel pos-INSERT.', max_length=64)),
                ('data_recebimento', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('ttl_expira_em', models.DateTimeField(help_text='D+7 dias corridos a partir de data_recebimento. Job `processar_provisorios_expirados` marca status=expirado_descartado ao cruzar.')),
                ('status', models.CharField(choices=[('pendente_promocao', 'Pendente de promocao'), ('promovido', 'Promovido a equipamento definitivo'), ('expirado_descartado', 'Expirado descartado')], default='pendente_promocao', max_length=30)),
                ('equipamento_promovido_id', models.UUIDField(blank=True, help_text='Aponta para Equipamento.id quando promovido. NULL ate promocao; UUID imutavel pos-promocao.', null=True)),
                ('promovido_em', models.DateTimeField(blank=True, null=True)),
                ('recebido_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='provisorios_registrados', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimentos_provisorios', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Recebimento provisorio',
                'verbose_name_plural': 'Recebimentos provisorios',
                'db_table': 'equipamentos_recebimento_provisorio',
                'ordering': ['-data_recebimento'],
            },
        ),
        migrations.CreateModel(
            name='RecebimentoProvisorioFoto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('storage_key', models.CharField(max_length=64, unique=True)),
                ('conteudo_bytes', models.BinaryField()),
                ('mime_type', models.CharField(max_length=30)),
                ('tamanho_bytes', models.PositiveIntegerField()),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('provisorio', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='foto', to='equipamentos.recebimentoprovisorio')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='provisorio_fotos', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Foto de recebimento provisorio',
                'verbose_name_plural': 'Fotos de recebimentos provisorios',
                'db_table': 'equipamentos_recebimento_provisorio_foto',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.AddIndex(
            model_name='recebimentoprovisorio',
            index=models.Index(fields=['tenant', 'status', '-data_recebimento'], name='equipamento_tenant__d485e0_idx'),
        ),
        migrations.AddIndex(
            model_name='recebimentoprovisorio',
            index=models.Index(fields=['tenant', 'ttl_expira_em'], name='equipamento_tenant__a4ebda_idx'),
        ),
        migrations.AddConstraint(
            model_name='recebimentoprovisorio',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('status', 'promovido'), ('equipamento_promovido_id__isnull', False), ('promovido_em__isnull', False)), models.Q(models.Q(('status', 'promovido'), _negated=True), ('equipamento_promovido_id__isnull', True), ('promovido_em__isnull', True)), _connector='OR'), name='ck_provisorio_promovido_all_or_nothing'),
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
    ]
