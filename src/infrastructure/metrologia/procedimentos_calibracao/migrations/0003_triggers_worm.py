"""T-PROC-023 — Triggers PG WORM Padrão B (ADR-0031 / INV-PROC-003 / INV-SOFT-002).

Espelha o padrão M6 (`escopo_cmc_worm_check`) — não reinventar.

1. `procedimento_calibracao_block_delete` (INV-SOFT-002 — soft-delete B):
   BEFORE DELETE sempre bloqueia. Procedimento sustenta certificado RBC (retenção
   25a cl. 8.4) — revogação usa `revogado_em` + estado REVOGADO, nunca DELETE.

2. `procedimento_calibracao_worm_check` (INV-PROC-003 / INV-PROC-007):
   BEFORE UPDATE. Em linha `estado IN (PUBLICADO, REVOGADO)`, campos técnicos/
   probatórios são imutáveis (codigo/grandeza/faixa/metodo/tipo_metodo/anexo_sha256/
   numero_revisao/aprovado_*/versao/vigência início). RASCUNHO é editável (não
   entra no congelamento). Revisão = INSERT de nova `versao`. Permitidas só as
   transições one-shot: revogação (`revogado_em` NULL→valor + estado→REVOGADO +
   motivo) e encerramento de vigência (`vigencia_fim` NULL→valor, superado por
   nova versão) + bump de `revision` (CAS).

# audit-immutability: triggers WORM do modulo procedimentos_calibracao (nao tocam cadeia auditoria)
# tests-coverage: tests/regressao/test_inv_proc_p2_schema_triggers.py (WORM) + management/commands/validar_procedimentos_calibracao.py (GATE-PROC-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. INV-SOFT-002 — procedimento_calibracao nunca DELETE fisico (soft-delete B)
-- =============================================================
CREATE OR REPLACE FUNCTION procedimento_calibracao_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-SOFT-002: ProcedimentoCalibracao nao pode ser deletado fisicamente (soft-delete B ADR-0031 — usar estado REVOGADO + revogado_em; retencao 25a cl. 8.4).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER procedimento_calibracao_block_delete_trg
    BEFORE DELETE ON procedimento_calibracao
    FOR EACH ROW
    EXECUTE FUNCTION procedimento_calibracao_block_delete();

-- =============================================================
-- 2. INV-PROC-003 — campo tecnico de PUBLICADO imutavel (WORM Padrao B)
-- =============================================================
CREATE OR REPLACE FUNCTION procedimento_calibracao_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos tecnicos/probatorios congelados em estado ja comprometido
    -- (PUBLICADO ou REVOGADO) — procedimento sustenta certificado mesmo apos
    -- revogacao (cl. 8.4 retroativo). RASCUNHO e editavel.
    IF OLD.estado IN ('PUBLICADO', 'REVOGADO') THEN
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
           OR NEW.codigo IS DISTINCT FROM OLD.codigo
           OR NEW.grandeza IS DISTINCT FROM OLD.grandeza
           OR NEW.faixa_min IS DISTINCT FROM OLD.faixa_min
           OR NEW.faixa_max IS DISTINCT FROM OLD.faixa_max
           OR NEW.unidade IS DISTINCT FROM OLD.unidade
           OR NEW.metodo_norma IS DISTINCT FROM OLD.metodo_norma
           OR NEW.tipo_metodo IS DISTINCT FROM OLD.tipo_metodo
           OR NEW.registro_validacao_id IS DISTINCT FROM OLD.registro_validacao_id
           OR NEW.numero_revisao IS DISTINCT FROM OLD.numero_revisao
           OR NEW.aprovado_em IS DISTINCT FROM OLD.aprovado_em
           OR NEW.aprovado_por_id IS DISTINCT FROM OLD.aprovado_por_id
           OR NEW.anexo_pdf_storage_key IS DISTINCT FROM OLD.anexo_pdf_storage_key
           OR NEW.anexo_pdf_sha256 IS DISTINCT FROM OLD.anexo_pdf_sha256
           OR NEW.versao IS DISTINCT FROM OLD.versao
           OR NEW.vigente_a_partir IS DISTINCT FROM OLD.vigente_a_partir
           OR NEW.vigencia_inicio IS DISTINCT FROM OLD.vigencia_inicio
        THEN
            RAISE EXCEPTION
                'INV-PROC-003/WORM: procedimento PUBLICADO e imutavel nos campos tecnicos (ADR-0031 Padrao B / cl. 8.4); revisao = nova versao, nunca UPDATE in-place.';
        END IF;
        -- revogacao one-shot
        IF OLD.revogado_em IS NOT NULL
           AND NEW.revogado_em IS DISTINCT FROM OLD.revogado_em THEN
            RAISE EXCEPTION
                'INV-PROC-003: procedimento ja revogado (revogado_em one-shot imutavel).';
        END IF;
        -- encerramento de vigencia one-shot (superado por nova versao)
        IF OLD.vigencia_fim IS NOT NULL
           AND NEW.vigencia_fim IS DISTINCT FROM OLD.vigencia_fim THEN
            RAISE EXCEPTION
                'INV-PROC-003: vigencia_fim ja encerrada (one-shot imutavel).';
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER procedimento_calibracao_worm_check_trg
    BEFORE UPDATE ON procedimento_calibracao
    FOR EACH ROW
    EXECUTE FUNCTION procedimento_calibracao_worm_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS procedimento_calibracao_worm_check_trg ON procedimento_calibracao;
DROP FUNCTION IF EXISTS procedimento_calibracao_worm_check();
DROP TRIGGER IF EXISTS procedimento_calibracao_block_delete_trg ON procedimento_calibracao;
DROP FUNCTION IF EXISTS procedimento_calibracao_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("procedimentos_calibracao", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
