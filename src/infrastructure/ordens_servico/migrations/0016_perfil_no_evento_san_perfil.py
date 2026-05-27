# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-043 (Sprint 4)
# AC-SAN-PERFIL-003-1 + INV-TENANT-PERFIL-003:
#
# evento_de_os ganha perfil_no_evento NULLABLE + trigger BEFORE INSERT
# (mesmo padrao audit/0019 e calibracao/0015).
#
# tenant-perfil-imutavel: skip -- migration cria coluna + trigger snapshot canonico ADR-0067

from django.db import migrations, models


SQL_CRIA_TRIGGER = """
CREATE OR REPLACE FUNCTION evento_os_perfil_no_evento_default()
RETURNS trigger AS $$
BEGIN
    IF NEW.perfil_no_evento IS NULL THEN
        NEW.perfil_no_evento := NULLIF(current_setting('app.perfil_tenant', true), '');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER evento_os_perfil_no_evento_trigger
BEFORE INSERT ON evento_de_os
FOR EACH ROW
EXECUTE FUNCTION evento_os_perfil_no_evento_default();
"""


SQL_REMOVE_TRIGGER = """
DROP TRIGGER IF EXISTS evento_os_perfil_no_evento_trigger ON evento_de_os;
DROP FUNCTION IF EXISTS evento_os_perfil_no_evento_default();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("ordens_servico", "0015_alter_atividadedaos_grandeza"),
        ("tenant", "0010_remove_tenantperfilhistorico_tph_tenant_recente_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventodeos",
            name="perfil_no_evento",
            field=models.CharField(
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
                    "Snapshot do perfil regulatorio do tenant no momento do evento OS. "
                    "ADR-0067 + INV-TENANT-PERFIL-003. Trigger BEFORE INSERT popula "
                    "via current_setting('app.perfil_tenant')."
                ),
            ),
        ),
        migrations.RunSQL(
            sql=SQL_CRIA_TRIGGER,
            reverse_sql=SQL_REMOVE_TRIGGER,
        ),
    ]
