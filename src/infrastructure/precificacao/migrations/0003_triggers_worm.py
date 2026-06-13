"""T-PRC-023 — Triggers de imutabilidade (molde `Imposto` 0003 da frente #1).

1. `prc_regra_worm_check` (INV-PRC-REGRA-IMUTAVEL — BEFORE UPDATE em
   `regra_formacao_preco`): campos probatórios imutáveis pós-INSERT
   (tenant/item/modo/versao_n/vigencia_inicio/criado_por + valores formação
   de preço: preco_fixo/custo_manual_declarado/custo_referencia_em/
   margem_alvo_pct/margem_piso_pct).
   MUTÁVEIS apenas os one-shot:
   `vigencia_fim` (NULL→data — encerramento pela regra sucessora) e
   `revogado_em`+`motivo_revogacao` (NULL→data — regra errada; sai da
   exclusion 0004 e NUNCA resolve).

2. `prc_regra_block_delete` (BEFORE DELETE): retenção comercial 5a
   (CC art. 205 — retencao-matriz linha RegraFormacaoPreco).

3. `prc_pedido_one_shot_estado` (BEFORE UPDATE em `pedido_aprovacao_desconto`):
   estado SOLICITADO→APROVADO|NEGADO (one-shot, sem volta —
   INV-PRC-APROVACAO-ONE-SHOT). Garante que a transição é só terminal.

4. `prc_pedido_worm_probatorio` (BEFORE UPDATE em `pedido_aprovacao_desconto`):
   campos probatórios pós-decisão congelados: pct_solicitado/cortesia/
   alcada_exigida/fingerprint_calculo/solicitante_id/snapshot_probatorio
   NUNCA mudam; decisor_id/justificativa_hash/decidido_em são preenchidos
   APENAS UMA VEZ (one-shot NULL→valor).

# audit-immutability: triggers do modulo precificacao (nao tocam cadeia de auditoria)
# tests-coverage: tests/test_precificacao_schema_fatia1b.py (unhappy UPDATE direto) +
# management/commands/validar_precificacao.py
"""

from __future__ import annotations

from django.db import migrations

# Campos probatórios da regra (imutáveis pós-INSERT)
_CAMPOS_REGRA = (
    "tenant_id",
    "item_id",
    "modo",
    "versao_n",
    "vigencia_inicio",
    "criado_por",
    "preco_fixo",
    "custo_manual_declarado",
    "custo_referencia_em",
    "margem_alvo_pct",
    "margem_piso_pct",
)

# Campos probatórios do pedido (imutáveis sempre)
_CAMPOS_PEDIDO_PROBATORIOS = (
    "tenant_id",
    "contexto_tipo",
    "contexto_id",
    "pct_solicitado",
    "cortesia",
    "alcada_exigida",
    "fingerprint_calculo",
    "solicitante_id",
    "snapshot_probatorio",
    "criado_em",
)


def _comparacoes(campos: tuple[str, ...]) -> str:
    return "\n       OR ".join(
        f"NEW.{c} IS DISTINCT FROM OLD.{c}" for c in campos
    )


FORWARD = f"""
-- =============================================================
-- 1. INV-PRC-REGRA-IMUTAVEL — campos probatorios imutaveis (molde Imposto)
-- =============================================================
CREATE OR REPLACE FUNCTION prc_regra_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF {_comparacoes(_CAMPOS_REGRA)} THEN
        RAISE EXCEPTION
            'INV-PRC-REGRA-IMUTAVEL: campo probatorio de regra_formacao_preco e imutavel pos-INSERT — regra errada se revoga e recria (publicar_regra), nunca UPDATE direto.';
    END IF;

    -- vigencia_fim one-shot: NULL -> data (encerramento); nunca re-escrita.
    IF OLD.vigencia_fim IS NOT NULL
       AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
        RAISE EXCEPTION
            'INV-PRC-REGRA-IMUTAVEL: vigencia_fim de regra_formacao_preco e one-shot (NULL->data); nao pode ser alterada/limpa.';
    END IF;

    -- revogacao one-shot: NULL -> data, com motivo congelando junto.
    IF OLD.revogado_em IS NOT NULL
       AND (NEW.revogado_em IS DISTINCT FROM OLD.revogado_em
            OR NEW.motivo_revogacao IS DISTINCT FROM OLD.motivo_revogacao) THEN
        RAISE EXCEPTION
            'INV-PRC-REGRA-IMUTAVEL: revogacao de regra_formacao_preco e one-shot; revogado_em/motivo nao mudam depois.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER regra_formacao_preco_worm_trg
    BEFORE UPDATE ON regra_formacao_preco
    FOR EACH ROW EXECUTE FUNCTION prc_regra_worm_check();

-- =============================================================
-- 2. INV-PRC-REGRA-IMUTAVEL — DELETE fisico bloqueado (retencao 5a)
-- =============================================================
CREATE OR REPLACE FUNCTION prc_regra_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-PRC-REGRA-IMUTAVEL: DELETE fisico de regra_formacao_preco proibido — retencao 5a CC art. 205 (prova comercial — retencao-matriz). Regra errada -> revogar.';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER regra_formacao_preco_block_delete_trg
    BEFORE DELETE ON regra_formacao_preco
    FOR EACH ROW EXECUTE FUNCTION prc_regra_block_delete();

-- =============================================================
-- 3. INV-PRC-APROVACAO-ONE-SHOT — estado do pedido (SOLICITADO->terminal)
-- =============================================================
CREATE OR REPLACE FUNCTION prc_pedido_one_shot_estado()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Estado terminal nunca volta
    IF OLD.estado IN ('aprovado', 'negado') THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: pedido_aprovacao_desconto em estado terminal (%) nao pode ser alterado — decisao e irreversivel.', OLD.estado;
    END IF;

    -- Transicao valida: SOLICITADO -> APROVADO | NEGADO
    IF NEW.estado NOT IN ('aprovado', 'negado') AND NEW.estado IS DISTINCT FROM OLD.estado THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: transicao de estado invalida em pedido_aprovacao_desconto (% -> %) — so SOLICITADO->APROVADO ou SOLICITADO->NEGADO.', OLD.estado, NEW.estado;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER pedido_aprovacao_desconto_one_shot_estado_trg
    BEFORE UPDATE ON pedido_aprovacao_desconto
    FOR EACH ROW EXECUTE FUNCTION prc_pedido_one_shot_estado();

-- =============================================================
-- 4. INV-PRC-APROVACAO-ONE-SHOT — campos probatorios do pedido imutaveis
-- =============================================================
CREATE OR REPLACE FUNCTION prc_pedido_worm_probatorio()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF {_comparacoes(_CAMPOS_PEDIDO_PROBATORIOS)} THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: campos probatorios de pedido_aprovacao_desconto sao imutaveis (pct/cortesia/alcada/fingerprint/solicitante/snapshot/contexto).';
    END IF;

    -- decisor_id: one-shot NULL -> valor (preenchido na decisao)
    IF OLD.decisor_id IS NOT NULL
       AND NEW.decisor_id IS DISTINCT FROM OLD.decisor_id THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: decisor_id de pedido_aprovacao_desconto e one-shot (imutavel apos preenchido).';
    END IF;

    -- justificativa_hash: one-shot NULL -> valor
    IF OLD.justificativa_hash <> '' AND OLD.justificativa_hash IS NOT NULL
       AND NEW.justificativa_hash IS DISTINCT FROM OLD.justificativa_hash THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: justificativa_hash de pedido_aprovacao_desconto e one-shot (imutavel apos preenchido).';
    END IF;

    -- decidido_em: one-shot NULL -> timestamp
    IF OLD.decidido_em IS NOT NULL
       AND NEW.decidido_em IS DISTINCT FROM OLD.decidido_em THEN
        RAISE EXCEPTION
            'INV-PRC-APROVACAO-ONE-SHOT: decidido_em de pedido_aprovacao_desconto e one-shot (imutavel apos preenchido).';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER pedido_aprovacao_desconto_worm_probatorio_trg
    BEFORE UPDATE ON pedido_aprovacao_desconto
    FOR EACH ROW EXECUTE FUNCTION prc_pedido_worm_probatorio();
"""

REVERSE = """
DROP TRIGGER IF EXISTS pedido_aprovacao_desconto_worm_probatorio_trg ON pedido_aprovacao_desconto;
DROP FUNCTION IF EXISTS prc_pedido_worm_probatorio();
DROP TRIGGER IF EXISTS pedido_aprovacao_desconto_one_shot_estado_trg ON pedido_aprovacao_desconto;
DROP FUNCTION IF EXISTS prc_pedido_one_shot_estado();
DROP TRIGGER IF EXISTS regra_formacao_preco_block_delete_trg ON regra_formacao_preco;
DROP FUNCTION IF EXISTS prc_regra_block_delete();
DROP TRIGGER IF EXISTS regra_formacao_preco_worm_trg ON regra_formacao_preco;
DROP FUNCTION IF EXISTS prc_regra_worm_check();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("precificacao", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
