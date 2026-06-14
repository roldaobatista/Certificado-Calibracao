"""T-ORC-024 — constraints de integridade do modulo (defesa em profundidade).

- partial unique `orcamento_link_publico`: 1 link ATIVO por orcamento
  (WHERE revogado_em IS NULL — INV-ORC-LINK-TOKEN). Django UniqueConstraint nao
  suporta WHERE parcial -> SQL puro (molde uq_cliente_doc_ativo).
- unique numero por tenant: cliente ve sequencial limpo (D-ORC-18 gap-less).
- trigger estado terminal: estado terminal nao transiciona
  (INV-ORC-CONVERTIDO-TERMINAL; spec §5 aceita "CHECK/trigger" — transicao exige
  OLD vs NEW, logo trigger, nao CHECK de linha). Defesa do dominio `transicoes.py`.
- CHECK bifurcacao item: equipamento_id <-> tipo_atividade_alvo casados
  (INV-ORC-EQUIP-ITEM; defesa do ItemOrcamento.__post_init__).

# tests-coverage: tests/test_orcamentos_schema.py
# rls-policy: external 0002_rls_policies (constraints/trigger — nao cria policy)
# audit-immutability: skip -- trigger de transicao de estado, nao toca cadeia auditoria
"""

from __future__ import annotations

from django.db import migrations

FORWARD = """
-- =============================================================
-- 1 link publico ATIVO por orcamento (INV-ORC-LINK-TOKEN)
-- =============================================================
CREATE UNIQUE INDEX uq_orcamento_link_ativo
    ON orcamento_link_publico (orcamento_id)
    WHERE revogado_em IS NULL;

-- =============================================================
-- Numero sequencial unico por tenant (D-ORC-18 gap-less)
-- =============================================================
CREATE UNIQUE INDEX uq_orcamento_numero_tenant
    ON orcamento (tenant_id, numero);

-- =============================================================
-- INV-ORC-CONVERTIDO-TERMINAL: estado terminal nao transiciona.
-- =============================================================
CREATE OR REPLACE FUNCTION orcamento_estado_terminal_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF OLD.estado IN ('convertido', 'recusado', 'expirado', 'cancelado')
       AND NEW.estado <> OLD.estado THEN
        RAISE EXCEPTION
            'INV-ORC-CONVERTIDO-TERMINAL: estado terminal % nao transiciona (% -> %)',
            OLD.estado, OLD.estado, NEW.estado;
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER orcamento_estado_terminal_trg
    BEFORE UPDATE ON orcamento
    FOR EACH ROW
    EXECUTE FUNCTION orcamento_estado_terminal_check();

-- =============================================================
-- INV-ORC-EQUIP-ITEM: bifurcacao tecnico x comercial casada.
-- equipamento_id IS NULL  <=>  tipo_atividade_alvo = '' (item comercial)
-- equipamento_id NOT NULL <=>  tipo_atividade_alvo != '' (item tecnico)
-- =============================================================
ALTER TABLE item_orcamento ADD CONSTRAINT ck_item_orc_bifurcacao
    CHECK ((equipamento_id IS NULL) = (tipo_atividade_alvo = ''));
"""

REVERSE = """
ALTER TABLE item_orcamento DROP CONSTRAINT IF EXISTS ck_item_orc_bifurcacao;
DROP TRIGGER IF EXISTS orcamento_estado_terminal_trg ON orcamento;
DROP FUNCTION IF EXISTS orcamento_estado_terminal_check();
DROP INDEX IF EXISTS uq_orcamento_numero_tenant;
DROP INDEX IF EXISTS uq_orcamento_link_ativo;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0003_triggers_worm"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD, reverse_sql=REVERSE),
    ]
