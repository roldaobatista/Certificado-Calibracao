"""FB-C1 — `sequencia` monotonica em authz_decisions (espelha audit/0009).

A cadeia hash authz precisa de ordem monotonica deterministica: `timestamp`
(auto_now_add) colide em microssegundo sob o advisory lock e reordena elos
(mesmo bug que FA-C1 matou na auditoria). Encadeamento e por-tenant OU
por-usuario (cadeia pre-tenant — FB-C3); `sequencia` so desempata.

`ADD COLUMN` com DEFAULT volatil (nextval) e DDL: preenche TODAS as linhas
existentes SEM passar por UPDATE (a policy/trigger anti-mutation so barra
UPDATE/DELETE de linha). Cadeias pre-migration sao nao-autoritativas (sem
cliente externo — memoria project_sem_cliente_externo_agora); o que importa
e o encadeamento monotonico daqui pra frente.

`hash_anterior` passa a NULL=True (alinha com Auditoria: NULL = primeira
linha da cadeia, em vez de string vazia — algoritmo unico FB-C1).

BLOQ #3 (review tech-lead): dep APENAS de authz/0003 — cada tabela tem sua
propria sequence; o helper compartilhado e runtime, nao schema. NAO depende
de audit/0009.

# tests-coverage: tests/test_authz_cadeia_pre_tenant.py
"""

from __future__ import annotations

from django.db import migrations, models

FORWARD = """
CREATE SEQUENCE IF NOT EXISTS authz_decisions_seq;

ALTER TABLE authz_decisions
    ADD COLUMN IF NOT EXISTS sequencia BIGINT NOT NULL
    DEFAULT nextval('authz_decisions_seq');

ALTER TABLE authz_decisions ALTER COLUMN hash_anterior DROP NOT NULL;

DROP INDEX IF EXISTS ix_authzdec_tenant_ts;
DROP INDEX IF EXISTS ix_authzdec_user_ts;

CREATE INDEX IF NOT EXISTS ix_authzdec_tenant_seq
    ON authz_decisions (tenant_id, sequencia);

-- Indice PARCIAL: caminho exato da leitura da cadeia pre-tenant POR-USUARIO
-- (review tech-lead Q2) — `.first()` O(log n) dentro do advisory lock.
CREATE INDEX IF NOT EXISTS ix_authzdec_user_seq_pretenant
    ON authz_decisions (usuario_id, sequencia)
    WHERE tenant_id IS NULL;
"""

REVERSE = """
DROP INDEX IF EXISTS ix_authzdec_user_seq_pretenant;
DROP INDEX IF EXISTS ix_authzdec_tenant_seq;
CREATE INDEX IF NOT EXISTS ix_authzdec_user_ts
    ON authz_decisions (usuario_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_authzdec_tenant_ts
    ON authz_decisions (tenant_id, timestamp);
ALTER TABLE authz_decisions ALTER COLUMN hash_anterior SET NOT NULL;
ALTER TABLE authz_decisions ALTER COLUMN sequencia DROP NOT NULL;
ALTER TABLE authz_decisions ALTER COLUMN sequencia DROP DEFAULT;
ALTER TABLE authz_decisions DROP COLUMN IF EXISTS sequencia;
DROP SEQUENCE IF EXISTS authz_decisions_seq;
"""


class Migration(migrations.Migration):
    # atomic=False: ALTER TABLE + CREATE INDEX em tabela com trigger pending.
    atomic = False

    dependencies = [
        ("authz", "0003_seed_perfis"),
    ]

    operations = [
        migrations.RunSQL(
            sql=FORWARD,
            reverse_sql=REVERSE,
            state_operations=[
                migrations.AddField(
                    model_name="authzdecision",
                    name="sequencia",
                    field=models.BigIntegerField(
                        editable=False,
                        db_default=models.Func(
                            models.Value("authz_decisions_seq"),
                            function="nextval",
                        ),
                    ),
                ),
                migrations.AlterField(
                    model_name="authzdecision",
                    name="hash_anterior",
                    field=models.CharField(
                        blank=True,
                        help_text=(
                            "SHA-256 da linha anterior na cadeia. " "NULL = primeira linha."
                        ),
                        max_length=64,
                        null=True,
                    ),
                ),
                migrations.AlterModelOptions(
                    name="authzdecision",
                    options={
                        "ordering": ["sequencia"],
                        "verbose_name": "Decisão de autorização (audit)",
                        "verbose_name_plural": "Decisões de autorização (audit)",
                    },
                ),
                migrations.RemoveIndex(
                    model_name="authzdecision",
                    name="ix_authzdec_tenant_ts",
                ),
                migrations.RemoveIndex(
                    model_name="authzdecision",
                    name="ix_authzdec_user_ts",
                ),
                migrations.AddIndex(
                    model_name="authzdecision",
                    index=models.Index(
                        fields=["tenant_id", "sequencia"],
                        name="ix_authzdec_tenant_seq",
                    ),
                ),
                migrations.AddIndex(
                    model_name="authzdecision",
                    index=models.Index(
                        fields=["usuario_id", "sequencia"],
                        name="ix_authzdec_user_seq_pretenant",
                        condition=models.Q(tenant_id__isnull=True),
                    ),
                ),
            ],
        ),
    ]
