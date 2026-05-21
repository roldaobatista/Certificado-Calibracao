"""Conserto causa-raiz ALTO-1 do Auditor de Segurança P5 (2026-05-21).

Substitui o cálculo de `documento_hash` no trigger
`trg_clientes_grava_op_tratamento` (migration 0014) — antes
`encode(sha256(NEW.documento::bytea), 'hex')` (SHA256 cru, rainbow-
table trivial; viola SANEA-02 + regra geral HMAC por-tenant) — agora
chama função SQL `pii_hash_hmac(text, uuid)` que:

1. Lê chave HMAC ativa de `current_setting('app.pii_hash_key_ativa')`
   (hex string setada por `setar_contexto_pg_na_conexao`).
2. Lê id da chave de `current_setting('app.pii_hash_key_ativa_id')`.
3. Calcula HMAC-SHA256 sobre `<tenant_id>:<valor>` (mesma mensagem
   que `hashear_pii_com_salt_tenant` em Python).
4. Retorna formato `<key_id>:<hex>` (compatível com
   `verificar_pii_hash`).
5. Fail-loud (RAISE) se GUC ausente/vazia — nenhum hash inseguro
   silencioso.

Espelha SANEA-02 + FA-A1: hash versionado por chave, HMAC com salt
por-tenant, fail-loud sem GUC. Cobertura defensiva BLOQ-TL-T4
preservada (trigger pega `.update()`, bulk_update, raw SQL).

# tests-coverage: tests/test_audit_documento_hash_hmac_t_sec1.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- Função pii_hash_hmac(valor, tenant_id) — HMAC-SHA256 versionado
-- Compatível bit-a-bit com `hashear_pii_com_salt_tenant` em Python.
-- =============================================================
CREATE OR REPLACE FUNCTION pii_hash_hmac(valor text, p_tenant_id uuid)
RETURNS text LANGUAGE plpgsql AS $body$
DECLARE
    v_chave_hex text;
    v_chave_id text;
    v_chave bytea;
    v_msg bytea;
    v_digest bytea;
BEGIN
    IF valor IS NULL OR valor = '' THEN
        RETURN '';
    END IF;
    IF p_tenant_id IS NULL THEN
        RAISE EXCEPTION 'pii_hash_hmac exige tenant_id (SANEA-02)';
    END IF;

    v_chave_hex := current_setting('app.pii_hash_key_ativa', true);
    v_chave_id := current_setting('app.pii_hash_key_ativa_id', true);

    IF v_chave_hex IS NULL OR v_chave_hex = ''
       OR v_chave_id IS NULL OR v_chave_id = '' THEN
        RAISE EXCEPTION
            'pii_hash_hmac: app.pii_hash_key_ativa ausente — '
            'contexto PG sem chave HMAC (SANEA-02 + FA-A1 fail-loud)';
    END IF;

    v_chave := decode(v_chave_hex, 'hex');
    v_msg := convert_to(p_tenant_id::text || ':' || valor, 'UTF8');
    v_digest := hmac(v_msg, v_chave, 'sha256');
    RETURN v_chave_id || ':' || encode(v_digest, 'hex');
END;
$body$;

-- =============================================================
-- Substitui função do trigger pra usar pii_hash_hmac
-- =============================================================
CREATE OR REPLACE FUNCTION trg_clientes_grava_op_tratamento()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE
    v_finalidade text;
    v_usuario_id uuid;
    v_app_user_id text;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_finalidade := 'cadastro';
    ELSIF TG_OP = 'UPDATE' THEN
        v_finalidade := 'edicao';
    ELSE
        RETURN NEW;
    END IF;

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
            -- ALTO-1 P5 conserto: HMAC versionado + salt por-tenant,
            -- não SHA256 cru. Compatível com hashear_pii_com_salt_tenant.
            'documento_hash', pii_hash_hmac(NEW.documento, NEW.tenant_id)
        ),
        now()
    );
    RETURN NEW;
END;
$body$;
"""

REVERSE = """
-- Volta trigger pra versão SHA256 cru (migration 0014).
CREATE OR REPLACE FUNCTION trg_clientes_grava_op_tratamento()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE
    v_finalidade text;
    v_usuario_id uuid;
    v_app_user_id text;
BEGIN
    IF TG_OP = 'INSERT' THEN
        v_finalidade := 'cadastro';
    ELSIF TG_OP = 'UPDATE' THEN
        v_finalidade := 'edicao';
    ELSE
        RETURN NEW;
    END IF;
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
        gen_random_uuid(), NEW.tenant_id, NEW.id, v_usuario_id, v_finalidade,
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
DROP FUNCTION IF EXISTS pii_hash_hmac(text, uuid);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("audit", "0014_operacao_tratamento_cliente"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
