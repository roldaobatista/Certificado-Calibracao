"""T-PPS-021 — Triggers de imutabilidade (molde `Imposto` 0003 da frente #1).

1. `pps_versao_worm_check` (INV-PPS-VERSAO-IMUTAVEL — BEFORE UPDATE em
   `item_catalogo_versao`): campos probatórios imutáveis pós-INSERT (tenant/
   item/versao_n/nome/descricao/categoria/unidade_medida/preco_padrao/
   vigencia_inicio/criado_por/motivo). MUTÁVEIS apenas os one-shot:
   `vigencia_fim` (NULL→data — encerramento pela versão sucessora) e
   `revogado_em`+`motivo_revogacao` (NULL→data — versão errada; sai da
   exclusion 0004 e NUNCA resolve — lição M2).

2. `pps_versao_block_delete` (BEFORE DELETE): retenção 10 anos (CC art. 205 —
   retencao-matriz linha ItemCatalogoVersao). Versão errada → revogar, nunca
   apagar (prova do preço de lista ofertado).

3. `pps_linha_worm_check` + 4. `pps_linha_block_delete` — idem para
   `linha_tabela_preco` (INV-PPS-LINHA-IMUTAVEL; preço de VENDA é prova
   comercial CDC art. 31 — ADV-PPS-04). Corrigir = use case composto
   revoga+recria atômico (D-PPS-8).

# audit-immutability: triggers do modulo produtos-pecas-servicos (nao tocam cadeia de auditoria)
# tests-coverage: tests/test_pps_schema_fatia1b.py (unhappy UPDATE/DELETE direto) +
# management/commands/validar_produtos_pecas_servicos.py
"""

from __future__ import annotations

from django.db import migrations


def _worm_fn(fn: str, tabela: str, campos_probatorios: tuple[str, ...], inv: str) -> str:
    comparacoes = "\n       OR ".join(
        f"NEW.{c} IS DISTINCT FROM OLD.{c}" for c in campos_probatorios
    )
    return f"""
CREATE OR REPLACE FUNCTION {fn}()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF {comparacoes} THEN
        RAISE EXCEPTION
            '{inv}: campo probatorio de {tabela} e imutavel pos-INSERT — linha errada se revoga e recria (use case composto), nunca UPDATE.';
    END IF;

    -- vigencia_fim one-shot: NULL -> data (encerramento); nunca re-escrita.
    IF OLD.vigencia_fim IS NOT NULL
       AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
        RAISE EXCEPTION
            '{inv}: vigencia_fim de {tabela} e one-shot (NULL->data); nao pode ser alterada/limpa.';
    END IF;

    -- revogacao one-shot: NULL -> data, com motivo congelando junto.
    IF OLD.revogado_em IS NOT NULL
       AND (NEW.revogado_em IS DISTINCT FROM OLD.revogado_em
            OR NEW.motivo_revogacao IS DISTINCT FROM OLD.motivo_revogacao) THEN
        RAISE EXCEPTION
            '{inv}: revogacao de {tabela} e one-shot; revogado_em/motivo nao mudam depois.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER {tabela}_worm_trg
    BEFORE UPDATE ON {tabela}
    FOR EACH ROW EXECUTE FUNCTION {fn}();
"""


def _block_delete_fn(fn: str, tabela: str, motivo: str) -> str:
    return f"""
CREATE OR REPLACE FUNCTION {fn}()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-PPS: DELETE fisico de {tabela} proibido — {motivo}';
END;
$body$;

CREATE TRIGGER {tabela}_block_delete_trg
    BEFORE DELETE ON {tabela}
    FOR EACH ROW EXECUTE FUNCTION {fn}();
"""


_CAMPOS_VERSAO = (
    "tenant_id",
    "item_id",
    "versao_n",
    "nome",
    "descricao",
    "categoria",
    "unidade_medida",
    "preco_padrao",
    "vigencia_inicio",
    "criado_por",
    "motivo",
)

_CAMPOS_LINHA = (
    "tenant_id",
    "tabela_id",
    "item_id",
    "preco",
    "vigencia_inicio",
    "origem_sugestao",
    "criado_por",
)

FORWARD = (
    _worm_fn(
        "pps_versao_worm_check", "item_catalogo_versao", _CAMPOS_VERSAO,
        "INV-PPS-VERSAO-IMUTAVEL",
    )
    + _block_delete_fn(
        "pps_versao_block_delete", "item_catalogo_versao",
        "retencao 10a CC art. 205 (prova do preco de lista — retencao-matriz). Versao errada -> revogar.",
    )
    + _worm_fn(
        "pps_linha_worm_check", "linha_tabela_preco", _CAMPOS_LINHA,
        "INV-PPS-LINHA-IMUTAVEL",
    )
    + _block_delete_fn(
        "pps_linha_block_delete", "linha_tabela_preco",
        "preco de venda e prova comercial CDC art. 31 (ADV-PPS-04). Linha errada -> revogar.",
    )
)

REVERSE = """
DROP TRIGGER IF EXISTS linha_tabela_preco_block_delete_trg ON linha_tabela_preco;
DROP FUNCTION IF EXISTS pps_linha_block_delete();
DROP TRIGGER IF EXISTS linha_tabela_preco_worm_trg ON linha_tabela_preco;
DROP FUNCTION IF EXISTS pps_linha_worm_check();
DROP TRIGGER IF EXISTS item_catalogo_versao_block_delete_trg ON item_catalogo_versao;
DROP FUNCTION IF EXISTS pps_versao_block_delete();
DROP TRIGGER IF EXISTS item_catalogo_versao_worm_trg ON item_catalogo_versao;
DROP FUNCTION IF EXISTS pps_versao_worm_check();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
