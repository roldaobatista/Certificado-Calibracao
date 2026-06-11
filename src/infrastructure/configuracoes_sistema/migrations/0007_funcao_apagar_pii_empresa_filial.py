"""Conserto LGPD M5 da auditoria P9 (LGPD-MEC-003) — rota de eliminação de PII.

Função `apagar_pii_empresa_filial(p_tenant_id)`: anonimiza os campos de
CONTATO de `empresa` e `filial` (endereco/telefone/site/logo_url) no
offboarding/pedido do titular. PRESERVA razao_social/cnpj/nome/IE/IM —
prova fiscal enquanto houver documento no prazo legal (CTN art. 173/174;
contrato na linha Empresa/Filial de `docs/conformidade/comum/retencao-matriz.md`;
PII de MEI embutida no CNPJ segue a linha "Cadastro de cliente (tenant)" —
crypto-shredding no fim do prazo, não UPDATE).

Roda como caller (app_user) — RLS FORCE aplica: só anonimiza dentro do
contexto do próprio tenant (sem SECURITY DEFINER; defesa em profundidade).
Caller de produção = offboarding do tenant (ADR-0015 — Wave A); teste
PG-real direto em tests/test_configuracoes_schema_fatia1b.py.

# audit-immutability: funcao de eliminacao LGPD sobre tabelas de config mutavel
#   (empresa/filial — D-CFG-7, nao-WORM); nao toca cadeia de auditoria.
# tests-coverage: tests/test_configuracoes_schema_fatia1b.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
CREATE OR REPLACE FUNCTION apagar_pii_empresa_filial(p_tenant_id uuid)
RETURNS integer LANGUAGE plpgsql AS $body$
DECLARE
    n_empresa integer := 0;
    n_filial integer := 0;
BEGIN
    -- Contato da empresa: anonimiza. Identificacao fiscal (razao_social/cnpj/
    -- regime/IE/IM): preservada (retencao-matriz — prova fiscal no prazo).
    UPDATE empresa SET
        endereco = '',
        telefone = '',
        site = '',
        logo_url = ''
    WHERE tenant_id = p_tenant_id
      AND (endereco <> '' OR telefone <> '' OR site <> '' OR logo_url <> '');
    GET DIAGNOSTICS n_empresa = ROW_COUNT;

    UPDATE filial SET
        endereco = '',
        telefone = ''
    WHERE tenant_id = p_tenant_id
      AND (endereco <> '' OR telefone <> '');
    GET DIAGNOSTICS n_filial = ROW_COUNT;

    RETURN n_empresa + n_filial;
END;
$body$;
"""

REVERSE = """
DROP FUNCTION IF EXISTS apagar_pii_empresa_filial(uuid);
"""


class Migration(migrations.Migration):
    dependencies = [
        ("configuracoes_sistema", "0006_seed_authz_configuracoes"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
