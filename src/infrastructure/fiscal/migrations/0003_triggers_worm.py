"""T-FIS-020 — Triggers PG WORM Padrão B (ADR-0031 / INV-FIS-004 / D-FIS-4).

Espelha o molde M6 (`escopo_cmc_*`) — não reinventar.

1. `nota_fiscal_servico_block_delete` (INV-FIS-008 — retenção fiscal 5a):
   BEFORE DELETE sempre bloqueia. NFS-e é documento fiscal probatório; cancelamento
   usa `status=CANCELED` + `cancelado_em`, nunca DELETE físico.

2. `nota_fiscal_servico_worm_check` (INV-FIS-004 — D-FIS-4):
   BEFORE UPDATE. Campos PROBATÓRIOS são imutáveis (tenant/origem/versao/
   tipo_servico/perfil/valor/cliente_hash/certificado/declaracao/tipo_acreditacao/
   snapshot_hash). MUTÁVEIS (transição da máquina de estados, validada no domínio):
   `status`, `provider_invoice_id`, `autorizacao_codigo`, `rejeicao_motivo`,
   `motivo_cancelamento`, `revision`, timestamps. `emitido_em` e `cancelado_em` são
   ONE-SHOT (NULL→valor; não voltam). A imutabilidade probatória vem do
   `snapshot_hash` (emissão) + evento append-only na cadeia hash — não do bloqueio
   do `status` (que precisa transicionar PENDING→AUTHORIZED|REJECTED; AUTHORIZED→
   CANCELED).

# audit-immutability: triggers WORM do modulo fiscal (nao tocam cadeia auditoria)
# tests-coverage: tests/test_fiscal_schema_fatia1b.py (WORM) + management/commands/validar_fiscal_nfse.py
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1. INV-FIS-008 — nota_fiscal_servico nunca DELETE fisico (retencao 5a)
-- =============================================================
CREATE OR REPLACE FUNCTION nota_fiscal_servico_block_delete()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    RAISE EXCEPTION
        'INV-FIS-008: NotaFiscalServico nao pode ser deletada fisicamente (retencao fiscal 5a — cancelamento usa status=CANCELED + cancelado_em).';
    RETURN OLD;
END;
$body$;

CREATE TRIGGER nota_fiscal_servico_block_delete_trg
    BEFORE DELETE ON nota_fiscal_servico
    FOR EACH ROW
    EXECUTE FUNCTION nota_fiscal_servico_block_delete();

-- =============================================================
-- 2. INV-FIS-004 — campos probatorios imutaveis (WORM Padrao B; status mutavel)
-- =============================================================
CREATE OR REPLACE FUNCTION nota_fiscal_servico_worm_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    -- Campos probatorios congelados pos-INSERT (D-FIS-4).
    IF NEW.tenant_id IS DISTINCT FROM OLD.tenant_id
       OR NEW.origem_id IS DISTINCT FROM OLD.origem_id
       OR NEW.versao IS DISTINCT FROM OLD.versao
       OR NEW.tipo_servico IS DISTINCT FROM OLD.tipo_servico
       OR NEW.perfil_no_evento IS DISTINCT FROM OLD.perfil_no_evento
       OR NEW.valor_centavos IS DISTINCT FROM OLD.valor_centavos
       OR NEW.cliente_referencia_hash IS DISTINCT FROM OLD.cliente_referencia_hash
       OR NEW.certificado_id IS DISTINCT FROM OLD.certificado_id
       OR NEW.declaracao_id IS DISTINCT FROM OLD.declaracao_id
       OR NEW.tipo_acreditacao_vinculo IS DISTINCT FROM OLD.tipo_acreditacao_vinculo
       OR NEW.snapshot_hash IS DISTINCT FROM OLD.snapshot_hash
    THEN
        RAISE EXCEPTION
            'INV-FIS-004/WORM: campos probatorios da NFS-e sao imutaveis pos-emissao (ADR-0031 Padrao B / D-FIS-4); so status/timestamps transicionam.';
    END IF;

    -- emitido_em one-shot (NULL -> valor; nunca volta nem muda)
    IF OLD.emitido_em IS NOT NULL
       AND NEW.emitido_em IS DISTINCT FROM OLD.emitido_em THEN
        RAISE EXCEPTION 'INV-FIS-004: emitido_em e one-shot (imutavel apos preenchido).';
    END IF;

    -- cancelado_em one-shot
    IF OLD.cancelado_em IS NOT NULL
       AND NEW.cancelado_em IS DISTINCT FROM OLD.cancelado_em THEN
        RAISE EXCEPTION 'INV-FIS-004: cancelado_em e one-shot (imutavel apos preenchido).';
    END IF;

    RETURN NEW;
END;
$body$;

CREATE TRIGGER nota_fiscal_servico_worm_check_trg
    BEFORE UPDATE ON nota_fiscal_servico
    FOR EACH ROW
    EXECUTE FUNCTION nota_fiscal_servico_worm_check();
"""

REVERSE = """
DROP TRIGGER IF EXISTS nota_fiscal_servico_worm_check_trg ON nota_fiscal_servico;
DROP FUNCTION IF EXISTS nota_fiscal_servico_worm_check();
DROP TRIGGER IF EXISTS nota_fiscal_servico_block_delete_trg ON nota_fiscal_servico;
DROP FUNCTION IF EXISTS nota_fiscal_servico_block_delete();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("fiscal", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
