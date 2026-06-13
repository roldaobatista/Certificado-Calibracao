"""T-COL-023 — Trigger defensivo BEFORE DELETE em `colaborador`.

Bloqueia delete físico de colaborador que tenha registros filhos em
`colaborador_papel`, `colaborador_habilidade` ou `colaborador_documento`.

Motivação: o agregado usa soft-delete Padrão C (deletado_em) e desligamento de
negócio (data_desligamento). Delete físico direto burla a trilha de auditoria e
quebra FKs de papéis/habilidades/documentos com ON DELETE PROTECT (INV-001 /
D-COL-3 / ADR-0031).

Mensagem de erro identificada por INV-COL-INATIVO para que o use case possa
capturar e retratar adequadamente (sem depender de IntegrityError genérico).

# audit-immutability: trigger de proteção — NÃO afeta cadeia WORM desta migration
# rls-policy: skip — trigger opera BEFORE DELETE sem bypass de RLS
# tests-coverage: tests/test_colaboradores_schema_fatia1b.py (test_trigger_block_delete)
"""

from __future__ import annotations

from django.db import migrations

SQL_FORWARD = """
CREATE OR REPLACE FUNCTION col_colaborador_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF EXISTS (SELECT 1 FROM colaborador_papel WHERE colaborador_id = OLD.id)
       OR EXISTS (SELECT 1 FROM colaborador_habilidade WHERE colaborador_id = OLD.id)
       OR EXISTS (SELECT 1 FROM colaborador_documento WHERE colaborador_id = OLD.id)
    THEN
        RAISE EXCEPTION
            'INV-COL-INATIVO: DELETE físico de colaborador bloqueado — existem registros filhos '
            '(papéis/habilidades/documentos). Use desligamento (data_desligamento) ou '
            'soft-delete (deletado_em).';
    END IF;
    RETURN OLD;
END;
$body$;

CREATE TRIGGER colaborador_block_delete_trg
    BEFORE DELETE ON colaborador
    FOR EACH ROW EXECUTE FUNCTION col_colaborador_block_delete();
"""

SQL_REVERSE = """
DROP TRIGGER IF EXISTS colaborador_block_delete_trg ON colaborador;
DROP FUNCTION IF EXISTS col_colaborador_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("colaboradores", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
