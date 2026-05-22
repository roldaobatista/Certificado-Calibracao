"""T-EQP-025 patch — funcao `resolver_qr_publico` precisa de policy
de bypass controlado RLS.

Owner da funcao SECURITY DEFINER e `app_migrator` (NOBYPASSRLS). RLS
default bloqueia SELECT em `equipamentos_qrcode` e `equipamentos`
quando `app.tenant_ids`/`app.active_tenant_id` nao estao setados
(Escopo C anonimo NAO tem context — middleware bypass).

Solucao: policy adicional que LIBERA SELECT quando GUC `app.scope`
= 'qr_publico_check'. A funcao seta GUC LOCAL antes do SELECT e
reseta no fim. Defesa em camadas: so a propria funcao pode setar
esse flag (`SET LOCAL` so afeta a transacao corrente; chamadores
externos podem setar, mas se setarem viola convencao + auditor
seguranca pega).

# tests-coverage: tests/test_equipamentos_qr_publico_t_eqp_025.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- Policy adicional pra SELECT em equipamentos_qrcode com flag publico.
CREATE POLICY equipamentos_qrcode_publico_resolver ON equipamentos_qrcode
    FOR SELECT
    USING (current_setting('app.scope', true) = 'qr_publico_check');

-- Policy adicional pra SELECT em equipamentos com flag publico.
CREATE POLICY equipamentos_publico_resolver ON equipamentos
    FOR SELECT
    USING (current_setting('app.scope', true) = 'qr_publico_check');

-- Atualiza funcao pra setar o flag antes do SELECT.
CREATE OR REPLACE FUNCTION resolver_qr_publico(p_hash text)
RETURNS TABLE (
    equipamento_id uuid,
    fabricante text,
    modelo text,
    status text
)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_eq_id uuid;
    v_fab text;
    v_mod text;
    v_status text;
BEGIN
    IF p_hash IS NULL OR position(':' IN p_hash) = 0 THEN
        RETURN;
    END IF;
    -- Libera RLS controladamente apenas para SELECT desta funcao.
    PERFORM set_config('app.scope', 'qr_publico_check', true);
    SELECT eq.id, eq.fabricante::text, eq.modelo::text, eq.status::text
        INTO v_eq_id, v_fab, v_mod, v_status
    FROM equipamentos_qrcode qr
    JOIN equipamentos eq ON eq.id = qr.equipamento_id
    WHERE qr.hash = p_hash
      AND qr.revogado_em IS NULL
      AND eq.deletado_em IS NULL
    LIMIT 1;
    -- Reseta flag imediatamente.
    PERFORM set_config('app.scope', '', true);
    IF v_eq_id IS NOT NULL THEN
        equipamento_id := v_eq_id;
        fabricante := v_fab;
        modelo := v_mod;
        status := v_status;
        RETURN NEXT;
    END IF;
END;
$body$;

REVOKE EXECUTE ON FUNCTION resolver_qr_publico(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolver_qr_publico(text) TO app_user;
"""

REVERSE = """
DROP POLICY IF EXISTS equipamentos_qrcode_publico_resolver ON equipamentos_qrcode;
DROP POLICY IF EXISTS equipamentos_publico_resolver ON equipamentos;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("equipamentos", "0010_resolver_qr_publico"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
