"""T-CER-030 (parcial) — sequence PG `certificado_numero_seq` para `numero_interno`.

Molde M4 (`calibracao_numero_seq_global`): sequence GLOBAL (buracos aceitos entre
tenants — INV-CER-NUM-002). O `numero_interno` é o ID sequencial interno (auditoria);
o `numero_certificado` VISÍVEL sem buracos (reserva TTL) vem na 1b-numeração.

GRANT USAGE na sequence p/ app_user (PROD OWNER=app_migrator; nextval exige USAGE).

# rls-policy: external 0003_rls_reconciliacao (sequence — não cria tabela com tenant_id)
# audit-immutability: skip -- sequence pura nao toca trigger nem cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
CREATE SEQUENCE IF NOT EXISTS certificado_numero_seq AS bigint START 1 INCREMENT 1;
GRANT USAGE, SELECT ON SEQUENCE certificado_numero_seq TO app_user;
"""

REVERSE = """
DROP SEQUENCE IF EXISTS certificado_numero_seq;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("certificados", "0006_seed_authz_certificados"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
