"""US-CLI-003: campos LGPD novos no Cliente + tabela `cliente_importacao_declaracoes`.

Endereca:
- R2 advogado (BLOQUEANTE): `aceite_lgpd_base_legal` + `aceite_lgpd_evidencia_externa`
- R1 advogado (BLOQUEANTE): `aceite_lgpd_pendente` (PJ-com-PF caminho 3)
- R8 advogado (ALTA): `cpf_responsavel_legal`
- R6 advogado (BLOQUEANTE): tabela `ClienteImportacaoDeclaracao`

RLS pattern v2 aplicado na nova tabela (INV-TENANT-001/002/003). CHECK
constraints nos enums (espelha padrao de bloqueio).
"""

# tests-coverage: tests/test_clientes_us_cli_003_importar.py

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models


RLS_DECLARACAO = """
ALTER TABLE cliente_importacao_declaracoes ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente_importacao_declaracoes FORCE ROW LEVEL SECURITY;

CREATE POLICY cli_imp_decl_tenant_iso_select ON cliente_importacao_declaracoes
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY cli_imp_decl_tenant_iso_insert ON cliente_importacao_declaracoes
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

CREATE POLICY cli_imp_decl_tenant_iso_update ON cliente_importacao_declaracoes
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY cli_imp_decl_tenant_iso_delete ON cliente_importacao_declaracoes
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));
"""

RLS_DECLARACAO_REVERSE = """
DROP POLICY IF EXISTS cli_imp_decl_tenant_iso_delete ON cliente_importacao_declaracoes;
DROP POLICY IF EXISTS cli_imp_decl_tenant_iso_update ON cliente_importacao_declaracoes;
DROP POLICY IF EXISTS cli_imp_decl_tenant_iso_insert ON cliente_importacao_declaracoes;
DROP POLICY IF EXISTS cli_imp_decl_tenant_iso_select ON cliente_importacao_declaracoes;
ALTER TABLE cliente_importacao_declaracoes DISABLE ROW LEVEL SECURITY;
"""


# CHECK constraints pros enums (R5 tech-lead — espelha padrao de bloqueio).
CHECKS = """
ALTER TABLE clientes
    ADD CONSTRAINT ck_cliente_base_legal CHECK (
        aceite_lgpd_base_legal = '' OR aceite_lgpd_base_legal IN ('art_7_v', 'art_7_i')
    );

ALTER TABLE cliente_importacao_declaracoes
    ADD CONSTRAINT ck_imp_decl_pf_origem CHECK (
        pf_aceite_origem = '' OR pf_aceite_origem IN (
            'contrato_preexistente_documentado',
            'consentimento_coletado_offline',
            'migracao_sistema_anterior_com_aceite'
        )
    );
"""

CHECKS_REVERSE = """
ALTER TABLE cliente_importacao_declaracoes DROP CONSTRAINT IF EXISTS ck_imp_decl_pf_origem;
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_base_legal;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("clientes", "0011_seed_authz_visao360"),
        ("tenant", "0002_tenant_bloqueio_automatico_inadimplencia_habilitado"),
    ]

    operations = [
        migrations.AddField(
            model_name="cliente",
            name="aceite_lgpd_base_legal",
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name="cliente",
            name="aceite_lgpd_evidencia_externa",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="cliente",
            name="aceite_lgpd_pendente",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="cliente",
            name="cpf_responsavel_legal",
            field=models.CharField(blank=True, max_length=11),
        ),
        migrations.CreateModel(
            name="ClienteImportacaoDeclaracao",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("usuario_id", models.UUIDField(blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("arquivo_hash", models.CharField(max_length=64)),
                ("arquivo_tamanho_bytes", models.PositiveIntegerField()),
                ("tem_base_legal", models.BooleanField()),
                ("compromisso_comunicar_titulares", models.BooleanField()),
                ("declara_sem_dados_sensiveis", models.BooleanField()),
                ("procedencia_declarada", models.CharField(max_length=200)),
                ("pf_aceite_origem", models.CharField(blank=True, max_length=40)),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="importacao_declaracoes",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Declaracao de procedencia (importacao)",
                "verbose_name_plural": "Declaracoes de procedencia",
                "db_table": "cliente_importacao_declaracoes",
                "ordering": ["-criado_em"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "-criado_em"],
                        name="ix_imp_decl_tenant_ts",
                    ),
                    models.Index(
                        fields=["tenant", "arquivo_hash"],
                        name="ix_imp_decl_tenant_hash",
                    ),
                ],
            },
        ),
        migrations.RunSQL(sql=RLS_DECLARACAO, reverse_sql=RLS_DECLARACAO_REVERSE),
        migrations.RunSQL(sql=CHECKS, reverse_sql=CHECKS_REVERSE),
    ]
