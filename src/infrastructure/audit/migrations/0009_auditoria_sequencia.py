"""FA-C1 — coluna `sequencia` monotonica na auditoria (SEQUENCE global).

Auditoria F-A rodada 1 (design FA-C1-design-hash-chain.md). A cadeia
hash precisa de ordem monotonica deterministica: `timestamp`
(auto_now_add) colide em microssegundo sob advisory lock e reordena
elos. Encadeamento e por-tenant (services.py filter tenant_id); a
sequencia so desempata a ordem dentro da cadeia.

Schema fica no app `audit` (dono do model Auditoria); as policies RLS
ficam em multitenant/0004. RunSQL + state_operations pra sincronizar o
Django state com a coluna criada via SQL (default vem do banco).

# tests-coverage: tests/test_audit_cadeia_por_tenant.py
"""

from __future__ import annotations

from django.db import migrations, models


FORWARD = """
CREATE SEQUENCE IF NOT EXISTS auditoria_seq;

-- ADD COLUMN com DEFAULT volatil (nextval) preenche TODAS as linhas
-- existentes — e DDL, NAO passa pela RLS policy. Um `UPDATE ... SET
-- sequencia` (DML) seria bloqueado: migrations rodam como app_migrator
-- (NOBYPASSRLS) e a policy UPDATE da auditoria chama require_tenant_ctx()
-- que RAISE sem contexto de tenant. Por isso NAO se faz backfill via UPDATE.
--
-- Trade-off aceito (tech-lead, FA-C1-design §"Riscos residuais"): a ordem
-- atribuida as linhas PRE-migration e a ordem fisica de varredura (heap),
-- nao (timestamp, id). Aceitavel: nao ha trilha de producao real (sem
-- cliente externo — memoria project_sem_cliente_externo_agora); o que
-- importa e o encadeamento monotonico DAQUI PRA FRENTE. Cadeias
-- pre-migration sao explicitamente nao-autoritativas.
ALTER TABLE auditoria
    ADD COLUMN IF NOT EXISTS sequencia BIGINT NOT NULL DEFAULT nextval('auditoria_seq');

CREATE INDEX IF NOT EXISTS ix_audit_cadeia_tenant_seq
    ON auditoria (tenant_id, sequencia);
"""

REVERSE = """
DROP INDEX IF EXISTS ix_audit_cadeia_tenant_seq;
ALTER TABLE auditoria ALTER COLUMN sequencia DROP NOT NULL;
ALTER TABLE auditoria ALTER COLUMN sequencia DROP DEFAULT;
ALTER TABLE auditoria DROP COLUMN IF EXISTS sequencia;
DROP SEQUENCE IF EXISTS auditoria_seq;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("audit", "0008_acesso_cliente_id_nullable"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD,
            reverse_sql=REVERSE,
            state_operations=[
                migrations.AddField(
                    model_name="auditoria",
                    name="sequencia",
                    field=models.BigIntegerField(
                        editable=False,
                        db_default=models.Func(
                            models.Value("auditoria_seq"), function="nextval"
                        ),
                    ),
                ),
            ],
        ),
    ]
