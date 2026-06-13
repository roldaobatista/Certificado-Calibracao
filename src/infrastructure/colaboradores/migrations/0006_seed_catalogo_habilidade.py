"""Seed global de CatalogoHabilidade (T-COL-026 — D-COL-5 / TL-COL-10).

Seed literal de 16 habilidades técnicas/gerais. Molde: authz/0003_seed_perfis.py
(INSERT direto — catalogo_habilidade NÃO tem RLS, logo sem DISABLE/ENABLE RLS).

Lista literal no arquivo — sem import de `metrologia` (evita aresta runtime com
calibracao — objetivo gap #4 / D-COL-5).

Seed idempotente: ON CONFLICT (codigo) DO NOTHING.
Reverse: DELETE WHERE codigo = ANY(codigos_do_seed).

# policy-test-coverage: skip -- seed global sem RLS, sem CREATE POLICY
# rls-policy: skip -- catalogo_habilidade não tem RLS (isenção TL-COL-10)
"""

from __future__ import annotations

from django.db import migrations

# Lista literal de habilidades do catálogo (D-COL-5 / TL-COL-10).
# Sem import de metrologia (evita aresta runtime — gap #4).
CATALOGO = [
    ("massa", "Calibração de instrumentos de pesagem e medição de massa", "massa"),
    ("volume", "Calibração de instrumentos de medição de volume e vazão estática", "volume"),
    ("temperatura", "Calibração de instrumentos de medição de temperatura", "temperatura"),
    ("dimensional", "Calibração de instrumentos de medição dimensional e geométrica", "dimensional"),
    ("pressao", "Calibração de instrumentos de medição de pressão e vácuo", "pressao"),
    ("eletricidade", "Calibração de instrumentos elétricos (tensão, corrente, resistência, potência)", "eletricidade"),
    ("tempo_frequencia", "Calibração de instrumentos de tempo e frequência", "tempo_frequencia"),
    ("vazao", "Calibração de medidores de vazão dinâmica (líquidos e gases)", "vazao"),
    ("torque", "Calibração de instrumentos de medição de torque e força", "torque"),
    ("dureza", "Calibração de equipamentos de ensaio de dureza (Rockwell, Vickers, Brinell)", "dureza"),
    ("acustica", "Calibração de instrumentos de medição acústica e vibração", "acustica"),
    ("otica", "Calibração de instrumentos ópticos e de iluminância", "otica"),
    ("umidade", "Calibração de higrômetros e instrumentos de medição de umidade", "umidade"),
    ("ph_condutividade", "Calibração de medidores de pH, condutividade e parâmetros eletroquímicos", "ph_condutividade"),
    ("laboratorio_geral", "Habilidade geral de laboratório de calibração (suporte técnico)", None),
    ("inspecao_metrologia_legal", "Inspeção e verificação em metrologia legal (INMETRO/IPEM)", "dimensional"),
]

_CODIGOS = [row[0] for row in CATALOGO]


def seed(apps, schema_editor):
    """Insere habilidades do catálogo global — idempotente (ON CONFLICT DO NOTHING)."""
    with schema_editor.connection.cursor() as cur:
        for codigo, descricao, grandeza in CATALOGO:
            cur.execute(
                "INSERT INTO catalogo_habilidade (codigo, descricao, grandeza) "
                "VALUES (%s, %s, %s) ON CONFLICT (codigo) DO NOTHING;",
                [codigo, descricao, grandeza],
            )


def unseed(apps, schema_editor):
    with schema_editor.connection.cursor() as cur:
        cur.execute(
            "DELETE FROM catalogo_habilidade WHERE codigo = ANY(%s);",
            [_CODIGOS],
        )


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("colaboradores", "0005_seed_authz_colaboradores"),
    ]

    operations = [
        migrations.RunPython(seed, reverse_code=unseed),
    ]
