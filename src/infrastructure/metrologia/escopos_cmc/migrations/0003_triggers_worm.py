"""T-ECMC-013 — Triggers PG WORM Padrão B (ADR-0031 / INV-ECMC-003 / INV-SOFT-002).

Espelha o padrão M5 (`recal_externo_padrao_worm_check`) — não reinventar.

1. `escopo_cmc_block_delete` (INV-SOFT-002 — ADR-0031 soft-delete B):
   BEFORE DELETE em escopo_cmc sempre bloqueia. Escopo sustenta certificado RBC
   (retenção 25a cl. 8.4) — revogação usa `revogado_em` + estado REVOGADO, nunca
   DELETE físico.

2. `escopo_cmc_worm_check` (INV-ECMC-003 — TL-C-07):
   BEFORE UPDATE. Em linha `estado=CONFIRMADO`, campos metrológicos/probatórios
   são imutáveis (grandeza/faixa/cmc/rbc/versao/procedimento/vigência início).
   Revisão = INSERT de nova `versao` (nunca UPDATE in-place). Permitidas só as
   transições one-shot: revogação (`revogado_em` NULL→valor + estado→REVOGADO +
   motivo) e encerramento de vigência (`vigencia_fim` NULL→valor, quando superado
   por nova versão) + bump de `revision` (CAS).

`escopo_extraido` (staging) NÃO tem WORM — é mutável/descartável até confirmação
(INV-ECMC-007: confirmar CRIA linha em escopo_cmc; não promove a staging).

# audit-immutability: triggers WORM do modulo escopos_cmc (nao tocam cadeia auditoria)
# tests-coverage: tests/regressao/test_inv_ecmc_p2_schema_triggers.py (WORM) + management/commands/validar_escopos_cmc.py (GATE-ECMC-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. INV-SOFT-002 — escopo_cmc nunca DELETE fisico (soft-delete B)
-- =============================================================
CREATE OR REPLACE FUNCTION escopo_cmc_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-SOFT-002: EscopoCMC nao pode ser deletado fisicamente (soft-delete B ADR-0031 — usar estado REVOGADO + revogado_em; retencao 25a cl. 8.4).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER escopo_cmc_block_delete_trg
    BEFORE DELETE ON escopo_cmc
    FOR EACH ROW
    EXECUTE FUNCTION escopo_cmc_block_delete();

-- =============================================================
-- 2. INV-ECMC-003 — campo metrologico de CONFIRMADO imutavel (WORM Padrao B)
-- =============================================================
CREATE OR REPLACE FUNCTION escopo_cmc_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos metrologicos congelados em qualquer estado ja comprometido
    -- (CONFIRMADO ou REVOGADO) — escopo sustenta certificado mesmo apos
    -- revogacao (cl. 8.4 retroativo). Rascunho vive em escopo_extraido.
    IF OLD.estado IN ('CONFIRMADO', 'REVOGADO') THEN
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
           OR NEW.grandeza IS DISTINCT FROM OLD.grandeza
           OR NEW.faixa_min IS DISTINCT FROM OLD.faixa_min
           OR NEW.faixa_max IS DISTINCT FROM OLD.faixa_max
           OR NEW.unidade IS DISTINCT FROM OLD.unidade
           OR NEW.cmc_forma IS DISTINCT FROM OLD.cmc_forma
           OR NEW.cmc_valor IS DISTINCT FROM OLD.cmc_valor
           OR NEW.cmc_unidade IS DISTINCT FROM OLD.cmc_unidade
           OR NEW.cmc_coef_relativo IS DISTINCT FROM OLD.cmc_coef_relativo
           OR NEW.rbc_acreditado IS DISTINCT FROM OLD.rbc_acreditado
           OR NEW.numero_escopo_cgcre IS DISTINCT FROM OLD.numero_escopo_cgcre
           OR NEW.procedimento_id IS DISTINCT FROM OLD.procedimento_id
           OR NEW.documento_regulatorio_id IS DISTINCT FROM OLD.documento_regulatorio_id
           OR NEW.versao IS DISTINCT FROM OLD.versao
           OR NEW.vigente_a_partir IS DISTINCT FROM OLD.vigente_a_partir
           OR NEW.vigencia_inicio IS DISTINCT FROM OLD.vigencia_inicio
           OR NEW.origem IS DISTINCT FROM OLD.origem
        THEN
            RAISE EXCEPTION
                'INV-ECMC-003/WORM: escopo CMC CONFIRMADO e imutavel nos campos metrologicos (ADR-0031 Padrao B / cl. 8.4); revisao = nova versao, nunca UPDATE in-place.';
        END IF;
        -- revogacao one-shot
        IF OLD.revogado_em IS NOT NULL
           AND NEW.revogado_em IS DISTINCT FROM OLD.revogado_em THEN
            RAISE EXCEPTION
                'INV-ECMC-003: escopo ja revogado (revogado_em one-shot imutavel).';
        END IF;
        -- encerramento de vigencia one-shot (superado por nova versao)
        IF OLD.vigencia_fim IS NOT NULL
           AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
            RAISE EXCEPTION
                'INV-ECMC-003: vigencia_fim ja encerrada (one-shot imutavel).';
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER escopo_cmc_worm_check_trg
    BEFORE UPDATE ON escopo_cmc
    FOR EACH ROW
    EXECUTE FUNCTION escopo_cmc_worm_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS escopo_cmc_worm_check_trg ON escopo_cmc;
DROP FUNCTION IF EXISTS escopo_cmc_worm_check();
DROP TRIGGER IF EXISTS escopo_cmc_block_delete_trg ON escopo_cmc;
DROP FUNCTION IF EXISTS escopo_cmc_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("escopos_cmc", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
