"""T-AGE-026 — Seed do catálogo de feriados nacionais BR (D-AGE-10).

Feriados nacionais fixos (Lei 9.093/95 + datas estáveis):
  - 01/01 Ano Novo
  - 21/04 Tiradentes
  - 01/05 Dia do Trabalho
  - 07/09 Independência do Brasil
  - 12/10 Nossa Sra. Aparecida
  - 02/11 Finados
  - 15/11 Proclamação da República
  - 20/11 Consciência Negra (Lei 14.759/2023)
  - 25/12 Natal

Feriados móveis (carnaval, semana santa, corpus christi) dependem do ciclo
pascalino e variam de ano para ano. O seed cobre apenas os FIXOS para não
requerer lógica de cálculo no banco. Feriados móveis por ano serão adicionados
via CRUD custom do tenant (D-AGE-10 / US-AG-005) ou job externo (GATE-AGE-FERIADO-API).

Os registros usam ``tenant=None`` (coluna ``tenant_id=NULL``) para indicar
catálogo nacional imutável. A policy de RLS SELECT em ``feriado`` inclui
``tenant_id IS NULL`` (migration 0002) para que todos os tenants leiam este seed.

Idempotente: ON CONFLICT DO NOTHING na constraint ``uq_agenda_feriado_nacional_data``.

# policy-test-coverage: skip -- seed RunPython, sem CREATE POLICY nova
# audit-immutability: skip -- dados de referência estáticos (feriados nacionais)
"""

from __future__ import annotations

import uuid
from datetime import date

from django.db import migrations

# (mês, dia, descrição)
_FERIADOS_FIXOS: list[tuple[int, int, str]] = [
    (1, 1, "Confraternização Universal (Ano Novo)"),
    (4, 21, "Tiradentes"),
    (5, 1, "Dia do Trabalho"),
    (9, 7, "Independência do Brasil"),
    (10, 12, "Nossa Senhora Aparecida (Padroeira do Brasil)"),
    (11, 2, "Finados"),
    (11, 15, "Proclamação da República"),
    (11, 20, "Dia da Consciência Negra (Lei 14.759/2023)"),
    (12, 25, "Natal"),
]

# Seeda feriados para os anos 2025-2030 (cobertura Wave A).
_ANOS = list(range(2025, 2031))


def _gerar_feriados() -> list[dict]:
    registros = []
    for ano in _ANOS:
        for mes, dia, descricao in _FERIADOS_FIXOS:
            registros.append(
                {
                    "id": str(uuid.uuid4()),
                    "data": date(ano, mes, dia).isoformat(),
                    "descricao": descricao,
                    "nacional": True,
                    "ativo": True,
                }
            )
    return registros


def seed(apps, schema_editor):
    """Insere feriados nacionais fixos (idempotente via ON CONFLICT DO NOTHING)."""
    feriados = _gerar_feriados()
    with schema_editor.connection.cursor() as cur:
        # RLS está ENABLED em feriado; como app_migrator não tem tenant_id,
        # precisamos desabilitar temporariamente para o seed (padrão dos seeds).
        cur.execute("ALTER TABLE feriado DISABLE ROW LEVEL SECURITY;")
        for f in feriados:
            # ON CONFLICT com partial index: UniqueConstraint(condition=...) vira partial index
            # no PG — precisa usar WHERE na cláusula ON CONFLICT (não ON CONSTRAINT).
            cur.execute(
                """
                INSERT INTO feriado (id, tenant_id, data, descricao, nacional, ativo, criado_em)
                VALUES (%s, NULL, %s, %s, TRUE, TRUE, now())
                ON CONFLICT (data) WHERE (nacional = TRUE AND tenant_id IS NULL) DO NOTHING;
                """,
                [f["id"], f["data"], f["descricao"]],
            )
        cur.execute("ALTER TABLE feriado ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE feriado FORCE ROW LEVEL SECURITY;")


def unseed(apps, schema_editor):
    """Remove feriados nacionais do seed (reversão — não afeta custom do tenant)."""
    with schema_editor.connection.cursor() as cur:
        cur.execute("ALTER TABLE feriado DISABLE ROW LEVEL SECURITY;")
        cur.execute("DELETE FROM feriado WHERE nacional = TRUE AND tenant_id IS NULL;")
        cur.execute("ALTER TABLE feriado ENABLE ROW LEVEL SECURITY;")
        cur.execute("ALTER TABLE feriado FORCE ROW LEVEL SECURITY;")


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("agenda", "0006_seed_authz"),
    ]
    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
