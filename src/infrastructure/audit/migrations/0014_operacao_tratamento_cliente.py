"""T-CLI-120 (AC-CLI-006-7) — tabela `operacao_tratamento_cliente` +
trigger PG AFTER INSERT/UPDATE em `clientes` (LGPD art. 37).

BLOQ-TL-T4 tech-lead: signal Django nao pega `.update()`,
`bulk_update`, raw SQL — trigger PG cobre 100%. Usa `app.usuario_id`
+ `app.modo_sistema` do contexto pra detectar autor.

INSERT-only (trigger anti-mutation). RLS FORCE. CHECK enum finalidade.

# tests-coverage: tests/test_us_cli_006_op_tratamento_t_cli_120.py
# rls-policy: external 0014
"""

from __future__ import annotations

from django.db import migrations, models

FORWARD = """
-- =====================================
-- RLS FORCE igual padroes do projeto
-- # tests-coverage: tests/test_us_cli_006_op_tratamento_t_cli_120.py
-- =====================================
ALTER TABLE operacao_tratamento_cliente ENABLE ROW LEVEL SECURITY;
ALTER TABLE operacao_tratamento_cliente FORCE ROW LEVEL SECURITY;

CREATE POLICY op_trat_cli_select ON operacao_tratamento_cliente
    FOR SELECT
    USING (
        CASE
            WHEN current_setting('app.modo_sistema', true) = '1'
                THEN TRUE
            ELSE tenant_id::text = ANY(
                string_to_array(require_tenant_ctx(), ',')
            )
        END
    );

CREATE POLICY op_trat_cli_insert ON operacao_tratamento_cliente
    FOR INSERT
    WITH CHECK (
        (current_setting('app.modo_sistema', true) = '1')
        OR
        (tenant_id::text = current_setting('app.active_tenant_id'))
    );

-- INSERT-only: bloqueia UPDATE/DELETE em RLS (trigger reforca em PG-level).
CREATE POLICY op_trat_cli_no_update ON operacao_tratamento_cliente
    FOR UPDATE USING (false);

CREATE POLICY op_trat_cli_no_delete ON operacao_tratamento_cliente
    FOR DELETE USING (false);

-- =====================================
-- CHECK enum finalidade
-- =====================================
ALTER TABLE operacao_tratamento_cliente
    ADD CONSTRAINT ck_op_trat_finalidade_enum CHECK (
        finalidade IN (
            'cadastro', 'edicao', 'export', 'compartilhamento_intermodular'
        )
    );

-- =====================================
-- Trigger PG AFTER INSERT/UPDATE em clientes (BLOQ-TL-T4)
-- Cobre `.update()`, bulk_update, raw SQL — signal Django nao alcanca.
-- =====================================
CREATE OR REPLACE FUNCTION trg_clientes_grava_op_tratamento()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE
    v_finalidade text;
    v_usuario_id uuid;
    v_app_user_id text;
BEGIN
    -- TG_OP = 'INSERT' -> finalidade=CADASTRO; 'UPDATE' -> EDICAO.
    IF TG_OP = 'INSERT' THEN
        v_finalidade := 'cadastro';
    ELSIF TG_OP = 'UPDATE' THEN
        v_finalidade := 'edicao';
    ELSE
        RETURN NEW;
    END IF;

    -- Lê usuario do contexto; NULL se sistema (cron, job).
    v_app_user_id := current_setting('app.usuario_id', true);
    IF v_app_user_id = '' OR v_app_user_id IS NULL THEN
        v_usuario_id := NULL;
    ELSE
        BEGIN
            v_usuario_id := v_app_user_id::uuid;
        EXCEPTION WHEN OTHERS THEN
            v_usuario_id := NULL;
        END;
    END IF;

    INSERT INTO operacao_tratamento_cliente
        (id, tenant_id, cliente_id, usuario_id, finalidade, payload, timestamp)
    VALUES (
        gen_random_uuid(),
        NEW.tenant_id,
        NEW.id,
        v_usuario_id,
        v_finalidade,
        jsonb_build_object(
            'base_legal', COALESCE(NEW.aceite_lgpd_base_legal, ''),
            'finalidade_negocial', COALESCE(NEW.aceite_lgpd_origem, ''),
            'documento_hash', encode(sha256(NEW.documento::bytea), 'hex')
        ),
        now()
    );
    RETURN NEW;
END;
$body$;

CREATE TRIGGER clientes_op_tratamento_trg
    AFTER INSERT OR UPDATE ON clientes
    FOR EACH ROW
    EXECUTE FUNCTION trg_clientes_grava_op_tratamento();
"""

REVERSE = """
DROP TRIGGER IF EXISTS clientes_op_tratamento_trg ON clientes;
DROP FUNCTION IF EXISTS trg_clientes_grava_op_tratamento();
ALTER TABLE operacao_tratamento_cliente DROP CONSTRAINT IF EXISTS ck_op_trat_finalidade_enum;
DROP POLICY IF EXISTS op_trat_cli_no_delete ON operacao_tratamento_cliente;
DROP POLICY IF EXISTS op_trat_cli_no_update ON operacao_tratamento_cliente;
DROP POLICY IF EXISTS op_trat_cli_insert ON operacao_tratamento_cliente;
DROP POLICY IF EXISTS op_trat_cli_select ON operacao_tratamento_cliente;
ALTER TABLE operacao_tratamento_cliente DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0013_breaker_acesso_pii_policy_endurece"),
        ("multitenant", "0004_audit_hash_chain_por_tenant"),
        ("clientes", "0021_us_cli_006_data_nascimento_observacao"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperacaoTratamentoCliente",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=__import__("uuid").uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("tenant_id", models.UUIDField(db_index=True)),
                ("cliente_id", models.UUIDField(db_index=True)),
                ("usuario_id", models.UUIDField(blank=True, db_index=True, null=True)),
                (
                    "finalidade",
                    models.CharField(
                        choices=[
                            ("cadastro", "Cadastro inicial"),
                            ("edicao", "Edicao de cadastro"),
                            ("export", "Exportacao de dados do cliente"),
                            (
                                "compartilhamento_intermodular",
                                "Compartilhamento entre modulos do Afere (OS, NF, etc)",
                            ),
                        ],
                        help_text="Enum FinalidadeTratamentoCliente. CHECK no banco.",
                        max_length=40,
                    ),
                ),
                (
                    "payload",
                    models.JSONField(
                        default=dict,
                        help_text="`base_legal` + `finalidade_negocial` "
                        "(BLOQ-A7 advogado) + metadados sanitizados.",
                    ),
                ),
                (
                    "timestamp",
                    models.DateTimeField(auto_now_add=True, db_index=True),
                ),
            ],
            options={
                "db_table": "operacao_tratamento_cliente",
                "verbose_name": "Operacao de tratamento de cliente (LGPD art. 37)",
                "verbose_name_plural": "Operacoes de tratamento de clientes",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddIndex(
            model_name="operacaotratamentocliente",
            index=models.Index(
                fields=["tenant_id", "cliente_id", "-timestamp"],
                name="ix_op_trat_tenant_cli_ts",
            ),
        ),
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
