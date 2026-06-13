"""Seed de faixas default de desconto para tenants existentes (T-PRC-033).

RunPython idempotente: só cria faixas em tenants que ainda não têm nenhuma.
Tenants provisionados APÓS esta migration recebem faixas via
`provisionar_tenant` (ADR-0015) que chama `seed_faixas_default`.

Faixas default (D-PRC-3 - decisao Roldao):
  0% - 10%  -> LIVRE    (sem aprovacao)
  10% - 20% -> GERENTE  (requer gerente)
  20% - 100% -> DONO    (requer dono)

# policy-test-coverage: skip -- RunPython de seed nao cria policy RLS nova
# rls-policy: external 0002_rls_policies (seed de dados, nao schema)
# audit-immutability: skip -- RunPython de seed nao toca triggers de auditoria
"""

from __future__ import annotations

import hashlib
import json
import uuid as _uuid
from decimal import Decimal


def _seed_faixas(apps, schema_editor):
    """Seed idempotente: tenants sem faixas recebem as default."""
    from django.db import connection as conn

    FAIXAS_DEFAULT = [
        (Decimal("0"), Decimal("10"), "livre"),
        (Decimal("10"), Decimal("20"), "gerente"),
        (Decimal("20"), Decimal("100"), "dono"),
    ]

    FaixaModel = apps.get_model("precificacao", "FaixaAprovacaoDesconto")
    TenantModel = apps.get_model("tenant", "Tenant")

    # DISABLE RLS ANTES das queries ORM (molde migration 0006)
    # Necessario para que FaixaModel.objects e TenantModel.objects nao sejam
    # filtrados por app.tenant_id ausente no contexto de migracao.
    with conn.cursor() as cur:
        cur.execute("ALTER TABLE faixa_aprovacao_desconto DISABLE ROW LEVEL SECURITY;")
        cur.execute("DROP POLICY IF EXISTS faixa_aprovacao_desconto_select_tenant_policy ON faixa_aprovacao_desconto;")
        cur.execute("DROP POLICY IF EXISTS faixa_aprovacao_desconto_insert_app_user_policy ON faixa_aprovacao_desconto;")
        cur.execute("DROP POLICY IF EXISTS faixa_aprovacao_desconto_update_app_user_policy ON faixa_aprovacao_desconto;")
        cur.execute("DROP POLICY IF EXISTS faixa_aprovacao_desconto_delete_block_policy ON faixa_aprovacao_desconto;")

    # Busca tenants sem faixas (RLS ja desabilitado acima)
    tenant_ids_com_faixa = set(
        FaixaModel.objects.values_list("tenant_id", flat=True).distinct()
    )
    tenant_ids_sem_faixa = list(
        TenantModel.objects.exclude(id__in=tenant_ids_com_faixa).values_list("id", flat=True)
    )

    if not tenant_ids_sem_faixa:
        # Restaura RLS mesmo sem tenants para processar (idempotencia)
        with conn.cursor() as cur:
            cur.execute("ALTER TABLE faixa_aprovacao_desconto ENABLE ROW LEVEL SECURITY;")
            cur.execute("ALTER TABLE faixa_aprovacao_desconto FORCE ROW LEVEL SECURITY;")
        return

    # Gera hash do conjunto default (igual para todos os tenants - mesmas faixas)
    payload = [
        {"pct_de": str(de), "pct_ate": str(ate), "alcada": alc}
        for de, ate, alc in FAIXAS_DEFAULT
    ]
    hash_conjunto = hashlib.sha256(
        json.dumps({"faixas": payload}, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()

    # UUID sentinel para criado_por no seed (sem usuario real)
    SEED_USER = _uuid.UUID("00000000-0000-0000-0000-000000000001")

    faixas_a_criar = []
    for tenant_id in tenant_ids_sem_faixa:
        for pct_de, pct_ate, alcada in FAIXAS_DEFAULT:
            faixas_a_criar.append(
                FaixaModel(
                    id=_uuid.uuid4(),
                    tenant_id=tenant_id,
                    pct_de=pct_de,
                    pct_ate=pct_ate,
                    alcada=alcada,
                    versao_n=1,
                    hash_conjunto=hash_conjunto,
                    criado_por=SEED_USER,
                )
            )

    if faixas_a_criar:
        FaixaModel.objects.bulk_create(faixas_a_criar, ignore_conflicts=True)

    # Restaura RLS (molde migration 0002)
    with conn.cursor() as cur:
        cur.execute(
            "CREATE POLICY faixa_aprovacao_desconto_select_tenant_policy "
            "ON faixa_aprovacao_desconto FOR SELECT "
            "USING (tenant_id = current_setting('app.tenant_id')::uuid);"
        )
        cur.execute(
            "CREATE POLICY faixa_aprovacao_desconto_insert_app_user_policy "
            "ON faixa_aprovacao_desconto FOR INSERT "
            "WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid);"
        )
        cur.execute(
            "CREATE POLICY faixa_aprovacao_desconto_update_app_user_policy "
            "ON faixa_aprovacao_desconto FOR UPDATE "
            "USING (tenant_id = current_setting('app.tenant_id')::uuid);"
        )
        cur.execute(
            "CREATE POLICY faixa_aprovacao_desconto_delete_block_policy "
            "ON faixa_aprovacao_desconto FOR DELETE "
            "USING (false);"
        )
        cur.execute("ALTER TABLE faixa_aprovacao_desconto ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE faixa_aprovacao_desconto FORCE ROW LEVEL SECURITY;")


def _unseed_faixas(apps, schema_editor):
    """Reversa: remove apenas faixas com versao_n=1 (seed default)."""
    FaixaModel = apps.get_model("precificacao", "FaixaAprovacaoDesconto")
    FaixaModel.objects.filter(versao_n=1).delete()


from django.db import migrations  # noqa: E402 -- após definição das funções de seed


class Migration(migrations.Migration):
    atomic = False  # seed manipula RLS manualmente

    dependencies = [
        ("precificacao", "0007_align_metadata"),
        ("tenant", "0012_aplicar_evento_cgcre_vigencia"),
    ]

    operations = [
        migrations.RunPython(_seed_faixas, reverse_code=_unseed_faixas),
    ]
