"""T-EQP-032 — funcao SECURITY DEFINER `resolver_qr_publico_tenant_id`
para lookup do tenant_id do equipamento dono de um QR publico.

Uso EXCLUSIVO em rate-limit global por tenant (escopo anonimo) — o
tenant_id NAO retorna no payload publico; e usado apenas para
contabilizar quota.

Defesa (mesmo padrao do migration 0010 + 0011 — owner e
`app_migrator` NOBYPASSRLS, logo SECURITY DEFINER nao basta):
- A funcao seta `app.scope='qr_publico_check'` via `set_config(...,
  true)` LOCAL antes do SELECT.
- Policy `equipamentos_publico_resolver` (criada em 0011) ja libera
  SELECT em `equipamentos` quando `app.scope='qr_publico_check'`.
- Reset do flag imediatamente apos.
- Lista de retorno MINIMA (so tenant_id; nao vaza tag/NS/PII).
- REVOKE PUBLIC + GRANT app_user (mesma role da web app).

# policy-test-coverage: skip -- funcao SECURITY DEFINER existente
# (resolver_qr_publico) ja tem padrao validado em 0010/0011; aqui
# replica para outra dimensao (tenant_id) com mesma policy.
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION resolver_qr_publico_tenant_id(p_hash text)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_tenant_id uuid;
BEGIN
    IF p_hash IS NULL OR position(':' IN p_hash) = 0 THEN
        RETURN NULL;
    END IF;
    -- Libera RLS controladamente (mesma policy do migration 0011).
    PERFORM set_config('app.scope', 'qr_publico_check', true);
    SELECT eq.tenant_id INTO v_tenant_id
    FROM equipamentos_qrcode qr
    JOIN equipamentos eq ON eq.id = qr.equipamento_id
    WHERE qr.hash = p_hash
      AND qr.revogado_em IS NULL
      AND eq.deletado_em IS NULL
    LIMIT 1;
    -- Reseta flag imediatamente.
    PERFORM set_config('app.scope', '', true);
    RETURN v_tenant_id;
END;
$body$;

REVOKE EXECUTE ON FUNCTION resolver_qr_publico_tenant_id(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolver_qr_publico_tenant_id(text) TO app_user;

COMMENT ON FUNCTION resolver_qr_publico_tenant_id(text) IS
'T-EQP-032 - lookup do tenant_id do equipamento dono de um QR publico. '
'Uso interno em rate-limit global por tenant; NAO retorna no payload publico.';
"""

REVERSE = """
DROP FUNCTION IF EXISTS resolver_qr_publico_tenant_id(text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("equipamentos", "0015_seed_authz_revogar_consentimento"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
