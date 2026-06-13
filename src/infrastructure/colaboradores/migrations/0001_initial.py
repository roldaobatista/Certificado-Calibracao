"""T-COL-021 — CreateModel ×5 + índices parciais + CHECKs (frente colaboradores).

Tabelas criadas:
  - catalogo_habilidade: PK textual, SEM tenant_id, SEM RLS (global read-only).
  - colaborador: agregado raiz com soft-delete Padrão C + desligamento de negócio.
  - colaborador_papel: vigência solta (data_inicio/data_fim/revogado_em).
  - colaborador_habilidade: catalogo FK nullable XOR descricao_livre.
  - colaborador_documento: armazenamento externo (storage_key + sha256).

Índices/CHECKs via RunSQL (Django ORM não suporta estas construções PG nativamente):
  - uq_col_cpf_ativo: UNIQUE INDEX parcial (tenant_id, cpf) WHERE deletado_em IS NULL.
  - uq_col_papel_dono_unico: UNIQUE INDEX parcial (tenant_id) WHERE papel='dono'
      AND data_fim IS NULL AND revogado_em IS NULL.
  - ck_col_comissao_range: CHECK comissao_default_pct BETWEEN 0 AND 100.
  - ck_col_hab_xor: CHECK (catalogo_id IS NOT NULL XOR descricao_livre IS NOT NULL).

# rls-policy: external 0002_rls_policies
# audit-immutability: skip -- CreateModel puro; colaboradores não são WORM
# tests-coverage: tests/test_colaboradores_schema_fatia1b.py +
#   management/commands/validar_colaboradores.py
"""

import uuid

import django.db.models.deletion
from django.db import migrations, models

SQL_FORWARD = """
-- Índice parcial CPF único por tenant (não-deletados).
-- Permite re-cadastro após soft-delete (deletado_em NOT NULL fica fora do índice).
CREATE UNIQUE INDEX uq_col_cpf_ativo
    ON colaborador (tenant_id, cpf)
    WHERE deletado_em IS NULL;

-- Índice parcial DONO único por tenant ativo.
-- Garante INV-COL-DONO-UNICO: só um papel DONO ativo por tenant.
CREATE UNIQUE INDEX uq_col_papel_dono_unico
    ON colaborador_papel (tenant_id)
    WHERE papel = 'dono'
      AND data_fim IS NULL
      AND revogado_em IS NULL;

-- CHECK comissão 0..100.
ALTER TABLE colaborador
    ADD CONSTRAINT ck_col_comissao_range
    CHECK (comissao_default_pct >= 0 AND comissao_default_pct <= 100);

-- CHECK habilidade XOR: exatamente um entre catalogo_id e descricao_livre deve ser NOT NULL.
ALTER TABLE colaborador_habilidade
    ADD CONSTRAINT ck_col_hab_xor
    CHECK (
        (catalogo_id IS NOT NULL AND descricao_livre IS NULL)
        OR
        (catalogo_id IS NULL AND descricao_livre IS NOT NULL)
    );
"""

SQL_REVERSE = """
ALTER TABLE colaborador_habilidade DROP CONSTRAINT IF EXISTS ck_col_hab_xor;
ALTER TABLE colaborador DROP CONSTRAINT IF EXISTS ck_col_comissao_range;
DROP INDEX IF EXISTS uq_col_papel_dono_unico;
DROP INDEX IF EXISTS uq_col_cpf_ativo;
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("tenant", "0012_aplicar_evento_cgcre_vigencia"),
    ]

    operations = [
        # ------------------------------------------------------------------
        # catalogo_habilidade — global, SEM tenant_id, SEM RLS (TL-COL-10)
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="CatalogoHabilidade",
            fields=[
                (
                    "codigo",
                    models.CharField(
                        primary_key=True,
                        serialize=False,
                        max_length=60,
                        help_text="Código canônico da habilidade (ex: 'massa', 'temperatura').",
                    ),
                ),
                (
                    "descricao",
                    models.CharField(
                        max_length=300,
                        help_text="Descrição humana da habilidade.",
                    ),
                ),
                (
                    "grandeza",
                    models.CharField(
                        max_length=60,
                        blank=True,
                        null=True,
                        help_text="Grandeza metrológica associada; None para habilidades gerais.",
                    ),
                ),
            ],
            options={
                "db_table": "catalogo_habilidade",
            },
        ),
        # ------------------------------------------------------------------
        # colaborador — agregado raiz
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="Colaborador",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        to="tenant.tenant",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colaboradores",
                    ),
                ),
                ("nome", models.CharField(max_length=200)),
                (
                    "cpf",
                    models.CharField(
                        max_length=11,
                        help_text="CPF somente dígitos (PII — art. 5° IX LGPD).",
                    ),
                ),
                (
                    "email",
                    models.CharField(
                        max_length=254,
                        help_text="E-mail funcional/pessoal (PII — base legal vinculo).",
                    ),
                ),
                (
                    "telefone",
                    models.CharField(
                        max_length=20,
                        help_text="Telefone de contato (PII — base legal vinculo).",
                    ),
                ),
                (
                    "foto_storage_key",
                    models.CharField(
                        max_length=500,
                        blank=True,
                        null=True,
                        help_text="Chave no storage externo (sem conteúdo cru — ADV-COL-01).",
                    ),
                ),
                (
                    "usuario_id",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text=(
                            "UUID do usuário associado (opcional — D-COL-2). "
                            "SIGNATARIO EXIGE NOT NULL (INV-COL-SIGNATARIO-IDENTIDADE)."
                        ),
                    ),
                ),
                (
                    "vinculo",
                    models.CharField(
                        max_length=15,
                        choices=[
                            ("clt", "clt"),
                            ("pj", "pj"),
                            ("estagiario", "estagiario"),
                            ("socio", "socio"),
                            ("terceirizado", "terceirizado"),
                        ],
                        help_text="Vínculo empregatício/contratual (base legal LGPD — ADV-COL-01).",
                    ),
                ),
                ("data_admissao", models.DateField()),
                (
                    "data_desligamento",
                    models.DateField(
                        blank=True,
                        null=True,
                        help_text="Data efetiva de encerramento do vínculo (D-COL-3).",
                    ),
                ),
                (
                    "motivo_desligamento",
                    models.CharField(max_length=500, blank=True, null=True),
                ),
                (
                    "comissao_default_pct",
                    models.DecimalField(
                        max_digits=5,
                        decimal_places=2,
                        help_text="Comissão padrão em % (0..100 — CHECK ck_col_comissao_range em 0001).",
                    ),
                ),
                ("observacao", models.TextField(blank=True, default="")),
                # Soft-delete Padrão C (ADR-0031)
                ("deletado_em", models.DateTimeField(blank=True, null=True)),
                ("deletado_por_usuario_id", models.UUIDField(blank=True, null=True)),
                ("deletado_motivo", models.CharField(max_length=500, blank=True, null=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "colaborador",
            },
        ),
        # ------------------------------------------------------------------
        # colaborador_papel
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="ColaboradorPapel",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                (
                    "colaborador",
                    models.ForeignKey(
                        to="colaboradores.Colaborador",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="papeis",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        to="tenant.tenant",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colaborador_papeis",
                    ),
                ),
                (
                    "papel",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("tecnico", "tecnico"),
                            ("signatario", "signatario"),
                            ("atendente", "atendente"),
                            ("gerente", "gerente"),
                            ("dono", "dono"),
                            ("qualidade", "qualidade"),
                            ("motorista_umc", "motorista_umc"),
                        ],
                    ),
                ),
                ("data_inicio", models.DateField()),
                ("data_fim", models.DateField(blank=True, null=True)),
                ("revogado_em", models.DateTimeField(blank=True, null=True)),
                (
                    "responsabilidade_tecnica_id",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text="RTCompetencia vigente — obrigatório quando papel=SIGNATARIO (D-COL-11).",
                    ),
                ),
                (
                    "pendencia_cnh",
                    models.BooleanField(
                        default=False,
                        help_text="True quando MOTORISTA_UMC sem CNH válida (R-COL-1).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "colaborador_papel",
            },
        ),
        # ------------------------------------------------------------------
        # colaborador_habilidade
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="ColaboradorHabilidade",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                (
                    "colaborador",
                    models.ForeignKey(
                        to="colaboradores.Colaborador",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="habilidades",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        to="tenant.tenant",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colaborador_habilidades",
                    ),
                ),
                (
                    "catalogo",
                    models.ForeignKey(
                        to="colaboradores.CatalogoHabilidade",
                        on_delete=django.db.models.deletion.SET_NULL,
                        null=True,
                        blank=True,
                        related_name="habilidades",
                        help_text="Habilidade do catálogo global; None se habilidade livre (D-COL-5).",
                    ),
                ),
                (
                    "descricao_livre",
                    models.CharField(
                        max_length=300,
                        blank=True,
                        null=True,
                        help_text="Habilidade livre não catalogada; None se habilidade de catálogo.",
                    ),
                ),
                (
                    "nivel",
                    models.CharField(
                        max_length=15,
                        choices=[
                            ("aprendiz", "aprendiz"),
                            ("capacitado", "capacitado"),
                            ("mestre", "mestre"),
                        ],
                    ),
                ),
                (
                    "evidencia_url",
                    models.CharField(
                        max_length=500,
                        blank=True,
                        null=True,
                        help_text="URL do documento comprobatório (opcional).",
                    ),
                ),
                ("data_avaliacao", models.DateField()),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "colaborador_habilidade",
            },
        ),
        # ------------------------------------------------------------------
        # colaborador_documento
        # ------------------------------------------------------------------
        migrations.CreateModel(
            name="ColaboradorDocumento",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuid.uuid4,
                        editable=False,
                        serialize=False,
                    ),
                ),
                (
                    "colaborador",
                    models.ForeignKey(
                        to="colaboradores.Colaborador",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="documentos",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        to="tenant.tenant",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="colaborador_documentos",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        max_length=20,
                        choices=[
                            ("ctps", "ctps"),
                            ("cnh", "cnh"),
                            ("certificado_curso", "certificado_curso"),
                            ("outro", "outro"),
                        ],
                    ),
                ),
                (
                    "storage_key",
                    models.CharField(
                        max_length=500,
                        help_text="Chave no storage externo (sem conteúdo cru — ADV-COL-01).",
                    ),
                ),
                (
                    "sha256",
                    models.CharField(
                        max_length=64,
                        help_text="Hash SHA-256 do arquivo calculado server-side (integridade).",
                    ),
                ),
                ("data_upload", models.DateTimeField()),
                (
                    "data_validade",
                    models.DateField(
                        blank=True,
                        null=True,
                        help_text="Validade do documento (CNH, certificados com prazo).",
                    ),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "colaborador_documento",
            },
        ),
        # ------------------------------------------------------------------
        # Índices parciais + CHECKs via RunSQL
        # ------------------------------------------------------------------
        migrations.RunSQL(
            sql=SQL_FORWARD,
            reverse_sql=SQL_REVERSE,
        ),
    ]
