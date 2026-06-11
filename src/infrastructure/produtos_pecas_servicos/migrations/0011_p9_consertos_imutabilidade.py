"""P9 conserto causa-raiz (auditores qualidade + seguranca) — 3 barreiras de banco.

1. QUAL-M1: trigger `pps_item_imutavel_check` em `item_catalogo` — a
   INV-PPS-CODIGO-UNICO declara `codigo_interno`/`tipo` imutáveis pós-criação,
   mas só havia defesa de convenção (`update_or_create` reescreveria em
   silêncio). `status`/`controla_estoque`/`codigo_fabricante` seguem mutáveis.
2. SEG-B1(ii): CHECK `vigencia_fim >= vigencia_inicio` (INV-VIG-001 no banco)
   nas 2 tabelas WORM — em linha já revogada a exclusion parcial não indexa e
   o one-shot aceitava fim < inicio.
3. SEG-B1(i): patch das funções WORM (`CREATE OR REPLACE`) — `motivo_revogacao`
   não pode mudar enquanto `revogado_em` continua NULL (era mutável
   pré-revogação; motivo só nasce JUNTO da revogação, one-shot).

# rls-policy: external 0002_rls_policies (trigger/CHECK — nao cria tabela)
# audit-immutability: skip -- triggers do modulo pps, nao tocam cadeia de auditoria
"""

from __future__ import annotations

from django.db import migrations

_ITEM_IMUTAVEL_FORWARD = """
CREATE OR REPLACE FUNCTION pps_item_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.codigo_interno IS DISTINCT FROM OLD.codigo_interno
       OR NEW.tipo IS DISTINCT FROM OLD.tipo
       OR NEW.tenant_id IS DISTINCT FROM OLD.tenant_id THEN
        RAISE EXCEPTION
            'INV-PPS-CODIGO-UNICO: codigo_interno/tipo de item_catalogo sao imutaveis pos-criacao — item errado se inativa e recria.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER item_catalogo_imutavel_trg
    BEFORE UPDATE ON item_catalogo
    FOR EACH ROW EXECUTE FUNCTION pps_item_imutavel_check();
"""

_ITEM_IMUTAVEL_REVERSE = """
DROP TRIGGER IF EXISTS item_catalogo_imutavel_trg ON item_catalogo;
DROP FUNCTION IF EXISTS pps_item_imutavel_check();
"""

_CHECKS_FORWARD = """
ALTER TABLE item_catalogo_versao
    ADD CONSTRAINT ck_pps_versao_fim_apos_inicio
    CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio);
ALTER TABLE linha_tabela_preco
    ADD CONSTRAINT ck_pps_linha_fim_apos_inicio
    CHECK (vigencia_fim IS NULL OR vigencia_fim >= vigencia_inicio);
"""

_CHECKS_REVERSE = """
ALTER TABLE linha_tabela_preco DROP CONSTRAINT IF EXISTS ck_pps_linha_fim_apos_inicio;
ALTER TABLE item_catalogo_versao DROP CONSTRAINT IF EXISTS ck_pps_versao_fim_apos_inicio;
"""


def _worm_fn_v2(fn: str, tabela: str, campos_probatorios: tuple[str, ...], inv: str) -> str:
    """Mesmo corpo da 0003 + guard: motivo_revogacao só muda JUNTO da revogação."""
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

    -- P9 SEG-B1(i): motivo_revogacao so nasce JUNTO da revogacao — mudar o
    -- motivo enquanto revogado_em continua NULL era brecha de pre-edicao.
    IF OLD.revogado_em IS NULL AND NEW.revogado_em IS NULL
       AND NEW.motivo_revogacao IS DISTINCT FROM OLD.motivo_revogacao THEN
        RAISE EXCEPTION
            '{inv}: motivo_revogacao de {tabela} so pode ser gravado junto da revogacao (one-shot).';
    END IF;
    RETURN NEW;
END;
$body$;
"""


def _worm_fn_v1(fn: str, tabela: str, campos_probatorios: tuple[str, ...], inv: str) -> str:
    """Corpo original da 0003 (pro reverse)."""
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

    IF OLD.vigencia_fim IS NOT NULL
       AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
        RAISE EXCEPTION
            '{inv}: vigencia_fim de {tabela} e one-shot (NULL->data); nao pode ser alterada/limpa.';
    END IF;

    IF OLD.revogado_em IS NOT NULL
       AND (NEW.revogado_em IS DISTINCT FROM OLD.revogado_em
            OR NEW.motivo_revogacao IS DISTINCT FROM OLD.motivo_revogacao) THEN
        RAISE EXCEPTION
            '{inv}: revogacao de {tabela} e one-shot; revogado_em/motivo nao mudam depois.';
    END IF;
    RETURN NEW;
END;
$body$;
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

_WORM_PATCH_FORWARD = _worm_fn_v2(
    "pps_versao_worm_check", "item_catalogo_versao", _CAMPOS_VERSAO,
    "INV-PPS-VERSAO-IMUTAVEL",
) + _worm_fn_v2(
    "pps_linha_worm_check", "linha_tabela_preco", _CAMPOS_LINHA,
    "INV-PPS-LINHA-IMUTAVEL",
)

_WORM_PATCH_REVERSE = _worm_fn_v1(
    "pps_versao_worm_check", "item_catalogo_versao", _CAMPOS_VERSAO,
    "INV-PPS-VERSAO-IMUTAVEL",
) + _worm_fn_v1(
    "pps_linha_worm_check", "linha_tabela_preco", _CAMPOS_LINHA,
    "INV-PPS-LINHA-IMUTAVEL",
)


class Migration(migrations.Migration):
    dependencies = [
        ("produtos_pecas_servicos", "0010_amplia_motivos"),
    ]

    operations = [
        migrations.RunSQL(sql=_ITEM_IMUTAVEL_FORWARD, reverse_sql=_ITEM_IMUTAVEL_REVERSE),
        migrations.RunSQL(sql=_CHECKS_FORWARD, reverse_sql=_CHECKS_REVERSE),
        migrations.RunSQL(sql=_WORM_PATCH_FORWARD, reverse_sql=_WORM_PATCH_REVERSE),
    ]
