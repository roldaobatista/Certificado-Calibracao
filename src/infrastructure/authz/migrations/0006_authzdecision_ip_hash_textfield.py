"""T-FB-04 — alarga AuthzDecision.ip_hash para TextField.

O `ip_hash` passou a ser HMAC VERSIONADO (`{key_id}:{64hex}` ≈ 67 chars)
— estourava varchar(64) (`DataError: value too long`). TextField (sem
limite) é imune ao crescimento do key_id; no Postgres `text` não tem
custo vs varchar. Mesma decisão FA-A1 p/ `AcessoDadosCliente.ip_hash`.

AlterField simples (DDL ALTER COLUMN TYPE — não passa pela RLS/trigger
anti-mutation, que só barram UPDATE/DELETE de linha). Mesmo padrão de
`audit/0010_acessos_ip_hash_textfield`.
"""

from __future__ import annotations

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("authz", "0005_policy_authz_decisions_por_usuario"),
    ]

    operations = [
        migrations.AlterField(
            model_name="authzdecision",
            name="ip_hash",
            field=models.TextField(
                blank=True,
                default="",
                help_text=(
                    "HMAC-SHA256 VERSIONADO do IP (`{key_id}:{digest}` — "
                    "nunca IP cru; LGPD art. 13 §4). TextField: o prefixo "
                    "de versão estoura varchar(64) — mesma decisão FA-A1 "
                    "p/ ip_hash (T-FB-04)."
                ),
            ),
        ),
    ]
