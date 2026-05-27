# Saneamento SAN-PERFIL-TENANT — T-SAN-PERFIL-041 (Sprint 4)
# AC-SAN-PERFIL-003-1 + INV-TENANT-PERFIL-003:
#
# Coluna `perfil_no_evento CHAR(1)` em auditoria — snapshot do perfil
# regulatorio do tenant NO MOMENTO do INSERT (preserva contexto regulatorio
# para auditoria CGCRE/ANPD retroativa, mesmo quando perfil futuro mudar).
#
# Estrategia: NULLABLE inicial + trigger BEFORE INSERT popula via
# current_setting('app.perfil_tenant') quando registrar_auditoria nao
# preencheu explicitamente (defesa em camadas). PostgreSQL NAO suporta
# subquery em GENERATED ALWAYS AS STORED — daria erro de "expressao nao
# imutavel". Trigger BEFORE INSERT e a alternativa canonica.
#
# SET NOT NULL fica em migration Wave A apos backfill total.
#
# audit-immutability: skip -- snapshot em coluna NOVA NULLABLE; trigger AFTER UPDATE/DELETE existente nao e afetada
# tenant-perfil-imutavel: skip -- migration cria coluna + trigger BEFORE INSERT canonico ADR-0067

from django.db import migrations, models


SQL_CRIA_TRIGGER = """
CREATE OR REPLACE FUNCTION audit_perfil_no_evento_default()
RETURNS trigger AS $$
BEGIN
    -- Se aplicacao ja preencheu (via registrar_auditoria), respeita.
    -- Senao, le do GUC app.perfil_tenant (setado pelo TenantMiddleware
    -- em setar_contexto_pg_na_conexao).
    IF NEW.perfil_no_evento IS NULL THEN
        NEW.perfil_no_evento := NULLIF(current_setting('app.perfil_tenant', true), '');
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER audit_perfil_no_evento_default_trigger
BEFORE INSERT ON auditoria
FOR EACH ROW
EXECUTE FUNCTION audit_perfil_no_evento_default();
"""


SQL_REMOVE_TRIGGER = """
DROP TRIGGER IF EXISTS audit_perfil_no_evento_default_trigger ON auditoria;
DROP FUNCTION IF EXISTS audit_perfil_no_evento_default();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0018_alter_adminaccess_eh_break_glass_and_more"),
        ("tenant", "0010_remove_tenantperfilhistorico_tph_tenant_recente_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="auditoria",
            name="perfil_no_evento",
            field=models.CharField(
                max_length=1,
                null=True,
                blank=True,
                choices=[
                    ("A", "A — Acreditado RBC"),
                    ("B", "B — Rastreavel"),
                    ("C", "C — Em preparacao"),
                    ("D", "D — Comercial puro"),
                ],
                help_text=(
                    "Snapshot do perfil regulatorio do tenant no momento do INSERT "
                    "(ADR-0067 + INV-TENANT-PERFIL-003). Trigger BEFORE INSERT "
                    "populates via current_setting('app.perfil_tenant') quando "
                    "registrar_auditoria nao preencheu. NULLABLE durante janela "
                    "de backfill — SET NOT NULL em Sprint Wave A pos validacao."
                ),
            ),
        ),
        migrations.RunSQL(
            sql=SQL_CRIA_TRIGGER,
            reverse_sql=SQL_REMOVE_TRIGGER,
        ),
    ]
