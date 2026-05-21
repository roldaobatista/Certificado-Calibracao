"""Tabela `idempotencia_chave` + RLS + trigger imutabilidade pos-terminal.

Coverage:
- INV-TENANT-001/002/003: RLS pattern v2 (SELECT/UPDATE/DELETE/INSERT).
- P-EQP-T6 / T-EQP-003: trigger `chave_idempotencia_imutavel_pos_terminal`
  bloqueia UPDATE em registros com status='concluida' OU 'falhada'
  (transicao em_processo→{concluida,falhada} permitida UMA vez).
- UNIQUE composto `(tenant_id, endpoint, chave)`: 2 tenants podem usar
  mesmo UUID sem colisao (RLS + UNIQUE composto cobrem o caso).

# tests-coverage: tests/test_equipamentos_etiqueta_idempotency_t_eqp_003.py
"""

from __future__ import annotations

import uuid

import django.db.models.deletion
from django.db import migrations, models

FORWARD_RLS_TRIGGER = """
-- =============================================================
-- RLS pattern v2 (ADR-0002 §6) — chave e tenant-scoped
-- =============================================================
ALTER TABLE idempotencia_chave ENABLE ROW LEVEL SECURITY;
ALTER TABLE idempotencia_chave FORCE ROW LEVEL SECURITY;

CREATE POLICY chave_idempotencia_tenant_isolation_select ON idempotencia_chave
    FOR SELECT
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY chave_idempotencia_tenant_isolation_update ON idempotencia_chave
    FOR UPDATE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')))
    WITH CHECK (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY chave_idempotencia_tenant_isolation_delete ON idempotencia_chave
    FOR DELETE
    USING (tenant_id::text = ANY(string_to_array(current_setting('app.tenant_ids'), ',')));

CREATE POLICY chave_idempotencia_tenant_isolation_insert ON idempotencia_chave
    FOR INSERT
    WITH CHECK (tenant_id = current_setting('app.active_tenant_id')::uuid);

-- =============================================================
-- Trigger: imutabilidade pos-terminal (P-EQP-T6)
--
-- Apos transicao em_processo -> {concluida, falhada} a linha NUNCA
-- pode mudar de novo. Garante replay deterministico (cliente recebe
-- a MESMA resposta do 1o processamento, sempre).
--
-- Permite UPDATE somente quando OLD.status='em_processo'. Bloqueia
-- qualquer outra mutacao (inclusive em_processo -> em_processo, que
-- nao faz sentido).
-- =============================================================
CREATE OR REPLACE FUNCTION chave_idempotencia_imutavel_pos_terminal_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.status IN ('concluida', 'falhada') THEN
        RAISE EXCEPTION 'P-EQP-T6: chave idempotencia % imutavel apos status terminal (%)',
            OLD.id, OLD.status;
    END IF;
    -- Campos que NUNCA podem mudar mesmo em transicao em_processo -> terminal.
    IF OLD.tenant_id IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION 'INV-TENANT-001: tenant_id da chave imutavel';
    END IF;
    IF OLD.endpoint IS DISTINCT FROM NEW.endpoint THEN
        RAISE EXCEPTION 'P-EQP-T6: endpoint da chave imutavel';
    END IF;
    IF OLD.chave IS DISTINCT FROM NEW.chave THEN
        RAISE EXCEPTION 'P-EQP-T6: chave (UUID cliente) imutavel';
    END IF;
    IF OLD.payload_hash IS DISTINCT FROM NEW.payload_hash THEN
        RAISE EXCEPTION 'P-EQP-T6: payload_hash imutavel apos INSERT';
    END IF;
    IF OLD.usuario_id IS DISTINCT FROM NEW.usuario_id THEN
        RAISE EXCEPTION 'P-EQP-T6: usuario_id (autoria) imutavel';
    END IF;
    IF OLD.criada_em IS DISTINCT FROM NEW.criada_em THEN
        RAISE EXCEPTION 'AUDIT: criada_em imutavel';
    END IF;
    IF OLD.expira_em IS DISTINCT FROM NEW.expira_em THEN
        RAISE EXCEPTION 'P-EQP-T6: expira_em fixado no INSERT (TTL imutavel)';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER chave_idempotencia_imutavel_pos_terminal_trg
    BEFORE UPDATE ON idempotencia_chave
    FOR EACH ROW
    EXECUTE FUNCTION chave_idempotencia_imutavel_pos_terminal_check();
"""

REVERSE_RLS_TRIGGER = """
DROP TRIGGER IF EXISTS chave_idempotencia_imutavel_pos_terminal_trg ON idempotencia_chave;
DROP FUNCTION IF EXISTS chave_idempotencia_imutavel_pos_terminal_check();
DROP POLICY IF EXISTS chave_idempotencia_tenant_isolation_insert ON idempotencia_chave;
DROP POLICY IF EXISTS chave_idempotencia_tenant_isolation_delete ON idempotencia_chave;
DROP POLICY IF EXISTS chave_idempotencia_tenant_isolation_update ON idempotencia_chave;
DROP POLICY IF EXISTS chave_idempotencia_tenant_isolation_select ON idempotencia_chave;
ALTER TABLE idempotencia_chave DISABLE ROW LEVEL SECURITY;
"""


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("tenant", "0002_tenant_bloqueio_automatico_inadimplencia_habilitado"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChaveIdempotencia",
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
                    "endpoint",
                    models.CharField(
                        help_text=(
                            "Identificador estavel do endpoint (ex: "
                            "'equipamentos.etiqueta', 'equipamentos.transferir'). "
                            "NUNCA trocar sem migracao consciente — chaves "
                            "antigas viram orfas."
                        ),
                        max_length=120,
                    ),
                ),
                (
                    "chave",
                    models.UUIDField(
                        help_text=(
                            "UUID enviado pelo cliente no header `Idempotency-Key`. "
                            "Cliente gera UMA vez antes da 1a tentativa (RFC draft "
                            "ietf-httpapi-idempotency-key-header)."
                        ),
                    ),
                ),
                (
                    "payload_hash",
                    models.CharField(
                        help_text=(
                            "SHA256-hex do payload normalizado (resource_id + body). "
                            "Mesma `chave` com payload_hash diferente → 422 "
                            "(politica P-EQP-T6)."
                        ),
                        max_length=64,
                    ),
                ),
                (
                    "usuario_id",
                    models.UUIDField(
                        help_text=(
                            "Quem fez a chamada (autoria). Defesa em profundidade: "
                            "chave criada por user A nao pode ser replayed por user "
                            "B (mesmo tenant) — service compara antes de aceitar."
                        ),
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("em_processo", "Em processo"),
                            ("concluida", "Concluida"),
                            ("falhada", "Falhada"),
                        ],
                        default="em_processo",
                        max_length=20,
                    ),
                ),
                (
                    "response_status",
                    models.SmallIntegerField(
                        blank=True,
                        help_text="HTTP status devolvido na 1a execucao (replay devolve igual).",
                        null=True,
                    ),
                ),
                (
                    "response_body_resumo",
                    models.JSONField(
                        blank=True,
                        help_text=(
                            "Resumo determinante da resposta (NUNCA PDF/binario). "
                            "Para etiqueta: {qrcode_id, equipamento_tag}. Permite "
                            "que a 2a chamada re-renderize o mesmo artefato sem "
                            "armazenar binarios no DB."
                        ),
                        null=True,
                    ),
                ),
                ("criada_em", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "concluida_em",
                    models.DateTimeField(
                        blank=True,
                        help_text="Timestamp da transicao para `concluida` ou `falhada`.",
                        null=True,
                    ),
                ),
                (
                    "expira_em",
                    models.DateTimeField(
                        db_index=True,
                        help_text=(
                            "criada_em + TTL (24h padrao). Apos esta data, replay "
                            "retorna 409 (chave expirada — politica P-EQP-T6)."
                        ),
                    ),
                ),
                (
                    "tenant",
                    models.ForeignKey(
                        help_text="Denormalizado pra RLS (mesmo padrao Marco 1).",
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="chaves_idempotencia",
                        to="tenant.tenant",
                    ),
                ),
            ],
            options={
                "verbose_name": "Chave de idempotencia",
                "verbose_name_plural": "Chaves de idempotencia",
                "db_table": "idempotencia_chave",
                "ordering": ["-criada_em"],
            },
        ),
        migrations.AddConstraint(
            model_name="chaveidempotencia",
            constraint=models.UniqueConstraint(
                fields=("tenant", "endpoint", "chave"),
                name="idempotencia_chave_uniq_tenant_endpoint",
            ),
        ),
        migrations.AddIndex(
            model_name="chaveidempotencia",
            index=models.Index(fields=["expira_em"], name="idempotenci_expira__db3a82_idx"),
        ),
        migrations.AddIndex(
            model_name="chaveidempotencia",
            index=models.Index(
                fields=["tenant", "endpoint", "status"],
                name="idempotenci_tenant__cf9d33_idx",
            ),
        ),
        migrations.RunSQL(sql=FORWARD_RLS_TRIGGER, reverse_sql=REVERSE_RLS_TRIGGER),
    ]
