# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-005 (Sprint 1)
# AC-SAN-PERFIL-001-1c — 3º step do 3-step T1:
#   ADD NULL (0003) -> backfill (0004) -> SET NOT NULL + CHECK (este).
# Decisao T8 do plan.md: CHAR(1) + CHECK constraint (nao usa PG ENUM type).
# Enum de dominio em src/domain/tenant/enums.py e fonte da verdade.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0004_perfil_regulatorio_backfill"),
    ]

    operations = [
        # 1. Tornar coluna NOT NULL agora que backfill da migration 0004 garantiu
        #    que nao existe linha com NULL.
        migrations.AlterField(
            model_name="tenant",
            name="perfil_regulatorio",
            field=models.CharField(
                max_length=1,
                null=False,
                blank=False,
                choices=[
                    ("A", "A — Acreditado RBC/CGCRE"),
                    ("B", "B — Rastreavel nao-acreditado"),
                    ("C", "C — Em preparacao para acreditar (trilha D→A)"),
                    ("D", "D — Comercial puro (sem ISO 17025)"),
                ],
                help_text=(
                    "Perfil regulatorio do tenant (ADR-0067). NOT NULL pos-backfill. "
                    "Mutavel APENAS via funcoes SECURITY DEFINER "
                    "aplicar_evento_cgcre() ou rebaixar_perfil_tenant_voluntario_cliente()."
                ),
            ),
        ),
        # 2. CHECK constraint defensivo a nivel de banco — Django CharField + choices
        #    valida apenas em form/clean; CHECK protege contra INSERT/UPDATE direto SQL.
        migrations.RunSQL(
            sql=(
                "ALTER TABLE tenants "
                "ADD CONSTRAINT tenants_perfil_regulatorio_check "
                "CHECK (perfil_regulatorio IN ('A','B','C','D'));"
            ),
            reverse_sql=(
                "ALTER TABLE tenants "
                "DROP CONSTRAINT IF EXISTS tenants_perfil_regulatorio_check;"
            ),
        ),
    ]
