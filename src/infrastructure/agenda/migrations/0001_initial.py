# T-AGE-022 — frente agenda schema inicial (7 tabelas achatadas).
#
# Tabelas:
#   evento_agenda, recorrencia_agenda, registro_no_show, capacidade_tecnico,
#   feriado, evento_auditoria_agenda, regime_jornada_colaborador
#
# CHECK:
#   chk_agenda_evento_atividade_obrigatoria_quando_os:
#     tipo != 'os' OR atividade_id IS NOT NULL (INV-AG-ATIVIDADE-001 / D-AGE-2)
#
# UNIQUE:
#   uq_agenda_evento_recorrencia_ocorrencia:
#     (recorrencia_id, ocorrencia_dt) WHERE recorrencia_id IS NOT NULL (INV-AG-RECORRENCIA-001 / R10)
#   uq_agenda_feriado_nacional_data:
#     data WHERE nacional=True AND tenant IS NULL (seed idempotente)
#
# Índices:
#   ag_evento_tenant_tec_inicia_idx: (tenant_id, tecnico_id, inicia_at) — R14 grade/overlap
#
# RLS policies = migration-irmã 0002_rls_policies (ADR-0002 §6 pattern v2).
# EXCLUDE GIST de overlap = 0003_exclusion_overlap (R1/R12).
# Triggers WORM INSERT-only = 0004_triggers_worm.
# GRANT app_user = 0005. Seed authz = 0006. Seed feriados = 0007.
#
# rls-policy: external 0002_rls_policies

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenant", "0012_aplicar_evento_cgcre_vigencia"),
    ]

    operations = [
        migrations.CreateModel(
            name="EventoAgenda",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos_agenda",
                        to="tenant.tenant",
                    ),
                ),
                (
                    "tecnico_id",
                    models.UUIDField(
                        help_text="Colaborador alocado (FK lógica — colaboradores FECHADO).",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("os", "os"),
                            ("bloqueio", "bloqueio"),
                            ("descanso_legal", "descanso_legal"),
                            ("deslocamento", "deslocamento"),
                            ("almoco", "almoco"),
                            ("manutencao_interna", "manutencao_interna"),
                            ("feriado", "feriado"),
                        ],
                        max_length=30,
                    ),
                ),
                (
                    "estado",
                    models.CharField(
                        choices=[
                            ("agendado", "agendado"),
                            ("em_execucao", "em_execucao"),
                            ("concluido", "concluido"),
                            ("cancelado", "cancelado"),
                            ("no_show", "no_show"),
                        ],
                        max_length=20,
                    ),
                ),
                ("inicia_at", models.DateTimeField()),
                ("termina_at", models.DateTimeField()),
                ("aloca_em_umc", models.BooleanField(default=False)),
                ("criado_por_usuario_id", models.UUIDField()),
                (
                    "atividade_id",
                    models.UUIDField(
                        blank=True,
                        null=True,
                        help_text="NOT NULL quando tipo='os' (CHECK — INV-AG-ATIVIDADE-001).",
                    ),
                ),
                ("os_id", models.UUIDField(blank=True, null=True)),
                (
                    "motivo_bloqueio",
                    models.CharField(
                        blank=True,
                        default="",
                        choices=[
                            ("ferias", "ferias"),
                            ("treinamento", "treinamento"),
                            ("atestado", "atestado"),
                            ("outro", "outro"),
                        ],
                        max_length=20,
                    ),
                ),
                ("descricao_publica", models.TextField(blank=True, default="")),
                ("recorrencia_id", models.UUIDField(blank=True, null=True)),
                ("ocorrencia_dt", models.DateTimeField(blank=True, null=True)),
                ("confirmar_feriado", models.BooleanField(default=False)),
                ("revision", models.IntegerField(default=0)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "evento_agenda",
                "verbose_name": "Evento de Agenda",
                "verbose_name_plural": "Eventos de Agenda",
                "ordering": ["inicia_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="EventoAgenda",
            constraint=models.CheckConstraint(
                condition=(~models.Q(tipo="os") | models.Q(atividade_id__isnull=False)),
                name="chk_agenda_evento_atividade_obrigatoria_quando_os",
            ),
        ),
        migrations.AddConstraint(
            model_name="EventoAgenda",
            constraint=models.UniqueConstraint(
                fields=["recorrencia_id", "ocorrencia_dt"],
                condition=models.Q(recorrencia_id__isnull=False),
                name="uq_agenda_evento_recorrencia_ocorrencia",
            ),
        ),
        migrations.AddIndex(
            model_name="EventoAgenda",
            index=models.Index(
                fields=["tenant", "tecnico_id", "inicia_at"],
                name="ag_evt_tec_inicia_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="EventoAgenda",
            index=models.Index(
                fields=["tenant", "estado"],
                name="ag_evt_tenant_estado_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="EventoAgenda",
            index=models.Index(
                fields=["tenant", "atividade_id"],
                name="ag_evt_tenant_ativ_idx",
            ),
        ),
        migrations.CreateModel(
            name="RecorrenciaAgenda",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="recorrencias_agenda",
                        to="tenant.tenant",
                    ),
                ),
                ("tecnico_id", models.UUIDField()),
                ("rrule_str", models.TextField()),
                ("inicia_em", models.DateTimeField()),
                ("duracao_minutos", models.IntegerField()),
                ("ativo", models.BooleanField(default=True)),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("os", "os"),
                            ("bloqueio", "bloqueio"),
                            ("descanso_legal", "descanso_legal"),
                            ("deslocamento", "deslocamento"),
                            ("almoco", "almoco"),
                            ("manutencao_interna", "manutencao_interna"),
                            ("feriado", "feriado"),
                        ],
                        max_length=30,
                    ),
                ),
                ("criado_por_usuario_id", models.UUIDField()),
                ("atividade_id", models.UUIDField(blank=True, null=True)),
                ("os_id", models.UUIDField(blank=True, null=True)),
                ("aloca_em_umc", models.BooleanField(default=False)),
                ("revision", models.IntegerField(default=0)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "recorrencia_agenda",
                "verbose_name": "Recorrência de Agenda",
                "verbose_name_plural": "Recorrências de Agenda",
                "ordering": ["-criado_em"],
            },
        ),
        migrations.AddIndex(
            model_name="RecorrenciaAgenda",
            index=models.Index(
                fields=["tenant", "tecnico_id"],
                name="ag_rec_tenant_tec_idx",
            ),
        ),
        migrations.CreateModel(
            name="RegistroNoShow",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="registros_no_show",
                        to="tenant.tenant",
                    ),
                ),
                ("evento_id", models.UUIDField()),
                ("tecnico_id", models.UUIDField()),
                ("ocorrido_em", models.DateTimeField()),
                ("custo_estimado", models.DecimalField(decimal_places=2, max_digits=10)),
                ("cobrar_cliente", models.BooleanField(default=False)),
                ("registrado_por_usuario_id", models.UUIDField()),
                ("observacao", models.TextField(blank=True, default="")),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "registro_no_show",
                "verbose_name": "Registro de No-Show",
                "verbose_name_plural": "Registros de No-Show",
                "ordering": ["-criado_em"],
            },
        ),
        migrations.AddIndex(
            model_name="RegistroNoShow",
            index=models.Index(
                fields=["tenant", "evento_id"],
                name="ag_nsh_tenant_evento_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="RegistroNoShow",
            index=models.Index(
                fields=["tenant", "tecnico_id"],
                name="ag_nsh_tenant_tec_idx",
            ),
        ),
        migrations.CreateModel(
            name="CapacidadeTecnico",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="capacidades_tecnico",
                        to="tenant.tenant",
                    ),
                ),
                ("colaborador_id", models.UUIDField()),
                ("horas_uteis_dia", models.IntegerField(default=8)),
                ("dias_trabalho", models.IntegerField(default=31)),
                ("hora_inicio", models.IntegerField(default=8)),
                ("hora_fim", models.IntegerField(default=17)),
                ("vigencia_inicio", models.DateField()),
                ("vigencia_fim", models.DateField(blank=True, null=True)),
                ("criado_por_usuario_id", models.UUIDField()),
                ("revision", models.IntegerField(default=0)),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "db_table": "capacidade_tecnico",
                "verbose_name": "Capacidade de Técnico",
                "verbose_name_plural": "Capacidades de Técnico",
                "ordering": ["-vigencia_inicio"],
            },
        ),
        migrations.AddIndex(
            model_name="CapacidadeTecnico",
            index=models.Index(
                fields=["tenant", "colaborador_id", "vigencia_inicio"],
                name="ag_cap_tenant_col_idx",
            ),
        ),
        migrations.CreateModel(
            name="Feriado",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="feriados_custom",
                        to="tenant.tenant",
                        null=True,
                        blank=True,
                    ),
                ),
                ("data", models.DateField()),
                ("descricao", models.CharField(max_length=200)),
                ("nacional", models.BooleanField(default=True)),
                ("ativo", models.BooleanField(default=True)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "feriado",
                "verbose_name": "Feriado",
                "verbose_name_plural": "Feriados",
                "ordering": ["data"],
            },
        ),
        migrations.AddConstraint(
            model_name="Feriado",
            constraint=models.UniqueConstraint(
                fields=["data"],
                condition=models.Q(nacional=True, tenant__isnull=True),
                name="uq_agenda_feriado_nacional_data",
            ),
        ),
        migrations.AddIndex(
            model_name="Feriado",
            index=models.Index(
                fields=["data", "nacional"],
                name="ag_fer_data_nacional_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="Feriado",
            index=models.Index(
                fields=["tenant", "data"],
                name="ag_fer_tenant_data_idx",
            ),
        ),
        migrations.CreateModel(
            name="EventoAuditoriaAgenda",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="eventos_auditoria_agenda",
                        to="tenant.tenant",
                    ),
                ),
                ("evento_id", models.UUIDField(db_index=True)),
                (
                    "acao",
                    models.CharField(
                        choices=[
                            ("criado", "criado"),
                            ("movido", "movido"),
                            ("reagendado", "reagendado"),
                            ("bloqueado", "bloqueado"),
                            ("cancelado", "cancelado"),
                            ("aprovado", "aprovado"),
                            ("no_show", "no_show"),
                            ("regime_indeterminado", "regime_indeterminado"),
                        ],
                        max_length=30,
                    ),
                ),
                ("actor_usuario_id", models.UUIDField(blank=True, null=True)),
                ("occurred_at", models.DateTimeField()),
                ("payload_resumo", models.TextField(blank=True, default="")),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "evento_auditoria_agenda",
                "verbose_name": "Evento de Auditoria da Agenda",
                "verbose_name_plural": "Eventos de Auditoria da Agenda",
                "ordering": ["criado_em"],
            },
        ),
        migrations.AddIndex(
            model_name="EventoAuditoriaAgenda",
            index=models.Index(
                fields=["tenant", "evento_id"],
                name="ag_aud_tenant_evento_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="EventoAuditoriaAgenda",
            index=models.Index(
                fields=["tenant", "criado_em"],
                name="ag_aud_tenant_criado_idx",
            ),
        ),
        migrations.CreateModel(
            name="RegimeJornadaColaborador",
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
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="regimes_jornada_colaborador",
                        to="tenant.tenant",
                    ),
                ),
                ("colaborador_id", models.UUIDField()),
                (
                    "regime",
                    models.CharField(
                        choices=[
                            ("motorista_profissional", "motorista_profissional"),
                            ("clt_geral", "clt_geral"),
                            ("nao_aplica", "nao_aplica"),
                        ],
                        max_length=30,
                    ),
                ),
                ("vigencia_inicio", models.DateField()),
                ("vigencia_fim", models.DateField(blank=True, null=True)),
                ("definido_por_usuario_id", models.UUIDField()),
                (
                    "fonte",
                    models.CharField(
                        choices=[
                            ("override_humano", "override_humano"),
                            ("derivado_papel", "derivado_papel"),
                            ("indeterminado", "indeterminado"),
                        ],
                        default="override_humano",
                        max_length=20,
                    ),
                ),
                ("justificativa", models.TextField(blank=True, default="")),
                ("criado_em", models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                "db_table": "regime_jornada_colaborador",
                "verbose_name": "Regime de Jornada de Colaborador",
                "verbose_name_plural": "Regimes de Jornada de Colaborador",
                "ordering": ["-vigencia_inicio"],
            },
        ),
        migrations.AddIndex(
            model_name="RegimeJornadaColaborador",
            index=models.Index(
                fields=["tenant", "colaborador_id", "vigencia_inicio"],
                name="ag_reg_tenant_col_idx",
            ),
        ),
    ]
