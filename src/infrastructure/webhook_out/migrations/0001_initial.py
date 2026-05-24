"""WebhookDestino — cadastro DPA + chave HMAC + RLS por tenant.

F-C1 P4 (T-FC1-11) — ADR-0054 aceita dentro desta fase.
INV-WEBHOOK-OUT-005 (DPA enforcement) materializado via constraints
+ RLS.

# rls-policy: external 0001 -- policy nasce nesta mesma migration
# tests-coverage: tests/test_webhook_destino_dpa.py (Wave A)
"""

import uuid

from django.db import migrations, models

FORWARD_CONSTRAINTS_AND_RLS = r"""
ALTER TABLE webhook_destino ENABLE ROW LEVEL SECURITY;
ALTER TABLE webhook_destino FORCE ROW LEVEL SECURITY;

-- SELECT/INSERT/UPDATE: modo_sistema OR tenant_id ativo
CREATE POLICY webhook_destino_select ON webhook_destino
    FOR SELECT
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            WHEN tenant_id IS NULL
                THEN FALSE
            ELSE tenant_id::text = ANY(
                string_to_array(
                    coalesce(current_setting('app.tenant_ids', true), ''),
                    ','
                )
            )
        END
    );

CREATE POLICY webhook_destino_insert ON webhook_destino
    FOR INSERT
    WITH CHECK (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            WHEN tenant_id IS NULL
                THEN FALSE
            ELSE tenant_id::text = ANY(
                string_to_array(
                    coalesce(current_setting('app.tenant_ids', true), ''),
                    ','
                )
            )
        END
    );

CREATE POLICY webhook_destino_update ON webhook_destino
    FOR UPDATE
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            WHEN tenant_id IS NULL
                THEN FALSE
            ELSE tenant_id::text = ANY(
                string_to_array(
                    coalesce(current_setting('app.tenant_ids', true), ''),
                    ','
                )
            )
        END
    );

-- DELETE NUNCA — soft-delete via desativado_em (ADR-0031 padrao mutavel)
CREATE POLICY webhook_destino_no_delete ON webhook_destino
    FOR DELETE
    USING (FALSE);
"""

REVERSE_CONSTRAINTS_AND_RLS = r"""
DROP POLICY IF EXISTS webhook_destino_select ON webhook_destino;
DROP POLICY IF EXISTS webhook_destino_insert ON webhook_destino;
DROP POLICY IF EXISTS webhook_destino_update ON webhook_destino;
DROP POLICY IF EXISTS webhook_destino_no_delete ON webhook_destino;
ALTER TABLE webhook_destino DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("multitenant", "0004_audit_hash_chain_por_tenant"),
    ]

    operations = [
        migrations.CreateModel(
            name="WebhookDestino",
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
                ("tenant_id", models.UUIDField(db_index=True)),
                ("nome", models.CharField(max_length=120)),
                ("url_base", models.URLField(max_length=500)),
                (
                    "papel_lgpd",
                    models.CharField(
                        choices=[
                            ("controlador", "Controlador (compartilhamento)"),
                            ("operador", "Operador (DPA obrigatorio art. 39)"),
                            ("terceiro_destinatario", "Terceiro destinatario"),
                        ],
                        max_length=30,
                    ),
                ),
                ("dpa_url", models.URLField(max_length=500)),
                ("dpa_assinado_em", models.DateField()),
                ("dpa_vence_em", models.DateField()),
                ("finalidade", models.TextField()),
                ("categorias_dados", models.JSONField(default=list)),
                ("chave_hmac_id", models.CharField(max_length=120)),
                ("chave_expires_at", models.DateField()),
                ("permite_http", models.BooleanField(default=False)),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("criado_por", models.UUIDField()),
                (
                    "desativado_em",
                    models.DateTimeField(blank=True, db_index=True, null=True),
                ),
                ("desativado_por", models.UUIDField(blank=True, null=True)),
                ("desativado_motivo", models.TextField(blank=True)),
            ],
            options={
                "verbose_name": "Webhook destino",
                "verbose_name_plural": "Webhook destinos",
                "db_table": "webhook_destino",
            },
        ),
        migrations.AddConstraint(
            model_name="webhookdestino",
            constraint=models.UniqueConstraint(
                condition=models.Q(("desativado_em__isnull", True)),
                fields=("tenant_id", "nome"),
                name="webhook_destino_nome_unique_por_tenant_ativo",
            ),
        ),
        migrations.AddConstraint(
            model_name="webhookdestino",
            constraint=models.CheckConstraint(
                check=models.Q(("dpa_vence_em__gt", models.F("dpa_assinado_em"))),
                name="webhook_destino_dpa_vigencia_coerente",
            ),
        ),
        migrations.AddIndex(
            model_name="webhookdestino",
            index=models.Index(
                fields=["tenant_id", "dpa_vence_em"],
                name="webhook_des_tenant__a83e22_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="webhookdestino",
            index=models.Index(
                fields=["tenant_id", "chave_expires_at"],
                name="webhook_des_tenant__c9d4e1_idx",
            ),
        ),
        migrations.RunSQL(
            sql=FORWARD_CONSTRAINTS_AND_RLS,
            reverse_sql=REVERSE_CONSTRAINTS_AND_RLS,
        ),
    ]
