"""T-CLI-103 / INV-CLI-001: âncora de identidade canônica em `cliente`.

Adiciona coluna `cliente_canonico_id UUID NOT NULL` apontando o vencedor da
cadeia de mesclagens (US-CLI-005). Default na criação: o próprio `id` do
cliente — significa "cliente canônico de si mesmo" (nunca foi mesclado).
Após mesclagem (perdedor → vencedor), `cliente_canonico_id` do perdedor é
atualizado para `vencedor.id`.

Trigger PG runtime que valida transição self → vencedor_id_vivo entra na
migration de T-CLI-113 (AC-CLI-005-7); aqui só estrutura + populate.

Pra resolver a cadeia (qual cliente vivo representa hoje um cliente
mesclado), ver `src/infrastructure/clientes/canonico.py`
`resolver_cliente_canonico`.

Implementação do backfill: usa coluna `GENERATED ALWAYS AS (id) STORED`
temporária + `DROP EXPRESSION` (PG 12+). Isso evita rodar UPDATE manual
sob RLS fail-loud (a função `require_tenant_ctx()` RAISE em contexto vazio
de migration; e desabilitar RLS na tabela durante a migration introduz
janela de risco em produção). DDL `GENERATED` é avaliado no escopo da
linha sem precisar de contexto de tenant.
"""

# rls-policy: external none -- ADD COLUMN em tabela existente; RLS herdada
# tests-coverage: tests/test_clientes_us_cli_005_canonico.py
# audit-immutability: skip -- esta migration NAO toca auditoria

from __future__ import annotations

from django.db import migrations, models

# Sequência DDL idempotente:
# 1. Coluna nasce como GENERATED ALWAYS AS (id) STORED → preenche linhas
#    existentes copiando do id sem precisar de contexto tenant.
# 2. DROP EXPRESSION transforma em coluna normal preservando os valores
#    já gravados. Permite UPDATE posterior (necessário pra mesclagem).
# 3. SET NOT NULL endurece o invariante (INV-CLI-001).
# 4. Trigger BEFORE INSERT garante que rows novas SEM cliente_canonico_id
#    explicito recebam `NEW.id` — Django não precisa conhecer o campo no
#    INSERT do model (compatibilidade com use cases existentes que ainda
#    nao foram refatorados pra setar o campo). T-CLI-113 adiciona BEFORE
#    UPDATE com validação de transição.
# 5. CREATE INDEX permite resolver canônico O(log n).
FORWARD_SQL = """
ALTER TABLE clientes
    ADD COLUMN cliente_canonico_id UUID GENERATED ALWAYS AS (id) STORED;
ALTER TABLE clientes
    ALTER COLUMN cliente_canonico_id DROP EXPRESSION;
ALTER TABLE clientes
    ALTER COLUMN cliente_canonico_id SET NOT NULL;

CREATE OR REPLACE FUNCTION cliente_canonico_default_on_insert()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF NEW.cliente_canonico_id IS NULL THEN
        NEW.cliente_canonico_id := NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER cliente_canonico_default_trg
    BEFORE INSERT ON clientes
    FOR EACH ROW EXECUTE FUNCTION cliente_canonico_default_on_insert();

CREATE INDEX clientes_cliente_canonico_id_idx
    ON clientes (cliente_canonico_id);
"""

REVERSE_SQL = """
DROP INDEX IF EXISTS clientes_cliente_canonico_id_idx;
DROP TRIGGER IF EXISTS cliente_canonico_default_trg ON clientes;
DROP FUNCTION IF EXISTS cliente_canonico_default_on_insert();
ALTER TABLE clientes DROP COLUMN IF EXISTS cliente_canonico_id;
"""


class Migration(migrations.Migration):
    dependencies = [
        ("clientes", "0016_alter_cliente_aceite_lgpd_base_legal_and_more"),
    ]

    operations = [
        # Estado do banco (DDL real)
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
        # Estado do model do Django (sem alterar o banco — state_operations só)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="cliente",
                    name="cliente_canonico_id",
                    field=models.UUIDField(
                        db_index=True,
                        help_text=(
                            "Vencedor imediato da cadeia de mesclagem; igual ao proprio id ate "
                            "que uma mesclagem aponte pra outro cliente vivo do mesmo tenant. "
                            "Resolver canonico via canonico.resolver_cliente_canonico."
                        ),
                    ),
                ),
            ],
        ),
    ]
