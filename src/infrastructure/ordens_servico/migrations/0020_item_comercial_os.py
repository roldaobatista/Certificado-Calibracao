"""Migration 0020 — CreateModel ItemComercialOS + RLS policies (ADR-0082 / D-OSME-3).

Fatia 1c da frente os-multi-equipamento.

Operacoes:
1. CreateModel ItemComercialOS — Padrao A soft-delete (ADR-0031).
2. AddIndex itemcom_tenant_os_idx (tenant, os).
3. RunSQL: ENABLE + FORCE ROW LEVEL SECURITY + 4 policies tenant (padrao v2 ADR-0002)
   + GRANT SELECT/INSERT/UPDATE/DELETE para app_user.
   reverse_sql: DROP POLICIES + DISABLE RLS + REVOKE.

INV-OSME-ITEMCOM-001: a tabela NUNCA tem equipamento_id nem tipo_bloqueia_concorrencia.
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models

# =============================================================
# RLS + GRANTS para item_comercial_os (padrao v2 ADR-0002 §6)
# Molde: 0002_rls_policies.py
# tests-coverage: tests/test_osme_fatia1c.py
#   happy: test_osme_f1c_b (persiste + lista via repo)
#   unhappy RLS: test_osme_f1c_c (tenant B NAO enxerga ItemComercialOS do tenant A)
# =============================================================
RLS_FORWARD = """
-- RLS pattern v2 (ADR-0002 §6) para item_comercial_os
ALTER TABLE item_comercial_os ENABLE ROW LEVEL SECURITY;
ALTER TABLE item_comercial_os FORCE ROW LEVEL SECURITY;

CREATE POLICY item_comercial_os_tenant_isolation_select ON item_comercial_os
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY item_comercial_os_tenant_isolation_update ON item_comercial_os
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY item_comercial_os_tenant_isolation_delete ON item_comercial_os
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY item_comercial_os_tenant_isolation_insert ON item_comercial_os
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- Grants para app_user (role que a aplicacao usa em runtime)
GRANT SELECT, INSERT, UPDATE, DELETE ON item_comercial_os TO app_user;
"""

RLS_REVERSE = """
REVOKE SELECT, INSERT, UPDATE, DELETE ON item_comercial_os FROM app_user;

DROP POLICY IF EXISTS item_comercial_os_tenant_isolation_insert ON item_comercial_os;
DROP POLICY IF EXISTS item_comercial_os_tenant_isolation_delete ON item_comercial_os;
DROP POLICY IF EXISTS item_comercial_os_tenant_isolation_update ON item_comercial_os;
DROP POLICY IF EXISTS item_comercial_os_tenant_isolation_select ON item_comercial_os;
ALTER TABLE item_comercial_os DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("ordens_servico", "0019_os_equipamento_nullable"),
        ("tenant", "0001_initial"),
    ]

    operations = [
        # 1. Cria a tabela ItemComercialOS.
        migrations.CreateModel(
            name="ItemComercialOS",
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
                        help_text="Tenant do item; herdado da OS pai (INV-TENANT-001).",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="itens_comerciais_os",
                        to="tenant.tenant",
                    ),
                ),
                (
                    "os",
                    models.ForeignKey(
                        help_text="OS pai do item comercial.",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="itens_comerciais",
                        to="ordens_servico.os",
                    ),
                ),
                (
                    "tipo",
                    models.CharField(
                        choices=[
                            ("deslocamento", "Deslocamento"),
                            ("taxa_visita", "Taxa de visita"),
                            ("outro", "Outro"),
                        ],
                        help_text="Enum dos 3 tipos comerciais (INV-OSME-ITEMCOM-001).",
                        max_length=30,
                    ),
                ),
                (
                    "descricao_publica",
                    models.CharField(
                        help_text="Descricao sem PII exibida na OS e no faturamento.",
                        max_length=200,
                    ),
                ),
                (
                    "valor",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Valor unitario (INV-OSME-ITEMCOM-001: soma em OS.valor_total).",
                        max_digits=14,
                    ),
                ),
                (
                    "quantidade",
                    models.IntegerField(
                        default=1,
                        help_text="Quantidade de unidades do item comercial.",
                    ),
                ),
                (
                    "origem_item_id",
                    models.UUIDField(
                        blank=True,
                        help_text=(
                            "Rastreio do item de orcamento de origem (db_constraint=False — "
                            "modulo orcamentos ainda nao existe). NULL em item avulso."
                        ),
                        null=True,
                    ),
                ),
                # Padrao A soft-delete (ADR-0031)
                ("deletado_em", models.DateTimeField(blank=True, null=True)),
                ("deletado_por_usuario_id", models.UUIDField(blank=True, null=True)),
                (
                    "deletado_motivo",
                    models.CharField(blank=True, default="", max_length=200),
                ),
                ("criado_em", models.DateTimeField(auto_now_add=True)),
                ("atualizado_em", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Item comercial da OS",
                "verbose_name_plural": "Itens comerciais da OS",
                "db_table": "item_comercial_os",
                "ordering": ["os", "criado_em"],
            },
        ),
        # 2. Indice por (tenant, os) para listagem eficiente.
        migrations.AddIndex(
            model_name="itemcomercialos",
            index=models.Index(
                fields=["tenant", "os"],
                name="itemcom_tenant_os_idx",
            ),
        ),
        # 3. RLS policies + grants (padrao v2 ADR-0002 §6).
        migrations.RunSQL(
            sql=RLS_FORWARD,
            reverse_sql=RLS_REVERSE,
        ),
    ]
