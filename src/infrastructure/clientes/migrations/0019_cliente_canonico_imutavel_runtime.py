"""T-CLI-113 / AC-CLI-005-7: trigger PG BEFORE UPDATE cliente_canonico_imutavel.

Defesa em profundidade runtime do INV-CLI-001 (identidade canônica). Hook
de migração `cliente-canonico-imutavel.sh` cobre tempo de CI; este trigger
cobre tempo de runtime — `update_one_off`, SQL cru ou agente IA que tente
manipular `cliente_canonico_id` é barrado pelo banco.

Regras de transição (apenas quando NEW.cliente_canonico_id != OLD.*):
1. NEW NULL → bloqueado (INV-CLI-001 + NOT NULL).
2. NEW = NEW.id (self-aponte) → só permitido se OLD = OLD.id (criação
   default ainda vigente); reverter pra self após mesclagem é proibido.
3. NEW = outro_id → deve apontar pra cliente VIVO do MESMO tenant.
   - target inexistente: erro.
   - target.tenant_id != NEW.tenant_id: cross-tenant proibido.
   - target.deletado_em != NULL: vencedor morto proibido.

Casos válidos cobertos:
- 1ª mesclagem: `self → vencedor_vivo` (perdedor.cliente_canonico_id =
  vencedor.id).
- Path compression: `intermediario → vencedor_final` (A→B→C: compressão
  faz A→C diretamente; trigger valida que C é vivo do mesmo tenant).

A leitura de `clientes WHERE id = NEW.cliente_canonico_id` dentro da
trigger passa por RLS — só funciona se o UPDATE estiver em contexto de
tenant ativo (que é o esperado em produção). Defesa em profundidade vs
RLS USING: se RLS retornar zero (cross-tenant) a query devolve NOT FOUND
e a trigger ainda assim levanta.
"""

# rls-policy: external none -- nao cria tabela; trigger sobre RLS herdada
# tests-coverage: tests/test_clientes_us_cli_005_canonico_trigger_t_cli_113.py
# audit-immutability: skip -- esta migration NAO toca auditoria

from __future__ import annotations

from django.db import migrations

FORWARD_SQL = """
CREATE OR REPLACE FUNCTION cliente_canonico_imutavel_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
DECLARE
    target_tenant uuid;
    target_deletado timestamp with time zone;
BEGIN
    -- 1) NEW NULL bloqueado (defesa adicional ao NOT NULL).
    IF NEW.cliente_canonico_id IS NULL THEN
        RAISE EXCEPTION 'cliente_canonico_id NAO pode ser NULL (INV-CLI-001)'
            USING ERRCODE = '23514'; -- check_violation
    END IF;

    -- 2) Self-aponte (NEW=self.id) — soh permitido se OLD ainda era self
    --    (criacao default vigente). Reverter apos mesclagem proibido.
    IF NEW.cliente_canonico_id = NEW.id THEN
        IF OLD.cliente_canonico_id IS DISTINCT FROM OLD.id THEN
            RAISE EXCEPTION 'Reverter cliente_canonico_id pra self proibido (INV-CLI-001 imutavel pos-mesclagem)'
                USING ERRCODE = '23514';
        END IF;
        RETURN NEW;
    END IF;

    -- 3) NEW aponta pra outro cliente: deve ser VIVO no MESMO tenant.
    SELECT tenant_id, deletado_em INTO target_tenant, target_deletado
    FROM clientes WHERE id = NEW.cliente_canonico_id;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'cliente_canonico_id=% nao existe ou nao visivel no tenant (INV-CLI-001 + INV-TENANT-001)',
            NEW.cliente_canonico_id
            USING ERRCODE = '23503'; -- foreign_key_violation
    END IF;

    IF target_tenant IS DISTINCT FROM NEW.tenant_id THEN
        RAISE EXCEPTION 'cliente_canonico_id cross-tenant proibido (INV-TENANT-001 + INV-CLI-001)'
            USING ERRCODE = '23514';
    END IF;

    IF target_deletado IS NOT NULL THEN
        RAISE EXCEPTION 'cliente_canonico_id deve apontar pra cliente vivo (INV-CLI-001)'
            USING ERRCODE = '23514';
    END IF;

    RETURN NEW;
END;
$$;

-- Trigger so dispara quando o campo MUDA — UPDATE de outros campos passa
-- direto. Defesa em profundidade pro caminho de mesclagem (US-CLI-005)
-- e pra path compression (canonico.py _comprimir_cadeia).
CREATE TRIGGER cliente_canonico_imutavel_trg
    BEFORE UPDATE OF cliente_canonico_id ON clientes
    FOR EACH ROW
    WHEN (OLD.cliente_canonico_id IS DISTINCT FROM NEW.cliente_canonico_id)
    EXECUTE FUNCTION cliente_canonico_imutavel_check();
"""

REVERSE_SQL = """
DROP TRIGGER IF EXISTS cliente_canonico_imutavel_trg ON clientes;
DROP FUNCTION IF EXISTS cliente_canonico_imutavel_check();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0018_lgpd_enums_5_bases_3_origens"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
    ]
