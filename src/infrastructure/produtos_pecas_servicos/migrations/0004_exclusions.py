"""T-PPS-021 — Exclusion constraints `btree_gist` (molde 0004 da frente #1).

1. `excl_pps_versao_vigencia` (INV-PPS-VERSAO-SEM-SOBREPOSICAO, parte do
   INV-026): duas versões do MESMO (tenant, item) não sobrepõem vigência —
   torna `versao_vigente_em(D)` determinístico. Half-open `[)`; `vigencia_fim
   NULL` = aberto. Revogadas saem (WHERE revogado_em IS NULL — revogar a
   versão errada libera o espaço pra corrigida, lição M2 da frente #1).

2. `excl_pps_linha_vigencia` (INV-PPS-LINHA-SEM-SOBREPOSICAO): idem por
   (tenant, tabela, item) — `linha_vigente_em(D)` determinístico (a porta
   `preco_para_os` resolve no máximo 1 linha — ADR-0081).

A extensão `btree_gist` já é criada pelos init scripts do PG (docker/postgres/
init); a migration NÃO tenta CREATE EXTENSION (exige superuser).

# rls-policy: external 0002_rls_policies (constraint pura — nao cria tabela)
# audit-immutability: skip -- constraint de exclusao nao toca trigger nem cadeia de auditoria
# tests-coverage: tests/test_pps_schema_fatia1b.py (sobreposicao + revogada/substituta)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
ALTER TABLE item_catalogo_versao ADD CONSTRAINT excl_pps_versao_vigencia
EXCLUDE USING gist (
    tenant_id WITH =,
    item_id WITH =,
    tstzrange(vigencia_inicio, vigencia_fim, '[)') WITH &&
) WHERE (revogado_em IS NULL);

ALTER TABLE linha_tabela_preco ADD CONSTRAINT excl_pps_linha_vigencia
EXCLUDE USING gist (
    tenant_id WITH =,
    tabela_id WITH =,
    item_id WITH =,
    tstzrange(vigencia_inicio, vigencia_fim, '[)') WITH &&
) WHERE (revogado_em IS NULL);
"""

REVERSE = """
ALTER TABLE linha_tabela_preco DROP CONSTRAINT IF EXISTS excl_pps_linha_vigencia;
ALTER TABLE item_catalogo_versao DROP CONSTRAINT IF EXISTS excl_pps_versao_vigencia;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
