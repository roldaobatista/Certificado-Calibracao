"""T-ORC-031 (Fatia 2 / Onda 2a) — amplia `item_orcamento.semaforo` (10 -> 15).

CONSERTO REGRA #0 (bug latente da Fatia 1b): o `Semaforo` do motor de
`precificacao` inclui `INDISPONIVEL = "indisponivel"` (12 chars), que e o caso
COMUM em Wave A — `CustoProviderStub` sempre devolve custo indisponivel, logo o
item sem regra de formacao/custo carimba `semaforo="indisponivel"`. O campo
nascera com `max_length=10`, causando `DataError: value too long` no INSERT do
1o item de orcamento. Ampliacao defensiva para 15 (folga). Aditivo/reversivel —
nao toca dados existentes (campo so passa a aceitar strings maiores).

# policy-test-coverage: skip -- AlterField puro, sem CREATE POLICY
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0006_seed_authz"),
    ]

    operations = [
        migrations.AlterField(
            model_name="itemorcamento",
            name="semaforo",
            field=models.CharField(
                help_text="verde | amarelo | vermelho | indisponivel (precificacao Semaforo.value).",
                max_length=15,
            ),
        ),
    ]
