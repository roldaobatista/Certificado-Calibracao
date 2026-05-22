"""T-EQP-047+058 (US-EQP-006 AC-EQP-006-1+10 / P-EQP-S3) — tabela
`equipamentos_recebimento` + `equipamentos_recebimento_foto` (BYTEA
inline Marco 2 dogfooding) + RLS pattern v2 + 2 triggers PG:

- `transicao_status_fluxo_lab_check`: matriz de 9 fases + 2 terminais
  (AC-EQP-006-3b / P-EQP-R3).
- `recebimento_foto_imutavel_check`: bloqueia mutacao em
  `foto_storage_key` e `foto_sha256` pos-INSERT (P-EQP-S3 corretora
  RAT-EQP-FOTO).

CHECK ck_recebimento_anomalia_exige_decisao (Django CheckConstraint
ja no Meta) cobre AC-EQP-006-2 (anomalia exige decisao + justificativa).

# tests-coverage: tests/test_equipamentos_receber_t_eqp_047_058.py
"""

import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

RLS_FORWARD = """
-- =============================================================
-- RLS pattern v2 — equipamentos_recebimento + equipamentos_recebimento_foto
-- =============================================================
ALTER TABLE equipamentos_recebimento ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_recebimento FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_recebimento_tenant_isolation_select ON equipamentos_recebimento
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_tenant_isolation_update ON equipamentos_recebimento
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_tenant_isolation_delete ON equipamentos_recebimento
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_tenant_isolation_insert ON equipamentos_recebimento
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

ALTER TABLE equipamentos_recebimento_foto ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_recebimento_foto FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_recebimento_foto_tenant_isolation_select ON equipamentos_recebimento_foto
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_foto_tenant_isolation_update ON equipamentos_recebimento_foto
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_foto_tenant_isolation_delete ON equipamentos_recebimento_foto
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_recebimento_foto_tenant_isolation_insert ON equipamentos_recebimento_foto
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- T-EQP-058 (P-EQP-S3) — trigger imutabilidade foto_storage_key +
-- foto_sha256 pos-INSERT. Demais campos podem mutar (status_fluxo_lab
-- progride via T-EQP-050 transicionar; decisao/justificativa podem
-- ser corrigidas em inspecao_visual).
-- =============================================================
CREATE OR REPLACE FUNCTION recebimento_foto_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.foto_storage_key IS DISTINCT FROM OLD.foto_storage_key THEN
        RAISE EXCEPTION
            'T-EQP-058 (P-EQP-S3): foto_storage_key imutavel pos-INSERT (RAT-EQP-FOTO).';
    END IF;
    IF NEW.foto_sha256 IS DISTINCT FROM OLD.foto_sha256 THEN
        RAISE EXCEPTION
            'T-EQP-058 (P-EQP-S3): foto_sha256 imutavel pos-INSERT (RAT-EQP-FOTO).';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER recebimento_foto_imutavel_trg
    BEFORE UPDATE ON equipamentos_recebimento
    FOR EACH ROW
    EXECUTE FUNCTION recebimento_foto_imutavel_check();

-- =============================================================
-- T-EQP-050 (AC-EQP-006-3b / P-EQP-R3) — matriz de transicao
-- status_fluxo_lab. 9 fases + 2 alternativos terminais.
-- =============================================================
CREATE OR REPLACE FUNCTION transicao_status_fluxo_lab_permitida(
    p_de text, p_para text
)
RETURNS boolean LANGUAGE plpgsql IMMUTABLE AS $body$
BEGIN
    IF p_de IS NULL OR p_de = '' THEN
        RETURN p_para IN ('recebido_pendente_inspecao', 'aguardando_recebimento');
    END IF;
    IF p_de = p_para THEN RETURN TRUE; END IF;
    -- Estados terminais nao saem.
    IF p_de IN ('devolvido', 'nao_conformidade_recebimento',
                'nao_conformidade_calibracao') THEN
        RETURN FALSE;
    END IF;
    -- Fluxo principal (linear) + NC saindo de qualquer estado nao-terminal.
    IF (p_de, p_para) IN (
        ('aguardando_recebimento', 'recebido_pendente_inspecao'),
        ('recebido_pendente_inspecao', 'em_inspecao_visual'),
        ('em_inspecao_visual', 'aguardando_calibracao'),
        ('aguardando_calibracao', 'aguardando_padrao_disponivel'),
        ('aguardando_calibracao', 'em_calibracao'),
        ('aguardando_padrao_disponivel', 'em_calibracao'),
        ('em_calibracao', 'aguardando_aprovacao_tecnica'),
        ('aguardando_aprovacao_tecnica', 'aguardando_devolucao'),
        ('aguardando_devolucao', 'devolvido')
    ) THEN
        RETURN TRUE;
    END IF;
    -- NC recebimento: pode sair de inspecao_visual ou recebido_pendente.
    IF p_para = 'nao_conformidade_recebimento'
       AND p_de IN ('recebido_pendente_inspecao', 'em_inspecao_visual') THEN
        RETURN TRUE;
    END IF;
    -- NC calibracao: pode sair de em_calibracao ou aguardando_aprovacao.
    IF p_para = 'nao_conformidade_calibracao'
       AND p_de IN ('em_calibracao', 'aguardando_aprovacao_tecnica',
                    'aguardando_padrao_disponivel') THEN
        RETURN TRUE;
    END IF;
    RETURN FALSE;
END;
$body$;

CREATE OR REPLACE FUNCTION transicao_status_fluxo_lab_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.status_fluxo_lab IS DISTINCT FROM OLD.status_fluxo_lab THEN
        IF NOT transicao_status_fluxo_lab_permitida(
            OLD.status_fluxo_lab, NEW.status_fluxo_lab
        ) THEN
            RAISE EXCEPTION
                'T-EQP-050 (AC-EQP-006-3b): transicao % -> % invalida.',
                OLD.status_fluxo_lab, NEW.status_fluxo_lab;
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER transicao_status_fluxo_lab_trg
    BEFORE UPDATE ON equipamentos_recebimento
    FOR EACH ROW
    EXECUTE FUNCTION transicao_status_fluxo_lab_check();
"""

RLS_REVERSE = """
DROP TRIGGER IF EXISTS transicao_status_fluxo_lab_trg ON equipamentos_recebimento;
DROP TRIGGER IF EXISTS recebimento_foto_imutavel_trg ON equipamentos_recebimento;
DROP FUNCTION IF EXISTS transicao_status_fluxo_lab_check();
DROP FUNCTION IF EXISTS transicao_status_fluxo_lab_permitida(text, text);
DROP FUNCTION IF EXISTS recebimento_foto_imutavel_check();
DROP POLICY IF EXISTS equipamentos_recebimento_foto_tenant_isolation_insert ON equipamentos_recebimento_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_foto_tenant_isolation_delete ON equipamentos_recebimento_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_foto_tenant_isolation_update ON equipamentos_recebimento_foto;
DROP POLICY IF EXISTS equipamentos_recebimento_foto_tenant_isolation_select ON equipamentos_recebimento_foto;
ALTER TABLE equipamentos_recebimento_foto DISABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS equipamentos_recebimento_tenant_isolation_insert ON equipamentos_recebimento;
DROP POLICY IF EXISTS equipamentos_recebimento_tenant_isolation_delete ON equipamentos_recebimento;
DROP POLICY IF EXISTS equipamentos_recebimento_tenant_isolation_update ON equipamentos_recebimento;
DROP POLICY IF EXISTS equipamentos_recebimento_tenant_isolation_select ON equipamentos_recebimento;
ALTER TABLE equipamentos_recebimento DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0018_seed_authz_sucatear'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipamentoRecebimento',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('condicao_visual_chegada', models.CharField(choices=[('integro', 'Integro'), ('amassado', 'Amassado'), ('lacre_violado', 'Lacre violado'), ('contaminado', 'Contaminado'), ('sem_acessorios', 'Sem acessorios'), ('outros', 'Outros')], max_length=30)),
                ('anomalias_observadas', models.TextField(blank=True, default='', help_text='Anti-PII (INV-EQP-ANOM-001) — texto <=500 chars descrevendo o estado fisico. Proibido CPF/CNPJ/email/telefone/nomes.')),
                ('decisao_apos_anomalia', models.CharField(blank=True, choices=[('prosseguir', 'Prosseguir mesmo assim'), ('contatar_cliente_aguardando', 'Contatar cliente e aguardar resposta'), ('recusar_recebimento', 'Recusar recebimento'), ('aceitar_com_ressalva', 'Aceitar com ressalva')], default='', help_text="Obrigatoria quando condicao_visual_chegada != 'integro' (AC-EQP-006-2). Defesa A: service raise; B: CHECK Django.", max_length=40)),
                ('justificativa_decisao', models.TextField(blank=True, default='', help_text='>=30 chars + anti-PII (INV-EQP-ANOM-002) quando decisao preenchida. Texto cru gravado (nao hash — auditoria ISO 17025 cl. 7.4 exige rastreabilidade legivel).')),
                ('foto_storage_key', models.CharField(blank=True, default='', help_text='UUID opaco gerado pelo FotoStorageService.salvar. Vazio quando perfil B/C/D recebe sem foto (perfil A: obrigatoria — service valida).', max_length=64)),
                ('foto_sha256', models.CharField(blank=True, default='', help_text='SHA-256 hex do binario FINAL pos-EXIF-strip (P-EQP-S3 / corretora RAT-EQP-FOTO). Imutavel via trigger PG pos-INSERT. Vazio quando foto_storage_key vazio.', max_length=64)),
                ('status_fluxo_lab', models.CharField(choices=[('aguardando_recebimento', 'Aguardando recebimento'), ('recebido_pendente_inspecao', 'Recebido pendente de inspecao'), ('em_inspecao_visual', 'Em inspecao visual'), ('aguardando_calibracao', 'Aguardando calibracao'), ('aguardando_padrao_disponivel', 'Aguardando padrao disponivel (RBC cl. 6.3)'), ('em_calibracao', 'Em calibracao'), ('aguardando_aprovacao_tecnica', 'Aguardando aprovacao tecnica'), ('aguardando_devolucao', 'Aguardando devolucao'), ('devolvido', 'Devolvido'), ('nao_conformidade_recebimento', 'Nao conformidade no recebimento (CAPA)'), ('nao_conformidade_calibracao', 'Nao conformidade na calibracao (CAPA)')], default='recebido_pendente_inspecao', help_text='9 fases + 2 alternativos (AC-EQP-006-3b). Trigger PG `transicao_status_fluxo_lab` valida + estados terminais bloqueiam UPDATE.', max_length=40)),
                ('data_recebimento', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('equipamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimentos', to='equipamentos.equipamento')),
                ('recebido_por', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimentos_registrados', to=settings.AUTH_USER_MODEL)),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimentos_equipamento', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Recebimento de equipamento',
                'verbose_name_plural': 'Recebimentos de equipamentos',
                'db_table': 'equipamentos_recebimento',
                'ordering': ['-data_recebimento'],
            },
        ),
        migrations.CreateModel(
            name='EquipamentoRecebimentoFoto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('storage_key', models.CharField(help_text='UUID opaco — bate com `EquipamentoRecebimento.foto_storage_key`.', max_length=64, unique=True)),
                ('conteudo_bytes', models.BinaryField(help_text='Binario JPEG/PNG pos-EXIF-strip. Marco 2: ≤5MB inline; Wave A migra pra B2 (GATE-EQP-2) — campo permanece como fallback ou e dropado depois da migracao.')),
                ('mime_type', models.CharField(help_text='image/jpeg ou image/png (validado no service).', max_length=30)),
                ('tamanho_bytes', models.PositiveIntegerField()),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('recebimento', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='foto', to='equipamentos.equipamentorecebimento')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='recebimento_fotos', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Foto de recebimento',
                'verbose_name_plural': 'Fotos de recebimentos',
                'db_table': 'equipamentos_recebimento_foto',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.AddIndex(
            model_name='equipamentorecebimento',
            index=models.Index(fields=['tenant', 'equipamento', '-data_recebimento'], name='equipamento_tenant__1d5242_idx'),
        ),
        migrations.AddIndex(
            model_name='equipamentorecebimento',
            index=models.Index(fields=['tenant', 'status_fluxo_lab'], name='equipamento_tenant__9d6853_idx'),
        ),
        migrations.AddConstraint(
            model_name='equipamentorecebimento',
            constraint=models.CheckConstraint(condition=models.Q(('condicao_visual_chegada', 'integro'), models.Q(models.Q(('condicao_visual_chegada', 'integro'), _negated=True), models.Q(('decisao_apos_anomalia', ''), _negated=True), models.Q(('justificativa_decisao', ''), _negated=True)), _connector='OR'), name='ck_recebimento_anomalia_exige_decisao'),
        ),
        migrations.AddConstraint(
            model_name='equipamentorecebimento',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('foto_storage_key', ''), ('foto_sha256', '')), models.Q(models.Q(('foto_storage_key', ''), _negated=True), models.Q(('foto_sha256', ''), _negated=True)), _connector='OR'), name='ck_recebimento_foto_storage_e_sha_all_or_nothing'),
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
    ]
