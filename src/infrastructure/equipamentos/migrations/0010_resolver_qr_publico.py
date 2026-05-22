"""T-EQP-025 (AC-EQP-003-2 / INV-051) — funcao SECURITY DEFINER
`resolver_qr_publico` pra Escopo C (anonimo) de GET `/v1/qr/{hash}`.

Escopo A (autenticado mesmo tenant) usa caminho ORM normal (RLS aplica
e libera). Escopo B (autenticado outro tenant) cai em RLS e vira 404
indistinguivel (P-EQP-S2). Escopo C (anonimo) NAO tem `app.active_tenant_id`
seto — RLS bloqueia TUDO. Esta funcao SECURITY DEFINER ignora RLS
controladamente, retornando APENAS campos da allowlist Escopo C
(`docs/conformidade/equipamentos/qr-publico-allowlist.md`): tipo,
fabricante, modelo, status. NAO retorna tenant_id, cliente_id, tag,
numero_serie, localizacao, foto, historico, eventos.

Defesas:
- Lista de retorno FECHADA na assinatura (tipos crus, nao SELECT *).
- Filtro de soft-delete `eq.deletado_em IS NULL`.
- Filtro de revogacao `qr.revogado_em IS NULL`.
- REVOKE PUBLIC + GRANT EXECUTE TO app_user (mesma role da web app).
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
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
BEGIN
    -- Hash invalido (sem prefixo `qrN:`) retorna 0 linhas (404
    -- indistinguivel no caller).
    IF p_hash IS NULL OR position(':' IN p_hash) = 0 THEN
        RETURN;
    END IF;
    RETURN QUERY
    SELECT
        eq.id,
        eq.fabricante::text,
        eq.modelo::text,
        eq.status::text
    FROM equipamentos_qrcode qr
    JOIN equipamentos eq ON eq.id = qr.equipamento_id
    WHERE qr.hash = p_hash
      AND qr.revogado_em IS NULL
      AND eq.deletado_em IS NULL;
END;
$body$;

REVOKE EXECUTE ON FUNCTION resolver_qr_publico(text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION resolver_qr_publico(text) TO app_user;

COMMENT ON FUNCTION resolver_qr_publico(text) IS
'T-EQP-025 (INV-051) - resolve hash de QR publico (Escopo C anonimo). '
'Retorna APENAS campos da allowlist publica. NAO retorna tenant/cliente/'
'tag/NS/localizacao/foto/historico.';
"""

REVERSE = """
DROP FUNCTION IF EXISTS resolver_qr_publico(text);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("equipamentos", "0009_seed_authz_ficha360"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
