"""T-AGE-024 — Exclusion constraint GIST de overlap de slots da agenda.

INV-AG-OVERLAP-001 / D-AGE-13 / R1 / R12 (TL-AGE-01 CRIT):

Dois eventos do MESMO técnico no MESMO tenant NÃO podem ter intervalos
sobrepostos (exceto quando ``estado = 'cancelado'``).

Constraint EXATA (byte-a-byte igual ao molde ``excl_imposto_vigencia_sobreposta``
em ``configuracoes_sistema/migrations/0004_exclusion_imposto.py``):

    EXCLUDE USING gist (
        tenant_id WITH =,
        tecnico_id WITH =,
        tstzrange(inicia_at, termina_at, '[)') WITH &&
    ) WHERE (estado != 'cancelado')

CRÍTICO — tenant_id é a 1ª coluna (R1):
    RLS NÃO escopa a constraint (é avaliada antes das policies). Omitir
    tenant_id causaria furo de isolamento: técnicos homônimos de tenants
    distintos colidiriam. tenant_id WITH = garante a escopo por tenant.

Range half-open '[)' (R12):
    Slots adjacentes 09:00-10:00 e 10:00-11:00 do MESMO técnico NAO
    colidem (extremo direito é aberto). Isso é exigido para que blocos
    contínuos de trabalho não sejam rejeitados.

btree_gist:
    Necessária para usar operador '=' (igualdade) em UUID dentro de um
    índice GIST. Já disponível pelos init scripts do PG
    (docker/postgres/init/02-extensions.sh) — a migration NÃO tenta
    CREATE EXTENSION (exige superuser).

# rls-policy: external 0002_rls_policies (constraint pura — não cria tabela)
# audit-immutability: skip -- constraint de exclusão não toca trigger nem cadeia auditoria
# tests-coverage: tests/test_agenda_schema_fatia1b.py (overlap + half-open + concorrência)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
ALTER TABLE evento_agenda ADD CONSTRAINT excl_agenda_tecnico_overlap
EXCLUDE USING gist (
    tenant_id WITH =,
    tecnico_id WITH =,
    tstzrange(inicia_at, termina_at, '[)') WITH &&
) WHERE (estado != 'cancelado');
"""

REVERSE = """
ALTER TABLE evento_agenda DROP CONSTRAINT IF EXISTS excl_agenda_tecnico_overlap;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("agenda", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
