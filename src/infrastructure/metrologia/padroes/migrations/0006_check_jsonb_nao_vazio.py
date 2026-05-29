"""T-PAD-060 (P7) — CHECK constraint não-vazio nos 3 JSONB (INV-PAD-002).

Defesa de banco que faltava: o use case `cadastrar_padrao` já valida ≥1
grandeza + ≥1 faixa + ≥1 incerteza no `__post_init__`, mas SQL cru / import
direto / `objects.create` poderiam burlar a camada application. Esta migration
crava a barreira no banco (ISO 17025 cl. 6.5 — cadeia metrológica não pode
nascer vazia; rejeição em supervisão CGCRE, R-018 score 25).

`jsonb_array_length(x) > 0` exige array JSON com ≥1 elemento. Os 3 campos são
JSONField (jsonb) com default=list; rows criadas pelo fluxo legítimo já
satisfazem (use case bloqueia vazio), então o ADD CONSTRAINT não quebra dados
existentes.

# rls-policy: external 0002_rls_policies (ALTER ADD CONSTRAINT — não cria tabela)
# audit-immutability: skip -- CHECK constraint puro nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

_CAMPOS = ("grandezas", "faixas", "incertezas_certificado")


def _forward() -> str:
    return "\n".join(
        f"ALTER TABLE padrao_metrologico "
        f"ADD CONSTRAINT ck_pad_{c}_nao_vazio "
        f"CHECK (jsonb_array_length({c}) > 0);"
        for c in _CAMPOS
    )


def _reverse() -> str:
    return "\n".join(
        f"ALTER TABLE padrao_metrologico DROP CONSTRAINT IF EXISTS ck_pad_{c}_nao_vazio;"
        for c in _CAMPOS
    )


class Migration(migrations.Migration):
    dependencies = [
        ("padroes", "0005_seed_authz_padroes"),
    ]

    operations = [
        migrations.RunSQL(sql=_forward(), reverse_sql=_reverse()),
    ]
