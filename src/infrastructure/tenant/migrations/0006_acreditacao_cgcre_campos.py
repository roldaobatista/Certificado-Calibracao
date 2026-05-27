# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-006 (Sprint 1)
# AC-SAN-PERFIL-001-1d — campos auxiliares de acreditacao CGCRE:
#   - acreditacao_cgcre_numero (cache do numero RBC principal — display)
#   - acreditacao_suspensa_em / acreditacao_suspensa_ate (suspensao temporaria NIT-DICLA-005)
#   - ilac_mra_aderido (R9 plan.md — ILAC-MRA nao e universal)
#
# Vigencia POR ESCOPO (grandeza × faixa × CMC × vigencia) NAO entra aqui (R1):
# migra para modulo `licencas-acreditacoes` Wave A.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0005_perfil_regulatorio_not_null"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="acreditacao_cgcre_numero",
            field=models.CharField(
                max_length=20,
                null=True,
                blank=True,
                help_text=(
                    "Numero RBC formato 'CRL NNNN' ou 'CRL NNNN-NN' (filial). "
                    "Preenchido apenas quando perfil_regulatorio='A'. "
                    "Validacao regex em Tenant.clean(). Cache do principal — "
                    "fonte da verdade granular (por escopo) e modulo licencas-acreditacoes "
                    "Wave A (R1 plan.md)."
                ),
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="acreditacao_suspensa_em",
            field=models.DateField(
                null=True,
                blank=True,
                help_text=(
                    "Data inicio da suspensao temporaria CGCRE (NIT-DICLA-005 §7.4). "
                    "Preserva perfil_regulatorio='A' mas predicate tenant_perfil_e({'A'}) "
                    "retorna False enquanto today < acreditacao_suspensa_ate. "
                    "Lab pode reabilitar sem nova auditoria CGCRE."
                ),
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="acreditacao_suspensa_ate",
            field=models.DateField(
                null=True,
                blank=True,
                help_text=(
                    "Data prevista de fim da suspensao temporaria CGCRE. "
                    "Apos esta data, predicate volta a aceitar perfil A. "
                    "Cancelamento definitivo (vs suspensao) usa direcao=CANCELAMENTO_CGCRE."
                ),
            ),
        ),
        migrations.AddField(
            model_name="tenant",
            name="ilac_mra_aderido",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Se True, lab esta no ILAC-MRA (reconhecimento internacional). "
                    "Template de certificado A com selo ILAC-MRA so e permitido se True. "
                    "Hook template-ilac-mra-coerencia (Wave A Sprint 5) valida. "
                    "R9 do plan.md — ILAC-MRA nao e universal entre labs A."
                ),
            ),
        ),
        # CHECK constraints de coerencia:
        # 1. acreditacao_cgcre_numero so faz sentido quando perfil='A'.
        # 2. Janela de suspensao deve ter ate >= em.
        # 3. ilac_mra_aderido so pode ser True quando perfil='A'.
        migrations.RunSQL(
            sql="""
                ALTER TABLE tenants
                ADD CONSTRAINT tenants_acreditacao_numero_so_perfil_a_check
                CHECK (
                    acreditacao_cgcre_numero IS NULL
                    OR perfil_regulatorio = 'A'
                );
                ALTER TABLE tenants
                ADD CONSTRAINT tenants_suspensao_janela_valida_check
                CHECK (
                    acreditacao_suspensa_em IS NULL
                    OR acreditacao_suspensa_ate IS NULL
                    OR acreditacao_suspensa_ate >= acreditacao_suspensa_em
                );
                ALTER TABLE tenants
                ADD CONSTRAINT tenants_ilac_mra_so_perfil_a_check
                CHECK (
                    ilac_mra_aderido = FALSE
                    OR perfil_regulatorio = 'A'
                );
            """,
            reverse_sql="""
                ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_acreditacao_numero_so_perfil_a_check;
                ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_suspensao_janela_valida_check;
                ALTER TABLE tenants DROP CONSTRAINT IF EXISTS tenants_ilac_mra_so_perfil_a_check;
            """,
        ),
    ]
