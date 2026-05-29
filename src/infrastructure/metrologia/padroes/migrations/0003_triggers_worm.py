"""T-PAD-015/016 — Triggers PG: INV-PAD-006 (GUC) + INV-SOFT-002 + WORM.

Triggers (espelham o padrao M4 calibracao — nao reinventar):

1. `padrao_incertezas_so_via_recal` (INV-PAD-006 — decisao C-10):
   BEFORE UPDATE em padrao_metrologico. Bloqueia mutacao de
   `incertezas_certificado` / `validade_certificado_rastreabilidade` /
   `proximo_recal` SALVO quando a sessao esta dentro do fluxo legitimo de
   recal (GUC `app.padrao_recal_em_curso` = '1', setado por SET LOCAL no use
   case `registrar_recal_retorno`/`aprovar_recal_rt`). GUC resetado no checkout
   do pool (connection.py) — defesa em profundidade.

2. `padrao_block_delete` (INV-SOFT-002 — ADR-0031 soft-delete B):
   BEFORE DELETE em padrao_metrologico sempre bloqueia. Baixa/sucata usam
   `estado` + `revogado_em`, nunca DELETE fisico (audit + retencao 25a cl. 8.4).

3. `recal_externo_padrao_worm` (C-4): pos `retornado_em`, valores retornados
   imutaveis; APENAS a aprovacao RT (`aprovado_rt_em`/`aprovado_rt_id_hash`)
   transiciona uma vez (NULL -> valor). DELETE bloqueado pos retorno.

4. `verificacao_intermediaria_append_only` (cl. 6.4.10): UPDATE + DELETE
   bloqueados (WORM puro — INV-022).

5. `intercomparacao_pt_worm` (cl. 6.6): campos de inicio imutaveis pos insert;
   resultado transiciona uma vez; DELETE bloqueado pos finalizacao.

6. `analise_carta_controle_append_only` (ADR-0070 / INV-PAD-010): UPDATE +
   DELETE bloqueados (registro probatorio congelado — cl. 8.4).

# audit-immutability: triggers WORM do modulo padroes (nao tocam cadeia auditoria)
# tests-coverage: tests/regressao/test_inv_pad_p2_schema_triggers.py (WORM/GUC) + test_inv_pad_classes_nomeadas.py (INV-PAD-006/010 — T-PAD-072 GATE-PAD-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. INV-PAD-006 — incertezas/validade/proximo_recal so via recal (GUC C-10)
-- =============================================================
CREATE OR REPLACE FUNCTION padrao_incertezas_so_via_recal()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF (NEW.incertezas_certificado IS DISTINCT FROM OLD.incertezas_certificado
        OR NEW.validade_certificado_rastreabilidade
           IS DISTINCT FROM OLD.validade_certificado_rastreabilidade
        OR NEW.proximo_recal IS DISTINCT FROM OLD.proximo_recal)
    THEN
        IF current_setting('app.padrao_recal_em_curso', true) IS DISTINCT FROM '1' THEN
            RAISE EXCEPTION
                'INV-PAD-006: incertezas/validade/proximo_recal do padrao so mudam dentro do fluxo de recal externo (use case seta SET LOCAL app.padrao_recal_em_curso); UPDATE direto negado (cl. 6.5 rastreabilidade).';
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER padrao_incertezas_so_via_recal_trg
    BEFORE UPDATE ON padrao_metrologico
    FOR EACH ROW
    EXECUTE FUNCTION padrao_incertezas_so_via_recal();

-- =============================================================
-- 2. INV-SOFT-002 — padrao_metrologico nunca DELETE fisico (soft-delete B)
-- =============================================================
CREATE OR REPLACE FUNCTION padrao_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-SOFT-002: PadraoMetrologico nao pode ser deletado fisicamente (soft-delete B ADR-0031 — usar estado BAIXADO/SUCATEADO + revogado_em; retencao 25a cl. 8.4).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER padrao_block_delete_trg
    BEFORE DELETE ON padrao_metrologico
    FOR EACH ROW
    EXECUTE FUNCTION padrao_block_delete();

-- =============================================================
-- 3. recal_externo_padrao — WORM pos retorno + aprovacao RT one-shot (C-4)
-- =============================================================
CREATE OR REPLACE FUNCTION recal_externo_padrao_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.retornado_em IS NOT NULL THEN
            IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
               OR NEW.padrao_id IS DISTINCT FROM OLD.padrao_id
               OR NEW.enviado_em IS DISTINCT FROM OLD.enviado_em
               OR NEW.lab_externo IS DISTINCT FROM OLD.lab_externo
               OR NEW.responsavel_envio_id_hash IS DISTINCT FROM OLD.responsavel_envio_id_hash
               OR NEW.status IS DISTINCT FROM OLD.status
               OR NEW.retornado_em IS DISTINCT FROM OLD.retornado_em
               OR NEW.cert_externo_novo_storage_key
                  IS DISTINCT FROM OLD.cert_externo_novo_storage_key
               OR NEW.incertezas_novas IS DISTINCT FROM OLD.incertezas_novas
               OR NEW.validade_nova IS DISTINCT FROM OLD.validade_nova
               OR NEW.valor_convencional_novo IS DISTINCT FROM OLD.valor_convencional_novo
            THEN
                RAISE EXCEPTION
                    'INV-PAD-006/WORM: recal externo imutavel pos retorno (cl. 6.5); reprocessar exige novo recal.';
            END IF;
            -- aprovacao RT (C-4): one-shot NULL -> valor; nunca re-aprovar/alterar.
            IF OLD.aprovado_rt_em IS NOT NULL
               AND NEW.aprovado_rt_em IS DISTINCT FROM OLD.aprovado_rt_em THEN
                RAISE EXCEPTION
                    'C-4: aprovacao critica do RT do recal ja registrada (one-shot, imutavel).';
            END IF;
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.retornado_em IS NOT NULL THEN
            RAISE EXCEPTION
                'WORM: recal externo retornado nao pode ser deletado (audit cl. 8.4).';
        END IF;
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER recal_externo_padrao_worm_trg
    BEFORE UPDATE OR DELETE ON recal_externo_padrao
    FOR EACH ROW
    EXECUTE FUNCTION recal_externo_padrao_worm_check();

-- =============================================================
-- 4. verificacao_intermediaria — APPEND-ONLY WORM (cl. 6.4.10)
-- =============================================================
CREATE OR REPLACE FUNCTION verificacao_intermediaria_append_only()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION
            'INV-022/WORM: VerificacaoIntermediaria e append-only (cl. 6.4.10 + cl. 8.4).';
    END IF;
    RAISE EXCEPTION
        'INV-022/WORM: VerificacaoIntermediaria nao pode ser deletada (audit imutavel).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER verificacao_intermediaria_append_only_trg
    BEFORE UPDATE OR DELETE ON verificacao_intermediaria
    FOR EACH ROW
    EXECUTE FUNCTION verificacao_intermediaria_append_only();

-- =============================================================
-- 5. intercomparacao_pt — WORM (inicio imutavel; resultado one-shot) cl. 6.6
-- =============================================================
CREATE OR REPLACE FUNCTION intercomparacao_pt_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
           OR NEW.padrao_id IS DISTINCT FROM OLD.padrao_id
           OR NEW.lab_organizador IS DISTINCT FROM OLD.lab_organizador
           OR NEW.protocolo IS DISTINCT FROM OLD.protocolo
           OR NEW.data_inicio IS DISTINCT FROM OLD.data_inicio
        THEN
            RAISE EXCEPTION
                'WORM: dados de inicio da intercomparacao/PT imutaveis pos abertura (cl. 6.6).';
        END IF;
        -- resultado one-shot: pos finalizacao (data_resultado NOT NULL) congela.
        IF OLD.data_resultado IS NOT NULL THEN
            IF NEW.resultado IS DISTINCT FROM OLD.resultado
               OR NEW.data_resultado IS DISTINCT FROM OLD.data_resultado
               OR NEW.zeta_score IS DISTINCT FROM OLD.zeta_score
               OR NEW.relatorio_pt_storage_key IS DISTINCT FROM OLD.relatorio_pt_storage_key
            THEN
                RAISE EXCEPTION
                    'WORM: resultado de PT ja registrado (one-shot, imutavel cl. 6.6).';
            END IF;
        END IF;
        RETURN NEW;
    END IF;
    IF TG_OP = 'DELETE' THEN
        IF OLD.data_resultado IS NOT NULL THEN
            RAISE EXCEPTION
                'WORM: PT finalizada nao pode ser deletada (audit cl. 8.4).';
        END IF;
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER intercomparacao_pt_worm_trg
    BEFORE UPDATE OR DELETE ON intercomparacao_pt
    FOR EACH ROW
    EXECUTE FUNCTION intercomparacao_pt_worm_check();

-- =============================================================
-- 6. analise_carta_controle — APPEND-ONLY WORM (ADR-0070 / INV-PAD-010)
-- =============================================================
CREATE OR REPLACE FUNCTION analise_carta_controle_append_only()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION
            'INV-PAD-010/WORM: AnaliseCartaControle e registro probatorio congelado (ADR-0070 + cl. 8.4).';
    END IF;
    RAISE EXCEPTION
        'INV-PAD-010/WORM: AnaliseCartaControle nao pode ser deletada (audit imutavel).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER analise_carta_controle_append_only_trg
    BEFORE UPDATE OR DELETE ON analise_carta_controle
    FOR EACH ROW
    EXECUTE FUNCTION analise_carta_controle_append_only();
"""

REVERSE = """
DROP TRIGGER IF EXISTS analise_carta_controle_append_only_trg ON analise_carta_controle;
DROP FUNCTION IF EXISTS analise_carta_controle_append_only();
DROP TRIGGER IF EXISTS intercomparacao_pt_worm_trg ON intercomparacao_pt;
DROP FUNCTION IF EXISTS intercomparacao_pt_worm_check();
DROP TRIGGER IF EXISTS verificacao_intermediaria_append_only_trg ON verificacao_intermediaria;
DROP FUNCTION IF EXISTS verificacao_intermediaria_append_only();
DROP TRIGGER IF EXISTS recal_externo_padrao_worm_trg ON recal_externo_padrao;
DROP FUNCTION IF EXISTS recal_externo_padrao_worm_check();
DROP TRIGGER IF EXISTS padrao_block_delete_trg ON padrao_metrologico;
DROP FUNCTION IF EXISTS padrao_block_delete();
DROP TRIGGER IF EXISTS padrao_incertezas_so_via_recal_trg ON padrao_metrologico;
DROP FUNCTION IF EXISTS padrao_incertezas_so_via_recal();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("padroes", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
