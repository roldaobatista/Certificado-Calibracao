"""T-LIC-020 — Triggers PG WORM Padrão B (ADR-0031 / INV-LIC-WORM-001 / INV-033).

Espelha o padrão M5-M8 — não reinventar.

1. `revisao_documento` (append-only puro — INV-LIC-WORM-001):
   BEFORE UPDATE e BEFORE DELETE sempre RAISE. Histórico versionado é imutável;
   renovação/retificação = nova revisão (nunca edita a anterior). cl. 8.4 (25a).

2. `evento_emergencial_licenca` (append-only puro — INV-033):
   BEFORE UPDATE e BEFORE DELETE sempre RAISE. Liberação excepcional auditada é
   registro WORM imutável (cl. 8.7 — modo emergencial não é bypass silencioso).

3. `documento_regulatorio` (raiz Padrão B — ADR-0031):
   BEFORE DELETE sempre bloqueia (sustenta trilha probatória 25a cl. 8.4 — revogação
   usa `revogado_em`, nunca DELETE físico). BEFORE UPDATE: campos de IDENTIDADE são
   imutáveis (tenant/tipo/numero/orgao_emissor/criado_em/criado_por); `revogado_em`
   é one-shot. Campos de "estado corrente" (vigência atual via renovação,
   status_cache, responsavel_id, bloqueante, observacao, escopo, revision) são
   mutáveis controlados.

`alerta_vencimento` e `bloqueio_operacional` são Padrão A (estado-máquina
operacional) — sem WORM físico; protegidos só por RLS.

# audit-immutability: triggers WORM do modulo licencas_acreditacoes (nao tocam cadeia auditoria)
# tests-coverage: tests/regressao/test_inv_lic_p2_schema_triggers.py (WORM) + management/commands/validar_licencas_acreditacoes.py (GATE-LIC-DRILL-LOCAL)
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. revisao_documento — append-only puro (INV-LIC-WORM-001)
-- =============================================================
CREATE OR REPLACE FUNCTION revisao_documento_block_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-LIC-WORM-001: revisao_documento e append-only (historico versionado imutavel cl. 8.4); renovacao/retificacao = nova revisao, nunca UPDATE/DELETE.';
    RETURN NULL;
END;
$body$;

CREATE TRIGGER revisao_documento_block_update_trg
    BEFORE UPDATE ON revisao_documento
    FOR EACH ROW EXECUTE FUNCTION revisao_documento_block_mutation();

CREATE TRIGGER revisao_documento_block_delete_trg
    BEFORE DELETE ON revisao_documento
    FOR EACH ROW EXECUTE FUNCTION revisao_documento_block_mutation();

-- =============================================================
-- 2. evento_emergencial_licenca — append-only puro (INV-033)
-- =============================================================
CREATE OR REPLACE FUNCTION evento_emergencial_licenca_block_mutation()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-033: evento_emergencial_licenca e append-only WORM (liberacao excepcional auditada cl. 8.7 imutavel).';
    RETURN NULL;
END;
$body$;

CREATE TRIGGER evento_emergencial_licenca_block_update_trg
    BEFORE UPDATE ON evento_emergencial_licenca
    FOR EACH ROW EXECUTE FUNCTION evento_emergencial_licenca_block_mutation();

CREATE TRIGGER evento_emergencial_licenca_block_delete_trg
    BEFORE DELETE ON evento_emergencial_licenca
    FOR EACH ROW EXECUTE FUNCTION evento_emergencial_licenca_block_mutation();

-- =============================================================
-- 3. documento_regulatorio — raiz Padrao B (ADR-0031)
-- =============================================================
CREATE OR REPLACE FUNCTION documento_regulatorio_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-SOFT-002: documento_regulatorio nao pode ser deletado fisicamente (Padrao B ADR-0031 — usar revogado_em; retencao 25a cl. 8.4).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER documento_regulatorio_block_delete_trg
    BEFORE DELETE ON documento_regulatorio
    FOR EACH ROW EXECUTE FUNCTION documento_regulatorio_block_delete();

CREATE OR REPLACE FUNCTION documento_regulatorio_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos de IDENTIDADE imutaveis (nunca mudam apos cadastro).
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.tipo IS DISTINCT FROM OLD.tipo
       OR NEW.numero IS DISTINCT FROM OLD.numero
       OR NEW.orgao_emissor IS DISTINCT FROM OLD.orgao_emissor
       OR NEW.criado_em IS DISTINCT FROM OLD.criado_em
       OR NEW.criado_por IS DISTINCT FROM OLD.criado_por
    THEN
        RAISE EXCEPTION
            'INV-LIC-WORM-001: documento_regulatorio tem identidade imutavel (tenant/tipo/numero/orgao_emissor/criado_*); mudanca de vigencia = nova revisao.';
    END IF;
    -- revogacao one-shot (Padrao B)
    IF OLD.revogado_em IS NOT NULL
       AND NEW.revogado_em IS DISTINCT FROM OLD.revogado_em THEN
        RAISE EXCEPTION
            'INV-SOFT-002: documento ja revogado (revogado_em one-shot imutavel).';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER documento_regulatorio_worm_check_trg
    BEFORE UPDATE ON documento_regulatorio
    FOR EACH ROW EXECUTE FUNCTION documento_regulatorio_worm_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS documento_regulatorio_worm_check_trg ON documento_regulatorio;
DROP FUNCTION IF EXISTS documento_regulatorio_worm_check();
DROP TRIGGER IF EXISTS documento_regulatorio_block_delete_trg ON documento_regulatorio;
DROP FUNCTION IF EXISTS documento_regulatorio_block_delete();
DROP TRIGGER IF EXISTS evento_emergencial_licenca_block_delete_trg ON evento_emergencial_licenca;
DROP TRIGGER IF EXISTS evento_emergencial_licenca_block_update_trg ON evento_emergencial_licenca;
DROP FUNCTION IF EXISTS evento_emergencial_licenca_block_mutation();
DROP TRIGGER IF EXISTS revisao_documento_block_delete_trg ON revisao_documento;
DROP TRIGGER IF EXISTS revisao_documento_block_update_trg ON revisao_documento;
DROP FUNCTION IF EXISTS revisao_documento_block_mutation();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("licencas_acreditacoes", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
