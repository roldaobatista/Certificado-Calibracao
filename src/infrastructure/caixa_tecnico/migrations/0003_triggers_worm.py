"""T-CT-024 — Triggers WORM e block-delete do caixa_tecnico.

3 grupos de proteção (molde contas_receber/0003 + orcamentos/0003):

(a) Anti-mutação despesa_validada:
    ``despesa_caixa_anti_mutacao`` — BEFORE UPDATE OR DELETE ON despesa_caixa
    FOR EACH ROW WHEN (OLD.status = 'validada') → RAISE;
    Permite reapresentação (rejeitada→pendente) e cancelamento (pendente→cancelada),
    mas BLOQUEIA qualquer UPDATE ou DELETE quando estado=validada.

(b) Block-delete despesa SEMPRE (documento fiscal 5a):
    ``despesa_caixa_block_delete`` — BEFORE DELETE ON despesa_caixa
    FOR EACH ROW → RAISE sempre;
    Molde título_receber_block_delete (D-CT-5a / INV-CT-IMUT-001).
    DELETE físico proibido em qualquer estado.

(c) PrestacaoContas WORM — campos financeiros congelados pós-INSERT:
    ``prestacao_contas_caixa_worm`` — BEFORE UPDATE ON prestacao_contas_caixa
    FOR EACH ROW → RAISE se tentar alterar:
      total_adiantado, total_despesas_validadas, saldo_final, direcao, fechada_em.
    UPDATE de pdf_url e observacoes é permitido (D-CT-8 / INV-CT-PRESTACAO-WORM-001).
"""

from django.db import migrations

# --------------------------------------------------------------------------
# (a+b) despesa_caixa — anti-mutação validada + block-delete absoluto
# --------------------------------------------------------------------------

_SQL_DESPESA_WORM = """
-- (b) Block-delete absoluto da despesa (documento fiscal — 5a de retenção)
CREATE OR REPLACE FUNCTION despesa_caixa_block_delete_fn()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'despesa_caixa: DELETE físico proibido — retenção 5 anos (D-CT-5a/INV-CT-IMUT-001). '
        'Para cancelar use UPDATE estado=''cancelada''.'
        USING ERRCODE = 'restrict_violation';
END;
$$;

DROP TRIGGER IF EXISTS despesa_caixa_block_delete ON despesa_caixa;
CREATE TRIGGER despesa_caixa_block_delete
    BEFORE DELETE ON despesa_caixa
    FOR EACH ROW
    EXECUTE FUNCTION despesa_caixa_block_delete_fn();

-- (a) Anti-mutação: bloqueia UPDATE e DELETE quando estado='validada'
--     Reapresentação (rejeitada→pendente) e cancelamento NÃO disparam
--     pois partem de estado != 'validada'.
CREATE OR REPLACE FUNCTION despesa_caixa_anti_mutacao_fn()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.estado = 'validada' THEN
        RAISE EXCEPTION
            'despesa_caixa: mutação proibida — despesa no estado ''validada'' é WORM '
            '(D-CT-3/INV-CT-IMUT-001). Correção = nova despesa tipo ''estorno''.'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS despesa_caixa_anti_mutacao ON despesa_caixa;
CREATE TRIGGER despesa_caixa_anti_mutacao
    BEFORE UPDATE ON despesa_caixa
    FOR EACH ROW
    WHEN (OLD.estado = 'validada')
    EXECUTE FUNCTION despesa_caixa_anti_mutacao_fn();
"""

_SQL_DESPESA_WORM_REVERSO = """
DROP TRIGGER IF EXISTS despesa_caixa_block_delete ON despesa_caixa;
DROP FUNCTION IF EXISTS despesa_caixa_block_delete_fn();
DROP TRIGGER IF EXISTS despesa_caixa_anti_mutacao ON despesa_caixa;
DROP FUNCTION IF EXISTS despesa_caixa_anti_mutacao_fn();
"""

# --------------------------------------------------------------------------
# (c) prestacao_contas_caixa — campos financeiros WORM pós-INSERT
# --------------------------------------------------------------------------

_SQL_PRESTACAO_WORM = """
-- (c) WORM financeiro da prestação — congela campos após fechamento.
--     UPDATE em pdf_url / observacoes é PERMITIDO.
CREATE OR REPLACE FUNCTION prestacao_contas_caixa_worm_fn()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    IF OLD.total_adiantado IS DISTINCT FROM NEW.total_adiantado
    OR OLD.total_despesas_validadas IS DISTINCT FROM NEW.total_despesas_validadas
    OR OLD.saldo_final IS DISTINCT FROM NEW.saldo_final
    OR OLD.direcao IS DISTINCT FROM NEW.direcao
    OR OLD.fechada_em IS DISTINCT FROM NEW.fechada_em
    THEN
        RAISE EXCEPTION
            'prestacao_contas_caixa: campos financeiros congelados pós-fechamento — '
            'total_adiantado, total_despesas_validadas, saldo_final, direcao, fechada_em '
            'são WORM (D-CT-8/INV-CT-PRESTACAO-WORM-001).'
            USING ERRCODE = 'restrict_violation';
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS prestacao_contas_caixa_worm ON prestacao_contas_caixa;
CREATE TRIGGER prestacao_contas_caixa_worm
    BEFORE UPDATE ON prestacao_contas_caixa
    FOR EACH ROW
    EXECUTE FUNCTION prestacao_contas_caixa_worm_fn();

-- Block-delete na prestacao (trilha WORM)
CREATE OR REPLACE FUNCTION prestacao_contas_caixa_block_delete_fn()
RETURNS trigger
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION
        'prestacao_contas_caixa: DELETE proibido — registro financeiro imutável (D-CT-8).'
        USING ERRCODE = 'restrict_violation';
END;
$$;

DROP TRIGGER IF EXISTS prestacao_contas_caixa_block_delete ON prestacao_contas_caixa;
CREATE TRIGGER prestacao_contas_caixa_block_delete
    BEFORE DELETE ON prestacao_contas_caixa
    FOR EACH ROW
    EXECUTE FUNCTION prestacao_contas_caixa_block_delete_fn();
"""

_SQL_PRESTACAO_WORM_REVERSO = """
DROP TRIGGER IF EXISTS prestacao_contas_caixa_worm ON prestacao_contas_caixa;
DROP FUNCTION IF EXISTS prestacao_contas_caixa_worm_fn();
DROP TRIGGER IF EXISTS prestacao_contas_caixa_block_delete ON prestacao_contas_caixa;
DROP FUNCTION IF EXISTS prestacao_contas_caixa_block_delete_fn();
"""


class Migration(migrations.Migration):
    dependencies = [
        ("caixa_tecnico", "0002_rls_policies"),
    ]

    operations = [
        migrations.RunSQL(
            sql=_SQL_DESPESA_WORM,
            reverse_sql=_SQL_DESPESA_WORM_REVERSO,
        ),
        migrations.RunSQL(
            sql=_SQL_PRESTACAO_WORM,
            reverse_sql=_SQL_PRESTACAO_WORM_REVERSO,
        ),
    ]
