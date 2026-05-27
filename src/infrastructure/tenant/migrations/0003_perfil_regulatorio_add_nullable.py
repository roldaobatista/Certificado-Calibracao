# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-003 (Sprint 1)
# AC-SAN-PERFIL-001-1a — 1º step do 3-step T1 do plan.md:
#   ADD COLUMN NULL (este) → backfill RunPython (0004) → SET NOT NULL + CHECK (0005)
# Idempotente: re-run no-op porque add_field é idempotente em Django.
# Falha de step posterior preserva sistema operável em estado degraded.

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tenant", "0002_tenant_bloqueio_automatico_inadimplencia_habilitado"),
    ]

    operations = [
        migrations.AddField(
            model_name="tenant",
            name="perfil_regulatorio",
            field=models.CharField(
                max_length=1,
                null=True,
                blank=True,
                choices=[
                    ("A", "A — Acreditado RBC/CGCRE"),
                    ("B", "B — Rastreável não-acreditado"),
                    ("C", "C — Em preparação para acreditar (trilha D→A)"),
                    ("D", "D — Comercial puro (sem ISO 17025)"),
                ],
                help_text=(
                    "Perfil regulatorio do tenant (ADR-0067). NULL apenas durante "
                    "janela de backfill (migrations 0003 -> 0004 -> 0005). "
                    "Apos migration 0005, NOT NULL + CHECK. "
                    "Mutavel APENAS via funcoes SECURITY DEFINER "
                    "aplicar_evento_cgcre() ou rebaixar_perfil_tenant_voluntario_cliente()."
                ),
            ),
        ),
    ]
