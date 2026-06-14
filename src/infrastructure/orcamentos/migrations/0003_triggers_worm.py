"""T-ORC-023 — triggers WORM anti-mutacao (Padrao B / ADR-0031).

Duas familias:

(1) INSERT-only PURO (molde aceite_atividade ordens_servico/0007):
    - orcamento_aprovacao       (INV-ORC-APROVACAO-WORM / INV-001) — aceite rico + ip_hash.
    - analise_critica_orcamento (INV-ORC-ANALISE-WORM / D-ORC-15) — snapshot_hash no envelope.
    UPDATE e DELETE sempre RAISE.

(2) CONGELAMENTO one-shot (versao_orcamento — D-ORC-8 / Padrao B apos congelar):
    A versao corrente nasce com snapshot={} (rascunho) e e congelada ao enviar
    (snapshot preenchido UMA vez). O trigger permite:
      - preencher snapshot vazio ('{}'::jsonb) -> conteudo (one-shot);
      - setar/alterar revogado_em + motivo_revogacao (soft-revoke — Wave B);
    e BLOQUEIA:
      - re-editar snapshot ja congelado (OLD.snapshot <> '{}');
      - mudar o nucleo (orcamento_id / tenant_id / numero_versao / criada_por);
      - DELETE.

Defesa em profundidade — GRANT (0005) concede o opcode; o trigger nega a mutacao indevida.

# tests-coverage: tests/test_orcamentos_schema.py
# (WORM bloqueia UPDATE/DELETE em aprovacao/analise; versao congela one-shot — drill PG-real)
"""

from __future__ import annotations

from django.db import migrations

# (1) Tabelas INSERT-only puro.
TABELAS_WORM_PURO = (
    "orcamento_aprovacao",
    "analise_critica_orcamento",
)


def _worm_puro_forward(tabela: str) -> str:
    return f"""
-- =============================================================
-- {tabela} - WORM Padrao B puro (ADR-0031): INSERT-only.
-- =============================================================
CREATE OR REPLACE FUNCTION {tabela}_anti_mutation_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        RAISE EXCEPTION
            '{tabela} eh imutavel pos-INSERT (Padrao B ADR-0031 / WORM)';
    END IF;
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            '{tabela} nao pode ser deletado (trilha imutavel)';
    END IF;
    RETURN NEW;
END;
$body$;

CREATE TRIGGER {tabela}_anti_mutation_trg
    BEFORE UPDATE OR DELETE ON {tabela}
    FOR EACH ROW
    EXECUTE FUNCTION {tabela}_anti_mutation_check();
"""


def _worm_puro_reverse(tabela: str) -> str:
    return f"""
DROP TRIGGER IF EXISTS {tabela}_anti_mutation_trg ON {tabela};
DROP FUNCTION IF EXISTS {tabela}_anti_mutation_check();
"""


# (2) versao_orcamento — congelamento one-shot.
VERSAO_FORWARD = """
-- =============================================================
-- versao_orcamento - congelamento one-shot (D-ORC-8 / Padrao B apos congelar).
-- =============================================================
CREATE OR REPLACE FUNCTION versao_orcamento_congelamento_check()
RETURNS TRIGGER LANGUAGE plpgsql AS $body$
BEGIN
    IF TG_OP = 'DELETE' THEN
        RAISE EXCEPTION
            'versao_orcamento nao pode ser deletada (trilha imutavel)';
    END IF;

    -- Nucleo imutavel desde o INSERT.
    IF NEW.orcamento_id <> OLD.orcamento_id
       OR NEW.tenant_id <> OLD.tenant_id
       OR NEW.numero_versao <> OLD.numero_versao
       OR NEW.criada_por <> OLD.criada_por THEN
        RAISE EXCEPTION
            'versao_orcamento: nucleo imutavel (orcamento/tenant/numero_versao/criada_por)';
    END IF;

    -- Snapshot one-shot: so pode ser preenchido quando ainda vazio ('{}'::jsonb).
    IF OLD.snapshot <> '{}'::jsonb AND NEW.snapshot IS DISTINCT FROM OLD.snapshot THEN
        RAISE EXCEPTION
            'versao_orcamento: snapshot ja congelado eh imutavel (Padrao B ADR-0031)';
    END IF;

    RETURN NEW;
END;
$body$;

CREATE TRIGGER versao_orcamento_congelamento_trg
    BEFORE UPDATE OR DELETE ON versao_orcamento
    FOR EACH ROW
    EXECUTE FUNCTION versao_orcamento_congelamento_check();
"""

VERSAO_REVERSE = """
DROP TRIGGER IF EXISTS versao_orcamento_congelamento_trg ON versao_orcamento;
DROP FUNCTION IF EXISTS versao_orcamento_congelamento_check();
"""


SQL_FORWARD = "\n".join(_worm_puro_forward(t) for t in TABELAS_WORM_PURO) + "\n" + VERSAO_FORWARD
SQL_REVERSE = VERSAO_REVERSE + "\n" + "\n".join(_worm_puro_reverse(t) for t in TABELAS_WORM_PURO)


class Migration(migrations.Migration):
    dependencies = [
        ("orcamentos", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(sql=SQL_FORWARD, reverse_sql=SQL_REVERSE),
    ]
