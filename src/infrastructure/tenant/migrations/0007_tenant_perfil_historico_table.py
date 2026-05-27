# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-007 (Sprint 1)
# AC-SAN-PERFIL-001-2 — tabela TenantPerfilHistorico append-only + trigger anti-mutacao.
#
# rls-policy: external — esta tabela e SHARED ACROSS TENANTS (padrao ADR-0002 §8,
# mesmo de `tenants` em si). NAO tem RLS propria — acesso e controlado por permissoes
# Django Admin + perfis de aplicacao (ADR-0012). RLS protege INTRA-tenant; aqui o
# escopo e cross-tenant por design (auditoria global do book regulatorio).
#
# Tambem espelha estado atual dos tenants existentes (post-backfill 0004) como
# evento PROVISIONAMENTO_INICIAL.

from __future__ import annotations

import uuid as uuidlib

from django.db import migrations, models


JUSTIFICATIVA_BACKFILL_BALANCAS = (
    "Backfill espelho do provisionamento inicial — Balancas Solution = B "
    "conforme docs/prd.md §2 + AskUserQuestion auditoria 10 lentes 2026-05-27. "
    "ADR-0067 aceita. Sem documento CGCRE porque perfil B nao exige."
)


JUSTIFICATIVA_BACKFILL_RESIDUAL = (
    "Backfill espelho do provisionamento inicial — tenant pre-saneamento sem "
    "perfil declarado recebeu D por default conservador. Corrigir via "
    "aplicar_evento_cgcre direcao=CORRECAO_ADMINISTRATIVA quando perfil real "
    "for identificado."
)


def espelhar_estado_atual_como_historico(apps, schema_editor):
    """Para cada tenant ja existente, INSERT em TenantPerfilHistorico
    direcao=PROVISIONAMENTO_INICIAL refletindo perfil cravado em 0004."""
    Tenant = apps.get_model("tenant", "Tenant")
    TenantPerfilHistorico = apps.get_model("tenant", "TenantPerfilHistorico")

    for tenant in Tenant.objects.all():
        if TenantPerfilHistorico.objects.filter(tenant_id=tenant.id).exists():
            continue
        if tenant.slug == "balancas-solution":
            motivo = JUSTIFICATIVA_BACKFILL_BALANCAS
        else:
            motivo = JUSTIFICATIVA_BACKFILL_RESIDUAL
        TenantPerfilHistorico.objects.create(
            id=uuidlib.uuid4(),
            tenant_id=tenant.id,
            perfil_anterior=None,
            perfil_novo=tenant.perfil_regulatorio,
            direcao="provisionamento_inicial",
            motivo=motivo,
            evento_origem_id=None,
            auditor_cgcre=None,
            certificado_acreditacao_documento_id=None,
            registrado_por_usuario_id=None,
            assinatura_a3_id=None,
        )


def desfazer_backfill_historico(apps, schema_editor):
    """Rollback: limpa TenantPerfilHistorico (so funciona se a tabela existe)."""
    TenantPerfilHistorico = apps.get_model("tenant", "TenantPerfilHistorico")
    TenantPerfilHistorico.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0006_acreditacao_cgcre_campos"),
    ]

    operations = [
        # 1. Criar tabela TenantPerfilHistorico.
        migrations.CreateModel(
            name="TenantPerfilHistorico",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        primary_key=True,
                        default=uuidlib.uuid4,
                        editable=False,
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        to="tenant.Tenant",
                        on_delete=models.PROTECT,
                        related_name="historico_perfil",
                        help_text="Tenant alvo da mudanca de perfil.",
                    ),
                ),
                (
                    "perfil_anterior",
                    models.CharField(
                        max_length=1,
                        null=True,
                        blank=True,
                        choices=[
                            ("A", "A"),
                            ("B", "B"),
                            ("C", "C"),
                            ("D", "D"),
                        ],
                        help_text=(
                            "Perfil antes da mudanca. NULL apenas quando "
                            "direcao=provisionamento_inicial."
                        ),
                    ),
                ),
                (
                    "perfil_novo",
                    models.CharField(
                        max_length=1,
                        choices=[
                            ("A", "A"),
                            ("B", "B"),
                            ("C", "C"),
                            ("D", "D"),
                        ],
                        help_text="Perfil apos a mudanca. NOT NULL.",
                    ),
                ),
                (
                    "direcao",
                    models.CharField(
                        max_length=40,
                        choices=[
                            ("provisionamento_inicial", "Provisionamento inicial"),
                            ("promocao_regulatoria", "Promocao regulatoria (D->C->B->A)"),
                            ("suspensao_temporaria_cgcre", "Suspensao temporaria CGCRE"),
                            ("cancelamento_cgcre", "Cancelamento CGCRE (A->B)"),
                            ("reducao_escopo_cgcre", "Reducao de escopo CGCRE"),
                            ("correcao_administrativa", "Correcao administrativa"),
                            ("rebaixamento_voluntario_cliente", "Rebaixamento voluntario do cliente"),
                        ],
                        help_text="Direcao da mudanca (ADR-0067 + plan.md R3 + A1).",
                    ),
                ),
                (
                    "motivo",
                    models.TextField(
                        help_text=(
                            "Justificativa textual da mudanca. Minimo 100 chars validado "
                            "em aplicar_evento_cgcre(). Conteudo passa por "
                            "sanitizar_payload_audit() antes do INSERT (A8 plan.md)."
                        ),
                    ),
                ),
                (
                    "evento_origem_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text=(
                            "FK opcional para evento WORM em `auditoria` ou "
                            "`licencas_acreditacoes`. NULL quando provisionamento inicial."
                        ),
                    ),
                ),
                (
                    "auditor_cgcre",
                    models.CharField(
                        max_length=200,
                        null=True,
                        blank=True,
                        help_text=(
                            "Nome do auditor CGCRE responsavel pela deliberacao. "
                            "Obrigatorio quando direcao=promocao_regulatoria E perfil_novo='A'."
                        ),
                    ),
                ),
                (
                    "certificado_acreditacao_documento_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text=(
                            "FK pra documento (PDF do certificado CGCRE). Obrigatorio "
                            "quando DirecaoMudancaPerfil.exige_documento_cgcre(direcao) "
                            "retorna True. Upload em B2 com hash SHA-256 + assinatura A3."
                        ),
                    ),
                ),
                (
                    "registrado_em",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp imutavel do INSERT.",
                    ),
                ),
                (
                    "registrado_por_usuario_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text=(
                            "FK pro usuario que disparou. NULL apenas em backfill "
                            "da migration 0007 (operador = sistema)."
                        ),
                    ),
                ),
                (
                    "assinatura_a3_id",
                    models.UUIDField(
                        null=True,
                        blank=True,
                        help_text=(
                            "FK pra assinatura A3 do operador. Obrigatoria quando "
                            "direcao=promocao_regulatoria. INV-TENANT-PERFIL-007."
                        ),
                    ),
                ),
            ],
            options={
                "db_table": "tenant_perfil_historico",
                "verbose_name": "Historico de perfil de tenant",
                "verbose_name_plural": "Historico de perfis de tenants",
                "ordering": ["-registrado_em"],
            },
        ),

        # 2. Indice de consulta por tenant + direcao.
        migrations.AddIndex(
            model_name="tenantperfilhistorico",
            index=models.Index(
                fields=["tenant", "-registrado_em"],
                name="tph_tenant_recente_idx",
            ),
        ),

        # 3. CHECK constraints de coerencia.
        migrations.RunSQL(
            sql="""
                ALTER TABLE tenant_perfil_historico
                ADD CONSTRAINT tph_perfil_anterior_null_so_provisionamento_check
                CHECK (
                    (perfil_anterior IS NULL AND direcao = 'provisionamento_inicial')
                    OR (perfil_anterior IS NOT NULL AND direcao != 'provisionamento_inicial')
                );

                ALTER TABLE tenant_perfil_historico
                ADD CONSTRAINT tph_motivo_minimo_100_chars_check
                CHECK (char_length(motivo) >= 100);

                ALTER TABLE tenant_perfil_historico
                ADD CONSTRAINT tph_a3_obrigatoria_em_promocao_check
                CHECK (
                    direcao != 'promocao_regulatoria'
                    OR assinatura_a3_id IS NOT NULL
                );

                ALTER TABLE tenant_perfil_historico
                ADD CONSTRAINT tph_documento_cgcre_obrigatorio_check
                CHECK (
                    direcao NOT IN (
                        'promocao_regulatoria',
                        'suspensao_temporaria_cgcre',
                        'cancelamento_cgcre',
                        'reducao_escopo_cgcre'
                    )
                    OR certificado_acreditacao_documento_id IS NOT NULL
                    OR direcao IN ('provisionamento_inicial', 'correcao_administrativa', 'rebaixamento_voluntario_cliente')
                );
            """,
            reverse_sql="""
                ALTER TABLE tenant_perfil_historico DROP CONSTRAINT IF EXISTS tph_perfil_anterior_null_so_provisionamento_check;
                ALTER TABLE tenant_perfil_historico DROP CONSTRAINT IF EXISTS tph_motivo_minimo_100_chars_check;
                ALTER TABLE tenant_perfil_historico DROP CONSTRAINT IF EXISTS tph_a3_obrigatoria_em_promocao_check;
                ALTER TABLE tenant_perfil_historico DROP CONSTRAINT IF EXISTS tph_documento_cgcre_obrigatorio_check;
            """,
        ),

        # 4. Trigger anti-mutacao: bloqueia UPDATE e DELETE.
        migrations.RunSQL(
            sql="""
                CREATE OR REPLACE FUNCTION tph_anti_mutation_block()
                RETURNS trigger AS $$
                BEGIN
                    IF TG_OP = 'UPDATE' THEN
                        RAISE EXCEPTION 'TenantPerfilHistorico e append-only — UPDATE proibido (INV-TENANT-PERFIL-002).';
                    END IF;
                    IF TG_OP = 'DELETE' THEN
                        RAISE EXCEPTION 'TenantPerfilHistorico e append-only — DELETE proibido (INV-TENANT-PERFIL-002).';
                    END IF;
                    RETURN NULL;
                END;
                $$ LANGUAGE plpgsql;

                CREATE TRIGGER tph_anti_update_trigger
                BEFORE UPDATE ON tenant_perfil_historico
                FOR EACH ROW
                EXECUTE FUNCTION tph_anti_mutation_block();

                CREATE TRIGGER tph_anti_delete_trigger
                BEFORE DELETE ON tenant_perfil_historico
                FOR EACH ROW
                EXECUTE FUNCTION tph_anti_mutation_block();
            """,
            reverse_sql="""
                DROP TRIGGER IF EXISTS tph_anti_update_trigger ON tenant_perfil_historico;
                DROP TRIGGER IF EXISTS tph_anti_delete_trigger ON tenant_perfil_historico;
                DROP FUNCTION IF EXISTS tph_anti_mutation_block();
            """,
        ),

        # 5. Backfill espelho do estado atual (PROVISIONAMENTO_INICIAL).
        migrations.RunPython(
            espelhar_estado_atual_como_historico,
            reverse_code=desfazer_backfill_historico,
            elidable=False,
        ),
    ]
