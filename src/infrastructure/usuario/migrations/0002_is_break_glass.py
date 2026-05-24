"""Adiciona Usuario.is_break_glass — F-C1 P4 T-FC1-13 (US-FC1-006).

Conta admin-recovery (acesso emergencial pos-MFA perdido). Detectada pelo
AdminHardeningMiddleware (T-FC1-04) via getattr(user, 'is_break_glass',
False) — bypassa IP allowlist (permitido de qualquer IP, mas dispara
alerta critico em todo login).

INV-ADMIN-003 (cravado em REGRAS pelo P3 retrofit). Procedimento operacional
em runbook.md §11.bis.

# rls-policy: external 0002 -- Usuario nao tem RLS por design (cross-tenant
# por natureza — pessoa pertence a N tenants via UsuarioPerfilTenant).
# Campo is_break_glass eh visivel a todas as queries; rate de break-glass
# accounts deve ser <=2 por instalacao (Roldao + DPO formal Wave A).
"""

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("usuario", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="usuario",
            name="is_break_glass",
            field=models.BooleanField(default=False),
        ),
    ]
