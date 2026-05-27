# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-042 (Sprint 4)
# AC-SAN-PERFIL-003-1 + AC-003-1b + INV-TENANT-PERFIL-003 + R7 plan.md:
#
# evento_de_calibracao ganha:
#   - perfil_no_evento CHAR(1) NULLABLE (trigger BEFORE INSERT populates
#     de current_setting('app.perfil_tenant'))
#   - escopos_acreditados_vigentes_no_momento JSONB NOT NULL DEFAULT '[]'
#     (R7 — auditor CGCRE pede em 2030 quais escopos estavam vigentes em
#     2027; fail-open lazy [] ate modulo licencas-acreditacoes Wave A
#     popular)
#
# tenant-perfil-imutavel: skip -- migration cria coluna + trigger snapshot canonico ADR-0067

from django.db import migrations, models


SQL_CRIA_TRIGGER = """
CREATE OR REPLACE FUNCTION evento_calibracao_perfil_no_evento_default()
RETURNS trigger AS $$
BEGIN
    IF NEW.perfil_no_evento IS NULL THEN
        NEW.perfil_no_evento := NULLIF(current_setting('app.perfil_tenant', true), '');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER evento_calibracao_perfil_no_evento_trigger
BEFORE INSERT ON evento_de_calibracao
FOR EACH ROW
EXECUTE FUNCTION evento_calibracao_perfil_no_evento_default();
"""


SQL_REMOVE_TRIGGER = """
DROP TRIGGER IF EXISTS evento_calibracao_perfil_no_evento_trigger ON evento_de_calibracao;
DROP FUNCTION IF EXISTS evento_calibracao_perfil_no_evento_default();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("calibracao", "0014_grants_app_user"),
        ("tenant", "0010_remove_tenantperfilhistorico_tph_tenant_recente_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="eventodecalibracao",
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
                    "Snapshot do perfil regulatorio do tenant no momento do evento. "
                    "ADR-0067 + INV-TENANT-PERFIL-003. Trigger BEFORE INSERT le "
                    "current_setting('app.perfil_tenant') quando NULL no INSERT."
                ),
            ),
        ),
        migrations.AddField(
            model_name="eventodecalibracao",
            name="escopos_acreditados_vigentes_no_momento",
            field=models.JSONField(
                default=list,
                help_text=(
                    "R7 plan.md — array de {grandeza, faixa, vigencia_inicio, "
                    "vigencia_fim, numero_rbc} vigentes no momento do evento, "
                    "quando perfil_no_evento='A'. NIT-DICLA-030 item 8.2.6. "
                    "Fail-open lazy `[]` ate modulo metrologia/escopos-cmc Wave A. "
                    "Auditor CGCRE em supervisao retroativa consulta este campo "
                    "para reconstruir escopo vigente na data do evento."
                ),
            ),
        ),
        migrations.RunSQL(
            sql=SQL_CRIA_TRIGGER,
            reverse_sql=SQL_REMOVE_TRIGGER,
        ),
    ]
