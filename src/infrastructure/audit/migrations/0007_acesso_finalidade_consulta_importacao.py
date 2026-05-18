"""US-CLI-003 R7 advogado: adiciona finalidade `consulta_relatorio_importacao`
ao CHECK enum de `acessos_dados_cliente`.

Leitura do historico de importacoes dispara INV-013 (log de acesso a dado de
cliente). Como AcessoDadosCliente exige finalidade em enum, precisamos
acrescentar o valor antes que a view passe a registrar.

DROP + CREATE da constraint eh necessario porque PG nao permite ALTER em CHECK.
"""

# rls-policy: external 0006 -- a tabela ja tem RLS; aqui so atualiza CHECK enum
# tests-coverage: tests/test_clientes_us_cli_003_importar.py

from __future__ import annotations

from django.db import migrations


ALTER_SQL = """
ALTER TABLE acessos_dados_cliente
    DROP CONSTRAINT IF EXISTS chk_acesso_finalidade_enum;

ALTER TABLE acessos_dados_cliente
    ADD CONSTRAINT chk_acesso_finalidade_enum
    CHECK (finalidade IN (
        'atendimento_pos_venda',
        'preparar_orcamento',
        'executar_os',
        'emitir_documento_fiscal',
        'cobranca_inadimplencia',
        'auditoria_interna',
        'atendimento_lgpd_titular',
        'investigacao_incidente',
        'consulta_relatorio_importacao'
    ));
"""

REVERSE_SQL = """
ALTER TABLE acessos_dados_cliente
    DROP CONSTRAINT IF EXISTS chk_acesso_finalidade_enum;

ALTER TABLE acessos_dados_cliente
    ADD CONSTRAINT chk_acesso_finalidade_enum
    CHECK (finalidade IN (
        'atendimento_pos_venda',
        'preparar_orcamento',
        'executar_os',
        'emitir_documento_fiscal',
        'cobranca_inadimplencia',
        'auditoria_interna',
        'atendimento_lgpd_titular',
        'investigacao_incidente'
    ));
"""


class Migration(migrations.Migration):
    dependencies = [("audit", "0006_acessos_policy_update_delete")]
    operations = [migrations.RunSQL(sql=ALTER_SQL, reverse_sql=REVERSE_SQL)]
