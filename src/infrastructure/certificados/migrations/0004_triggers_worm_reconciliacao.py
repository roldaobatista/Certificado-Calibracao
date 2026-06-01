"""T-CER-023 — Triggers PG WORM Padrão B (ADR-0031 / INV-CER-WORM-001 / INV-SOFT-002).

Espelha o padrão M6/M7 (`*_block_delete` + `*_worm_check`) — não reinventar. NÃO
toca o trigger `equipamento_imutabilidade_pos_cert` do 0001 (lê `'emitido'` literal).

1. `ponto_reconciliado` / `analise_reconciliacao_cert` — APPEND-ONLY puro: BEFORE
   DELETE sempre bloqueia (retenção 25a cl. 8.4) + BEFORE UPDATE sempre bloqueia
   (snapshots imutáveis — não há campo mutável legítimo).

2. `certificados` — WORM SELETIVO pós `status='emitido'`: campos técnicos/probatórios
   imutáveis; permitidas SÓ as transições one-shot da máquina de estados:
   `emitido → substituida` (reemissão T-CER-043) ou `emitido → revogado`, ligar
   `revogado_em` (NULL→valor one-shot) e bump de `revision` (CAS). `rascunho` é
   editável (não materializado nesta frente, mas o stub Marco 2 pode tê-lo).

# audit-immutability: triggers WORM do modulo certificados (nao tocam cadeia auditoria nem trigger INV-025 de equipamento)
# tests-coverage: tests/regressao/test_inv_cer_p2_schema_triggers.py (WORM) + management/commands/validar_certificados.py (GATE-CER-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. APPEND-ONLY: ponto_reconciliado + analise_reconciliacao_cert
-- =============================================================
CREATE OR REPLACE FUNCTION ponto_reconciliado_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CER-WORM-001/INV-SOFT-002: ponto_reconciliado e append-only (retencao 25a cl. 8.4); correcao via reemissao versionada do certificado, nunca DELETE.';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER ponto_reconciliado_block_delete_trg
    BEFORE DELETE ON ponto_reconciliado
    FOR EACH ROW EXECUTE FUNCTION ponto_reconciliado_block_delete();

CREATE OR REPLACE FUNCTION ponto_reconciliado_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CER-WORM-001: ponto_reconciliado e imutavel pos-INSERT (WORM Padrao B ADR-0031); correcao via reemissao versionada.';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER ponto_reconciliado_worm_check_trg
    BEFORE UPDATE ON ponto_reconciliado
    FOR EACH ROW EXECUTE FUNCTION ponto_reconciliado_worm_check();

CREATE OR REPLACE FUNCTION analise_reconciliacao_cert_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CER-WORM-001/INV-SOFT-002: analise_reconciliacao_cert e append-only (decisao WORM do RT, cl. 7.10.1 + retencao 25a); nunca DELETE.';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER analise_reconciliacao_cert_block_delete_trg
    BEFORE DELETE ON analise_reconciliacao_cert
    FOR EACH ROW EXECUTE FUNCTION analise_reconciliacao_cert_block_delete();

CREATE OR REPLACE FUNCTION analise_reconciliacao_cert_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-CER-WORM-001: analise_reconciliacao_cert e imutavel pos-INSERT (decisao WORM do RT — ADR-0070).';
    RETURN NEW;
END;
$body$;

CREATE TRIGGER analise_reconciliacao_cert_worm_check_trg
    BEFORE UPDATE ON analise_reconciliacao_cert
    FOR EACH ROW EXECUTE FUNCTION analise_reconciliacao_cert_worm_check();

-- =============================================================
-- 2. certificados — WORM seletivo pos status='emitido' (INV-CER-WORM-001)
-- =============================================================
CREATE OR REPLACE FUNCTION certificado_emissao_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Estados terminais (substituida/revogado): TUDO imutavel — WORM retroativo
    -- (cl. 8.4); o certificado sustenta prova mesmo apos substituido/revogado.
    -- Garante revogado_em/status one-shot: uma vez terminal, nenhum UPDATE passa.
    IF OLD.status IN ('substituida', 'revogado') THEN
        RAISE EXCEPTION
            'INV-CER-WORM-001: certificado em estado terminal (%) e imutavel (WORM ADR-0078 / cl. 8.4 retroativo); correcao via reemissao versionada (US-CER-004).', OLD.status;
    END IF;
    IF OLD.status = 'emitido' THEN
        -- campos tecnicos/probatorios congelados
        IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
           OR NEW.equipamento_id IS DISTINCT FROM OLD.equipamento_id
           OR NEW.calibracao_id IS DISTINCT FROM OLD.calibracao_id
           OR NEW.numero_interno IS DISTINCT FROM OLD.numero_interno
           OR NEW.numero_certificado IS DISTINCT FROM OLD.numero_certificado
           OR NEW.versao IS DISTINCT FROM OLD.versao
           OR NEW.perfil_emissor_no_momento IS DISTINCT FROM OLD.perfil_emissor_no_momento
           OR NEW.faixa_certificado_min IS DISTINCT FROM OLD.faixa_certificado_min
           OR NEW.faixa_certificado_max IS DISTINCT FROM OLD.faixa_certificado_max
           OR NEW.tipo_acreditacao IS DISTINCT FROM OLD.tipo_acreditacao
           OR NEW.snapshot_equipamento_json IS DISTINCT FROM OLD.snapshot_equipamento_json
           OR NEW.snapshot_padroes_usados_json IS DISTINCT FROM OLD.snapshot_padroes_usados_json
           OR NEW.regra_decisao_snapshot IS DISTINCT FROM OLD.regra_decisao_snapshot
           OR NEW.reconciliacao_hash IS DISTINCT FROM OLD.reconciliacao_hash
           OR NEW.emitido_em IS DISTINCT FROM OLD.emitido_em
        THEN
            RAISE EXCEPTION
                'INV-CER-WORM-001: certificado emitido e imutavel nos campos tecnicos (ADR-0078 / cl. 8.4); correcao via reemissao versionada (US-CER-004), nunca UPDATE in-place.';
        END IF;
        -- a partir de emitido, status so pode permanecer emitido OU ir a
        -- substituida/revogado (a transicao em si seta revogado_em — one-shot,
        -- protegido pelo bloco terminal acima nos UPDATEs seguintes).
        IF NEW.status NOT IN ('emitido', 'substituida', 'revogado') THEN
            RAISE EXCEPTION
                'INV-CER-WORM-001: transicao de status invalida a partir de emitido (apenas substituida/revogado).';
        END IF;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER certificado_emissao_worm_check_trg
    BEFORE UPDATE ON certificados
    FOR EACH ROW EXECUTE FUNCTION certificado_emissao_worm_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS certificado_emissao_worm_check_trg ON certificados;
DROP FUNCTION IF EXISTS certificado_emissao_worm_check();
DROP TRIGGER IF EXISTS analise_reconciliacao_cert_worm_check_trg ON analise_reconciliacao_cert;
DROP FUNCTION IF EXISTS analise_reconciliacao_cert_worm_check();
DROP TRIGGER IF EXISTS analise_reconciliacao_cert_block_delete_trg ON analise_reconciliacao_cert;
DROP FUNCTION IF EXISTS analise_reconciliacao_cert_block_delete();
DROP TRIGGER IF EXISTS ponto_reconciliado_worm_check_trg ON ponto_reconciliado;
DROP FUNCTION IF EXISTS ponto_reconciliado_worm_check();
DROP TRIGGER IF EXISTS ponto_reconciliado_block_delete_trg ON ponto_reconciliado;
DROP FUNCTION IF EXISTS ponto_reconciliado_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("certificados", "0003_rls_reconciliacao"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
