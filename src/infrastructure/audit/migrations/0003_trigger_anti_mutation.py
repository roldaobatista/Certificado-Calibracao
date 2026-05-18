"""Trigger PG que bloqueia UPDATE/DELETE na tabela auditoria.

Defesa em profundidade — alem do .save()/.delete() bloqueados em Python
(Marco 2), o banco RECUSA a operacao mesmo se alguem usar SQL bruto ou se
um agente IA encontrar um caminho fora do ORM.

So app_migrator pode dropar este trigger. Em runtime (app_user), nao ha
como contornar.
"""

from __future__ import annotations

from django.db import migrations


TRIGGER_SQL = """
CREATE OR REPLACE FUNCTION auditoria_bloqueia_mutation()
RETURNS trigger
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION
        'Auditoria e INSERT-only. % bloqueado em trigger PG (Marco 4 F-A).',
        TG_OP
    USING ERRCODE = '23514'; -- check_violation
END;
$$;

CREATE TRIGGER auditoria_anti_update
    BEFORE UPDATE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION auditoria_bloqueia_mutation();

CREATE TRIGGER auditoria_anti_delete
    BEFORE DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION auditoria_bloqueia_mutation();
"""

TRIGGER_REVERSE_SQL = """
DROP TRIGGER IF EXISTS auditoria_anti_delete ON auditoria;
DROP TRIGGER IF EXISTS auditoria_anti_update ON auditoria;
DROP FUNCTION IF EXISTS auditoria_bloqueia_mutation();
"""


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0002_initial"),
    ]

    operations = [
        migrations.RunSQL(
            sql=TRIGGER_SQL,
            reverse_sql=TRIGGER_REVERSE_SQL,
        ),
    ]
