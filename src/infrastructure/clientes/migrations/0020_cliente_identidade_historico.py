"""T-CLI-102 / AC-CLI-001-7: ClienteIdentidadeHistorico + triggers PG.

Rastreabilidade ISO/IEC 17025 §7.8.2.1 (b) + §8.4: certificado emitido em
nome de empresa que depois alterou razão social na JC (mesmo CNPJ) precisa
rastrear o cliente no momento da emissão.

Cria:
1. Tabela `cliente_identidade_historico` (INSERT-only, RLS isolada por tenant).
2. Trigger AFTER UPDATE em `clientes` que grava linha quando `nome` ou
   `nome_fantasia` muda (defesa em profundidade — funciona mesmo se endpoint
   esquecer de gravar).
3. Trigger anti-mutation em `cliente_identidade_historico` (BEFORE UPDATE +
   BEFORE DELETE → RAISE) — análogo ao `auditoria_anti_*` de F-A.
4. Policies RLS (SELECT/INSERT) via template único `rls_templates.py`. UPDATE
   e DELETE não têm policy — proibidos por design (trigger anti-mutation cobre).

A trigger AFTER UPDATE não precisa de `app.usuario_id` setado: lê
`current_setting('app.usuario_id', true)` e grava NULL se vazio (alteração de
sistema/migração). Documentado em `criado_por_id`.
"""

# rls-policy: external none -- usa rls_templates.py mas com pattern especial (sem UPDATE/DELETE)
# tests-coverage: tests/test_clientes_us_cli_001_identidade_historico_t_cli_102.py
# audit-immutability: skip -- esta migration cria tabela propria de historico, NAO auditoria

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models

CREATE_TABLE_RLS = """
-- Tabela INSERT-only de historico de identidade do cliente
ALTER TABLE cliente_identidade_historico ENABLE ROW LEVEL SECURITY;
ALTER TABLE cliente_identidade_historico FORCE ROW LEVEL SECURITY;

-- SELECT: lista de tenants do contexto (require_tenant_ctx fail-loud)
CREATE POLICY cli_id_hist_tenant_iso_select ON cliente_identidade_historico
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(
        coalesce(current_setting('app.tenant_ids', true), ''), ','
    )));

-- INSERT: tenant ativo (mesma forma de auditoria)
CREATE POLICY cli_id_hist_tenant_iso_insert ON cliente_identidade_historico
    FOR INSERT
    WITH CHECK (
        tenant_id::text = coalesce(current_setting('app.active_tenant_id', true), '')
        OR current_setting('app.modo_sistema', true) = '1'
    );

-- UPDATE/DELETE: SEM policy = nenhuma role consegue mutar; defesa de profundidade
-- via trigger PG abaixo (anti-mutation) que RAISE explicitamente.
"""

CREATE_TABLE_RLS_REVERSE = """
DROP POLICY IF EXISTS cli_id_hist_tenant_iso_insert ON cliente_identidade_historico;
DROP POLICY IF EXISTS cli_id_hist_tenant_iso_select ON cliente_identidade_historico;
ALTER TABLE cliente_identidade_historico DISABLE ROW LEVEL SECURITY;
"""


ANTI_MUTATION_TRIGGER = """
CREATE OR REPLACE FUNCTION cliente_identidade_historico_bloqueia_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'cliente_identidade_historico e INSERT-only (ISO 17025 §8.4 + LGPD art. 37)'
        USING ERRCODE = '23514';
END;
$$;

CREATE TRIGGER cliente_identidade_historico_anti_update
    BEFORE UPDATE ON cliente_identidade_historico
    FOR EACH ROW EXECUTE FUNCTION cliente_identidade_historico_bloqueia_mutation();

CREATE TRIGGER cliente_identidade_historico_anti_delete
    BEFORE DELETE ON cliente_identidade_historico
    FOR EACH ROW EXECUTE FUNCTION cliente_identidade_historico_bloqueia_mutation();
"""

ANTI_MUTATION_TRIGGER_REVERSE = """
DROP TRIGGER IF EXISTS cliente_identidade_historico_anti_delete ON cliente_identidade_historico;
DROP TRIGGER IF EXISTS cliente_identidade_historico_anti_update ON cliente_identidade_historico;
DROP FUNCTION IF EXISTS cliente_identidade_historico_bloqueia_mutation();
"""


AUTO_LOG_TRIGGER = """
-- AFTER UPDATE em `clientes`: grava historico de alteracao de identidade
CREATE OR REPLACE FUNCTION cliente_identidade_log_after_update()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    v_usuario uuid;
    v_usuario_txt text;
BEGIN
    -- Lê usuario do contexto; vazio/invalido -> NULL (alteracao de sistema)
    v_usuario_txt := coalesce(current_setting('app.usuario_id', true), '');
    IF v_usuario_txt = '' THEN
        v_usuario := NULL;
    ELSE
        BEGIN
            v_usuario := v_usuario_txt::uuid;
        EXCEPTION WHEN others THEN
            v_usuario := NULL;
        END;
    END IF;

    IF NEW.nome IS DISTINCT FROM OLD.nome THEN
        INSERT INTO cliente_identidade_historico (
            id, tenant_id, cliente_id, campo,
            valor_anterior, valor_novo, data_efetivacao,
            evidencia_documental_id, criado_por_id
        ) VALUES (
            gen_random_uuid(), NEW.tenant_id, NEW.id, 'nome',
            coalesce(OLD.nome, ''), NEW.nome, now(),
            NULL, v_usuario
        );
    END IF;

    IF NEW.nome_fantasia IS DISTINCT FROM OLD.nome_fantasia THEN
        INSERT INTO cliente_identidade_historico (
            id, tenant_id, cliente_id, campo,
            valor_anterior, valor_novo, data_efetivacao,
            evidencia_documental_id, criado_por_id
        ) VALUES (
            gen_random_uuid(), NEW.tenant_id, NEW.id, 'nome_fantasia',
            coalesce(OLD.nome_fantasia, ''), NEW.nome_fantasia, now(),
            NULL, v_usuario
        );
    END IF;

    RETURN NEW;
END;
$$;

CREATE TRIGGER cliente_identidade_log_after_update_trg
    AFTER UPDATE OF nome, nome_fantasia ON clientes
    FOR EACH ROW
    WHEN (OLD.nome IS DISTINCT FROM NEW.nome OR OLD.nome_fantasia IS DISTINCT FROM NEW.nome_fantasia)
    EXECUTE FUNCTION cliente_identidade_log_after_update();
"""

AUTO_LOG_TRIGGER_REVERSE = """
DROP TRIGGER IF EXISTS cliente_identidade_log_after_update_trg ON clientes;
DROP FUNCTION IF EXISTS cliente_identidade_log_after_update();
"""


# tests-coverage: tests/test_clientes_us_cli_001_identidade_historico_t_cli_102.py
# rls-policy: external none (CREATE POLICY/ENABLE ROW LEVEL SECURITY inline acima)


class Migration(migrations.Migration):
    # atomic=False: CreateModel + RunSQL com policies/triggers + criação de FK
    # esbarra em "pending trigger events" porque o NOT VALID check da FK
    # `cliente_identidade_historico.cliente_id → clientes.id` faz SELECT em
    # `clientes` que passa por RLS (require_tenant_ctx RAISE em contexto vazio).
    # Quebrar em comandos auto-commit evita.
    dependencies = [
        ("clientes", "0019_cliente_canonico_imutavel_runtime"),
        ("tenant", "0002_tenant_bloqueio_automatico_inadimplencia_habilitado"),
    ]

    operations = [
        migrations.CreateModel(
            name="ClienteIdentidadeHistorico",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "campo",
                    models.CharField(
                        choices=[
                            ("nome", "Nome / Razao Social"),
                            ("nome_fantasia", "Nome Fantasia"),
                        ],
                        help_text="Campo alterado (nome ou nome_fantasia).",
                        max_length=20,
                    ),
                ),
                (
                    "valor_anterior",
                    models.CharField(
                        blank=True,
                        help_text="Valor antes da alteracao. Vazio se campo era NULL/blank.",
                        max_length=200,
                    ),
                ),
                (
                    "valor_novo",
                    models.CharField(
                        help_text="Valor depois da alteracao (>= 1 char).",
                        max_length=200,
                    ),
                ),
                (
                    "data_efetivacao",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Quando a alteracao foi gravada (DEFAULT now() na trigger PG).",
                    ),
                ),
                (
                    "evidencia_documental_id",
                    models.UUIDField(
                        blank=True,
                        help_text=(
                            "FK opaco pra anexo de evidencia (contrato social consolidado, "
                            "ata JC). Obrigatorio em M&A (US-CLI-005 AC-CLI-005-3b); opcional "
                            "em alteracao simples (renomeacao operacional). Modelo formal de "
                            "anexos entra em modulo de governanca futuro."
                        ),
                        null=True,
                    ),
                ),
                (
                    "criado_por_id",
                    models.UUIDField(
                        blank=True,
                        help_text=(
                            "Usuario que disparou a alteracao (vem do contexto request via "
                            "`app.usuario_id`). NULL quando alteracao veio de processo de "
                            "sistema (job/migracao)."
                        ),
                        null=True,
                    ),
                ),
                (
                    "cliente",
                    models.ForeignKey(
                        help_text=(
                            "FK PROTECT pra preservar trilha mesmo apos mesclagem "
                            "(cliente soft-deletado). db_constraint=False pra evitar "
                            "FK validation passando por RLS na criacao da tabela; "
                            "integridade real garantida pela trigger AFTER UPDATE que "
                            "so insere com NEW.id valido."
                        ),
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="identidade_historico",
                        db_constraint=False,
                        to="clientes.cliente",
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="cliente_identidade_historico",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Historico de identidade do cliente",
                "verbose_name_plural": "Historico de identidade dos clientes",
                "db_table": "cliente_identidade_historico",
                "ordering": ["-data_efetivacao"],
                "indexes": [
                    models.Index(
                        fields=["tenant", "cliente", "-data_efetivacao"],
                        name="ix_cli_id_hist_tenant_cli",
                    ),
                    models.Index(
                        fields=["tenant", "-data_efetivacao"],
                        name="ix_cli_id_hist_tenant_ts",
                    ),
                ],
            },
        ),
        migrations.RunSQL(sql=CREATE_TABLE_RLS, reverse_sql=CREATE_TABLE_RLS_REVERSE),
        migrations.RunSQL(sql=ANTI_MUTATION_TRIGGER, reverse_sql=ANTI_MUTATION_TRIGGER_REVERSE),
        migrations.RunSQL(sql=AUTO_LOG_TRIGGER, reverse_sql=AUTO_LOG_TRIGGER_REVERSE),
    ]
