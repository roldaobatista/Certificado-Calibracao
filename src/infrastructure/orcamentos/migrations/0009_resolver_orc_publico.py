"""T-ORC-038 (Onda 2e) — resolução de token do link público SEM RLS (D-ORC-19).

O endpoint público `/api/v1/public/orcamentos/{token}` precisa resolver o tenant a
partir do token opaco ANTES de entrar em `run_in_tenant_context` (galinha-ovo). A
tabela `orcamento_link_publico` tem FORCE RLS — sem contexto de tenant, nenhuma
linha é visível. Molde: `resolver_qr_publico` (equipamentos migrations 0011/0016).

Mecanismo (bypass controlado de RLS):
  - Policy `orcamento_link_publico_publico_resolver` libera SELECT quando o GUC
    `app.scope = 'orc_publico_check'` está setado.
  - Função `resolver_orc_publico_token` (SECURITY DEFINER) seta o flag LOCAL, faz
    o SELECT por token, reseta o flag e retorna o mínimo (tenant_id, orcamento_id,
    link_id, expira_em, revogado_em). A view checa expiração/revogação e então
    entra em `run_in_tenant_context(tenant_id)` para o resto (RLS normal aplica).
  - REVOKE PUBLIC + GRANT app_user — só a role da web app executa.

NÃO retorna dados do orçamento (número/itens/valores) — isso é lido sob RLS dentro
do contexto. A função expõe só o necessário para resolver o tenant (D-ORC-19).

# rls-policy: external 0002_rls_policies (adiciona policy de bypass escopada por GUC)
# tests-coverage: tests/test_orcamentos_publico.py
# (resolve token; cross-tenant cravado na Fatia 3 — T-ORC-052)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- Policy adicional: SELECT em orcamento_link_publico quando o flag publico
-- esta setado (somente dentro da funcao SECURITY DEFINER).
CREATE POLICY orcamento_link_publico_publico_resolver ON orcamento_link_publico
    FOR SELECT
    USING (current_setting('app.scope', true) = 'orc_publico_check');

CREATE OR REPLACE FUNCTION resolver_orc_publico_token(p_token text)
RETURNS TABLE (
    tenant_id uuid,
    orcamento_id uuid,
    link_id uuid,
    expira_em timestamptz,
    revogado_em timestamptz,
    criado_em timestamptz
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_tenant_id uuid;
    v_orcamento_id uuid;
    v_link_id uuid;
    v_expira_em timestamptz;
    v_revogado_em timestamptz;
    v_criado_em timestamptz;
BEGIN
    -- Token vazio/curto: 0 linhas (404 indistinguivel no caller).
    IF p_token IS NULL OR length(p_token) < 16 THEN
        RETURN;
    END IF;
    -- Libera RLS controladamente apenas para o SELECT desta funcao.
    PERFORM set_config('app.scope', 'orc_publico_check', true);
    SELECT lp.tenant_id, lp.orcamento_id, lp.id, lp.expira_em, lp.revogado_em, lp.criado_em
        INTO v_tenant_id, v_orcamento_id, v_link_id, v_expira_em, v_revogado_em, v_criado_em
    FROM orcamento_link_publico lp
    WHERE lp.token = p_token
    LIMIT 1;
    -- Reseta o flag imediatamente.
    PERFORM set_config('app.scope', '', true);
    IF v_link_id IS NOT NULL THEN
        tenant_id := v_tenant_id;
        orcamento_id := v_orcamento_id;
        link_id := v_link_id;
        expira_em := v_expira_em;
        revogado_em := v_revogado_em;
        criado_em := v_criado_em;
        RETURN NEXT;
    END IF;
END;
$body$;

REVOKE EXECUTE ON FUNCTION resolver_orc_publico_token(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolver_orc_publico_token(text) TO app_user;

COMMENT ON FUNCTION resolver_orc_publico_token(text) IS
'T-ORC-038 (D-ORC-19) - resolve token opaco de link publico de orcamento para '
'(tenant_id, orcamento_id, link_id, expira_em, revogado_em). Bypass de RLS '
'controlado por GUC app.scope. NAO retorna dados do orcamento (lidos sob RLS).';
"""

REVERSE = """
DROP FUNCTION IF EXISTS resolver_orc_publico_token(text);
DROP POLICY IF EXISTS orcamento_link_publico_publico_resolver ON orcamento_link_publico;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0008_item_mensurando_solicitado"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
