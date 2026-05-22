"""T-EQP-051 — tabela `equipamentos_devolucao_foto` (BYTEA inline
Marco 2 dogfooding; Wave A: B2 GATE-EQP-2) + RLS pattern v2.

Tabela paralela a `equipamentos_recebimento_foto` (OneToOne com
recebimento) — a devolucao precisa de foto INDEPENDENTE pra registrar
estado fisico na SAIDA (RAT-EQP-FOTO bilateral).

# tests-coverage: tests/test_equipamentos_devolver_t_eqp_051.py
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models

RLS_FORWARD = """
ALTER TABLE equipamentos_devolucao_foto ENABLE ROW LEVEL SECURITY;
ALTER TABLE equipamentos_devolucao_foto FORCE ROW LEVEL SECURITY;

CREATE POLICY equipamentos_devolucao_foto_tenant_isolation_select ON equipamentos_devolucao_foto
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_foto_tenant_isolation_update ON equipamentos_devolucao_foto
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_foto_tenant_isolation_delete ON equipamentos_devolucao_foto
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY equipamentos_devolucao_foto_tenant_isolation_insert ON equipamentos_devolucao_foto
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);
"""

RLS_REVERSE = """
DROP POLICY IF EXISTS equipamentos_devolucao_foto_tenant_isolation_insert ON equipamentos_devolucao_foto;
DROP POLICY IF EXISTS equipamentos_devolucao_foto_tenant_isolation_delete ON equipamentos_devolucao_foto;
DROP POLICY IF EXISTS equipamentos_devolucao_foto_tenant_isolation_update ON equipamentos_devolucao_foto;
DROP POLICY IF EXISTS equipamentos_devolucao_foto_tenant_isolation_select ON equipamentos_devolucao_foto;
ALTER TABLE equipamentos_devolucao_foto DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ('equipamentos', '0021_equipamentodevolucao'),
        ('tenant', '0002_tenant_bloqueio_automatico_inadimplencia_habilitado'),
    ]

    operations = [
        migrations.CreateModel(
            name='EquipamentoDevolucaoFoto',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('storage_key', models.CharField(help_text='UUID opaco — bate com `EquipamentoDevolucao.foto_storage_key`.', max_length=64, unique=True)),
                ('conteudo_bytes', models.BinaryField()),
                ('mime_type', models.CharField(max_length=30)),
                ('tamanho_bytes', models.PositiveIntegerField()),
                ('criado_em', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('devolucao', models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name='foto', to='equipamentos.equipamentodevolucao')),
                ('tenant', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='devolucao_fotos', to='tenant.tenant')),
            ],
            options={
                'verbose_name': 'Foto de devolucao',
                'verbose_name_plural': 'Fotos de devolucoes',
                'db_table': 'equipamentos_devolucao_foto',
                'ordering': ['-criado_em'],
            },
        ),
        migrations.RunSQL(sql=RLS_FORWARD, reverse_sql=RLS_REVERSE),
    ]
