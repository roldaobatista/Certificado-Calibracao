"""T-CFG-024 — Exclusion constraint `btree_gist` no catálogo de impostos.

INV-CFG-IMPOSTO-SEM-SOBREPOSICAO (TL-05): duas linhas do MESMO
(tenant, tipo, filial) não podem ter vigências sobrepostas — é isso que torna
"imposto vigente em D" determinístico (D-CFG-3). O range é half-open `[)` com
`vigencia_fim NULL` = aberto (+inf). `filial_id` NULL = catálogo do tenant
inteiro: como NULL nunca colide em constraint, normaliza com COALESCE para o
UUID-zero sentinela. Linhas REVOGADAS saem da constraint (WHERE revogado_em IS
NULL) — revogar a linha errada libera o espaço para a corrigida.

A extensão `btree_gist` (igualdade de uuid/text em índice gist) já é criada
pelos init scripts do PG (docker/postgres/init/02-extensions.sh e 03-test-db.sh);
a migration NÃO tenta CREATE EXTENSION (exige superuser — app_migrator não tem).

# rls-policy: external 0002_rls_policies (constraint pura — nao cria tabela)
# audit-immutability: skip -- constraint de exclusao nao toca trigger nem cadeia de auditoria
# tests-coverage: tests/test_configuracoes_schema_fatia1b.py (sobreposicao)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
ALTER TABLE imposto ADD CONSTRAINT excl_imposto_vigencia_sobreposta
EXCLUDE USING gist (
    tenant_id WITH =,
    tipo WITH =,
    COALESCE(filial_id, '00000000-0000-0000-0000-000000000000'::uuid) WITH =,
    tstzrange(vigencia_inicio, vigencia_fim, '[)') WITH &&
) WHERE (revogado_em IS NULL);
"""

REVERSE = """
ALTER TABLE imposto DROP CONSTRAINT IF EXISTS excl_imposto_vigencia_sobreposta;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("configuracoes_sistema", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
