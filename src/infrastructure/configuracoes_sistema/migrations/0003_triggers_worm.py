"""T-CFG-023 — Triggers PG do módulo `configuracoes-sistema` (ADR-0031/0080).

Espelha os moldes fiscal (`nota_fiscal_servico_*`) e M8 (`numero_cert_reservado_*`).

1. `serie_documento_inv028_check` (INV-028 — BEFORE UPDATE):
   `proximo_numero` NUNCA diminui; única exceção legítima é o reset anual
   (TL-07): `reset_anual=TRUE` E `ano_corrente` trocando de valor. Também barra
   mutação de tenant/tipo/prefixo/regime_numeracao — o regime é DERIVADO do
   tipo (ADR-0080) e tipo+prefixo são a chave de unicidade (TL-06); mudar isso
   pós-criação corromperia a sequência (cria-se outra série).

2. `imposto_block_delete` (retenção fiscal 5a — ADV-05/CTN art. 195):
   DELETE físico sempre bloqueado. Linha errada → `revogado_em` (one-shot);
   alíquota nova → NOVA linha com nova vigência.

3. `imposto_worm_check` (INV-CFG-IMPOSTO-IMUTAVEL — TL-04, Padrão B):
   campos probatórios imutáveis pós-INSERT (tenant/tipo/filial/aliquota/
   vigencia_inicio/figuras fiscais/cfop/ncm). MUTÁVEIS: `observacoes` (anotação
   não-probatória) e os one-shot `vigencia_fim` (encerrar = NULL→data, D-CFG-3)
   e `revogado_em`+`motivo_revogacao` (revogar linha errada; motivo congela
   junto — validação ≥10 chars no domínio INV-VIG-002).

4. Numeração gap-less `numero_documento_reservado` (INV-CFG-NUM-ATOMICA —
   mesmos 3 triggers do motor M8, por (tenant, serie, ano)):
   consecutividade no INSERT (`sequencial <= max+1`), confirmação one-shot +
   chave imutável no UPDATE, DELETE só de reserva NÃO-confirmada (número
   confirmado é preservado — cancelamento não devolve à sequência).

# audit-immutability: triggers do modulo configuracoes-sistema (nao tocam cadeia de auditoria)
# tests-coverage: tests/test_configuracoes_schema_fatia1b.py +
# management/commands/validar_configuracoes_sistema.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. INV-028 — serie_documento.proximo_numero nunca diminui
--    (exceto reset anual TL-07) + chave/regime imutaveis (ADR-0080)
-- =============================================================
CREATE OR REPLACE FUNCTION serie_documento_inv028_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.tipo IS DISTINCT FROM OLD.tipo
       OR NEW.prefixo IS DISTINCT FROM OLD.prefixo
       OR NEW.regime_numeracao IS DISTINCT FROM OLD.regime_numeracao THEN
        RAISE EXCEPTION
            'ADR-0080: tenant/tipo/prefixo/regime_numeracao de serie_documento sao imutaveis pos-criacao (regime e DERIVADO do tipo; crie outra serie).';
    END IF;

    IF NEW.proximo_numero < OLD.proximo_numero
       AND NOT (NEW.reset_anual AND NEW.ano_corrente IS DISTINCT FROM OLD.ano_corrente) THEN
        RAISE EXCEPTION
            'INV-028: proximo_numero de serie_documento nao pode diminuir (% -> %) — unica excecao e reset anual legitimo (reset_anual + troca de ano_corrente).',
            OLD.proximo_numero, NEW.proximo_numero;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER serie_documento_inv028_check_trg
    BEFORE UPDATE ON serie_documento
    FOR EACH ROW
    EXECUTE FUNCTION serie_documento_inv028_check();

-- =============================================================
-- 2. imposto nunca DELETE fisico (retencao fiscal 5a — ADV-05)
-- =============================================================
CREATE OR REPLACE FUNCTION imposto_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CFG-IMPOSTO-IMUTAVEL: linha de imposto nao pode ser deletada fisicamente (retencao fiscal 5a — linha errada usa revogado_em; aliquota nova = NOVA linha).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER imposto_block_delete_trg
    BEFORE DELETE ON imposto
    FOR EACH ROW
    EXECUTE FUNCTION imposto_block_delete();

-- =============================================================
-- 3. INV-CFG-IMPOSTO-IMUTAVEL — campos probatorios imutaveis (TL-04)
-- =============================================================
CREATE OR REPLACE FUNCTION imposto_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.tipo IS DISTINCT FROM OLD.tipo
       OR NEW.filial_id IS DISTINCT FROM OLD.filial_id
       OR NEW.aliquota IS DISTINCT FROM OLD.aliquota
       OR NEW.vigencia_inicio IS DISTINCT FROM OLD.vigencia_inicio
       OR NEW.iss_retido_fonte IS DISTINCT FROM OLD.iss_retido_fonte
       OR NEW.tem_st IS DISTINCT FROM OLD.tem_st
       OR NEW.simples_excedeu_sublimite IS DISTINCT FROM OLD.simples_excedeu_sublimite
       OR NEW.cfop_padrao IS DISTINCT FROM OLD.cfop_padrao
       OR NEW.ncm_padrao IS DISTINCT FROM OLD.ncm_padrao
    THEN
        RAISE EXCEPTION
            'INV-CFG-IMPOSTO-IMUTAVEL: campos probatorios da linha de imposto sao imutaveis (TL-04 — aliquota nova = NOVA linha com nova vigencia).';
    END IF;

    -- vigencia_fim one-shot (encerrar vigencia = NULL -> data; nao reabre nem muda)
    IF OLD.vigencia_fim IS NOT NULL
       AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
        RAISE EXCEPTION 'INV-CFG-IMPOSTO-IMUTAVEL: vigencia_fim e one-shot (D-CFG-3 — imutavel apos preenchida).';
    END IF;

    -- revogado_em one-shot; motivo congela junto com a revogacao
    IF OLD.revogado_em IS NOT NULL THEN
        IF NEW.revogado_em IS DISTINCT FROM OLD.revogado_em
           OR NEW.motivo_revogacao IS DISTINCT FROM OLD.motivo_revogacao THEN
            RAISE EXCEPTION 'INV-CFG-IMPOSTO-IMUTAVEL: revogado_em/motivo_revogacao sao one-shot (imutaveis apos revogacao).';
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER imposto_worm_check_trg
    BEFORE UPDATE ON imposto
    FOR EACH ROW
    EXECUTE FUNCTION imposto_worm_check();

-- =============================================================
-- 4. INV-CFG-NUM-ATOMICA — numeracao gap-less (motor M8 por serie)
-- =============================================================
-- 4a. Consecutividade no INSERT (sem buraco confirmavel — ADR-0080).
CREATE OR REPLACE FUNCTION numero_doc_reservado_consecutivo_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
DECLARE max_seq integer;
BEGIN
    IF NEW.sequencial < 1 THEN
        RAISE EXCEPTION 'INV-CFG-NUM-ATOMICA: sequencial de documento deve ser >= 1 (recebeu %).', NEW.sequencial;
    END IF;
    SELECT COALESCE(MAX(sequencial), 0) INTO max_seq
    FROM numero_documento_reservado
    WHERE tenant_id = NEW.tenant_id AND serie_id = NEW.serie_id AND ano = NEW.ano;
    IF NEW.sequencial > max_seq + 1 THEN
        RAISE EXCEPTION
            'INV-CFG-NUM-ATOMICA: numero de documento fora de sequencia consecutiva (seq=% > max+1=%) — buraco proibido em serie gap-less (ADR-0080).',
            NEW.sequencial, max_seq + 1;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER numero_doc_reservado_consecutivo_check_trg
    BEFORE INSERT ON numero_documento_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_doc_reservado_consecutivo_check();

-- 4b. Confirmacao one-shot + chave imutavel no UPDATE.
CREATE OR REPLACE FUNCTION numero_doc_reservado_confirma_one_shot()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.confirmado AND NOT NEW.confirmado THEN
        RAISE EXCEPTION 'INV-CFG-NUM-ATOMICA: confirmacao de numero de documento e one-shot (nao reverte).';
    END IF;
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.serie_id IS DISTINCT FROM OLD.serie_id
       OR NEW.ano IS DISTINCT FROM OLD.ano
       OR NEW.sequencial IS DISTINCT FROM OLD.sequencial THEN
        RAISE EXCEPTION 'INV-CFG-NUM-ATOMICA: chave (tenant/serie/ano/sequencial) do numero reservado e imutavel.';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER numero_doc_reservado_confirma_one_shot_trg
    BEFORE UPDATE ON numero_documento_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_doc_reservado_confirma_one_shot();

-- 4c. Bloqueio de DELETE de numero CONFIRMADO (cancelamento PRESERVA o numero).
CREATE OR REPLACE FUNCTION numero_doc_reservado_block_delete_confirmado()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.confirmado THEN
        RAISE EXCEPTION
            'INV-CFG-NUM-ATOMICA: numero de documento confirmado nao pode ser deletado nem reusado (cancelamento PRESERVA o numero — ADR-0080).';
    END IF;
    RETURN OLD;
END;
$body$;

CREATE TRIGGER numero_doc_reservado_block_delete_confirmado_trg
    BEFORE DELETE ON numero_documento_reservado
    FOR EACH ROW EXECUTE FUNCTION numero_doc_reservado_block_delete_confirmado();
"""

REVERSE = """
DROP TRIGGER IF EXISTS numero_doc_reservado_block_delete_confirmado_trg ON numero_documento_reservado;
DROP FUNCTION IF EXISTS numero_doc_reservado_block_delete_confirmado();
DROP TRIGGER IF EXISTS numero_doc_reservado_confirma_one_shot_trg ON numero_documento_reservado;
DROP FUNCTION IF EXISTS numero_doc_reservado_confirma_one_shot();
DROP TRIGGER IF EXISTS numero_doc_reservado_consecutivo_check_trg ON numero_documento_reservado;
DROP FUNCTION IF EXISTS numero_doc_reservado_consecutivo_check();
DROP TRIGGER IF EXISTS imposto_worm_check_trg ON imposto;
DROP FUNCTION IF EXISTS imposto_worm_check();
DROP TRIGGER IF EXISTS imposto_block_delete_trg ON imposto;
DROP FUNCTION IF EXISTS imposto_block_delete();
DROP TRIGGER IF EXISTS serie_documento_inv028_check_trg ON serie_documento;
DROP FUNCTION IF EXISTS serie_documento_inv028_check();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("configuracoes_sistema", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
