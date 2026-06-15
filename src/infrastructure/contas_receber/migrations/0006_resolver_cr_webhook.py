"""T-CR-036 — Resolver tenant do título por gateway_externo_id (webhook público SEM RLS).

O endpoint público `ContasReceberWebhookView` (POST /api/v1/public/contas-receber/webhook/)
precisa resolver o tenant a partir do `gateway_externo_id` ANTES de entrar em
`run_in_tenant_context` (galinha-ovo: FORCE RLS sem contexto = nenhuma linha visível).

Molde: `orcamentos/migrations/0009_resolver_orc_publico.py` (mesmo padrão D-ORC-19).

Mecanismo (bypass controlado de RLS — D-CR-8 / R7):
  - Policy `titulo_receber_webhook_resolver` libera SELECT em `titulo_receber` quando
    GUC `app.scope = 'cr_webhook_check'` está setado (escopo local à função).
  - Função `resolver_cr_titulo_por_gateway(p_gateway_id text)` (SECURITY DEFINER):
    seta GUC LOCAL → SELECT `(tenant_id, id)` por `gateway_externo_id` → reseta GUC →
    retorna APENAS `(tenant_id, titulo_id)` — NÃO retorna campos do título (lidos sob
    RLS normal pelo use case dentro do `run_in_tenant_context`).
  - REVOKE PUBLIC + GRANT app_user: só a role da web app executa.

Anti-oráculo (D-CR-8 / R7): gateway_id inexistente → 0 linhas → VIEW responde 401
indistinguível do HMAC inválido (sem diferença de corpo ou timing observable).

# rls-policy: external 0002_rls_policies (policy adicional de bypass escopado por GUC)
# tests-coverage: tests/test_contas_receber_webhook_fatia2b.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- Policy adicional: SELECT em titulo_receber quando o flag de webhook está setado
-- (somente dentro da função SECURITY DEFINER — bypass controlado de RLS).
CREATE POLICY titulo_receber_webhook_resolver ON titulo_receber
    FOR SELECT
    USING (current_setting('app.scope', true) = 'cr_webhook_check');

-- Função SECURITY DEFINER: resolve (tenant_id, titulo_id) por gateway_externo_id.
-- Não retorna outros campos do título (lidos sob RLS normal pelo use case).
CREATE OR REPLACE FUNCTION resolver_cr_titulo_por_gateway(p_gateway_id text)
RETURNS TABLE (
    tenant_id uuid,
    titulo_id uuid
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_tenant_id uuid;
    v_titulo_id uuid;
BEGIN
    -- gateway_id vazio/curto: 0 linhas (401 indistinguível no caller — anti-oráculo).
    IF p_gateway_id IS NULL OR length(p_gateway_id) < 4 THEN
        RETURN;
    END IF;
    -- Libera RLS controladamente apenas para o SELECT desta função.
    PERFORM set_config('app.scope', 'cr_webhook_check', true);
    SELECT tr.tenant_id, tr.id
        INTO v_tenant_id, v_titulo_id
    FROM titulo_receber tr
    WHERE tr.gateway_externo_id = p_gateway_id
      AND tr.gateway_externo_id <> ''
    LIMIT 1;
    -- Reseta o flag imediatamente (LOCAL = vive só na transação, mas reseta defensivamente).
    PERFORM set_config('app.scope', '', true);
    IF v_titulo_id IS NOT NULL THEN
        tenant_id := v_tenant_id;
        titulo_id := v_titulo_id;
        RETURN NEXT;
    END IF;
END;
$body$;

REVOKE EXECUTE ON FUNCTION resolver_cr_titulo_por_gateway(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolver_cr_titulo_por_gateway(text) TO app_user;

COMMENT ON FUNCTION resolver_cr_titulo_por_gateway(text) IS
'T-CR-036 (D-CR-8) - resolve gateway_externo_id para (tenant_id, titulo_id) sem RLS. '
'Bypass de RLS controlado por GUC app.scope=cr_webhook_check. '
'Retorna 0 linhas se inexistente (anti-oráculo = 401 igual ao HMAC inválido). '
'NAO retorna campos do título (lidos sob RLS normal pelo use case).';
"""

REVERSE = """
DROP FUNCTION IF EXISTS resolver_cr_titulo_por_gateway(text);
DROP POLICY IF EXISTS titulo_receber_webhook_resolver ON titulo_receber;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("contas_receber", "0005_seed_authz"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
