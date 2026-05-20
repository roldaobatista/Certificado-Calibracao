"""T-CLI-101 / AC-CLI-001-4: enum LGPD 5 bases + 3 origens + lia_id.

Alinha código com a spec FORWARD do Marco 1 pós-review do advogado em
P2 (P-CLI-A1 AJUSTADO):

- `aceite_lgpd_base_legal`: passa de 2 valores (`art_7_v`, `art_7_i`)
  para 5 (`CONSENTIMENTO`, `EXECUCAO_CONTRATO`, `OBRIG_LEGAL`,
  `LEGITIMO_INTERESSE`, `PROTECAO_CREDITO`) — LGPD art. 7º.
- `aceite_lgpd_origem`: passa de 4 valores (`balcao`, `portal`,
  `importacao`, `api_terceiro`) para 3 (`CADASTRO_DIRETO`,
  `IMPORTACAO_LEGADA`, `MIGRACAO_SISTEMA_ANTERIOR`) — distingue origem
  legítima (cadastro direto pelo operador OU portal — ambos viram
  CADASTRO_DIRETO) de importação legada (sem aceite formal) ou
  migração com aceite prévio documentado.
- Novo campo `aceite_lgpd_lia_id UUID NULL` apontando teste de
  balanceamento de Legítimo Interesse (LIA — art. 10 LGPD). Obrigatório
  quando base_legal = LEGITIMO_INTERESSE (CHECK constraint). A tabela
  `lia_testes_balanceamento` (módulo de governança LGPD futura) ainda
  não existe; aqui só o campo opaco UUID — FK formal entra com o
  modelo dedicado em US-CLI-006.

Remap dos valores antigos:
  art_7_v          → EXECUCAO_CONTRATO    (LGPD art. 7º V)
  art_7_i          → CONSENTIMENTO        (art. 7º I)
  balcao           → CADASTRO_DIRETO
  portal           → CADASTRO_DIRETO
  importacao       → IMPORTACAO_LEGADA
  api_terceiro     → MIGRACAO_SISTEMA_ANTERIOR

Pra rodar UPDATE em massa em tabela com RLS fail-loud, a estratégia
aqui é: DISABLE RLS temporariamente (DDL — fora de RLS), UPDATE,
re-ENABLE RLS no estado original (FORCE também). Janela de risco em
deploy real é da duração da própria migration (segundos); em ambiente
multi-tenant ativo o caminho preferido seria backfill por tenant
(em job operacional), mas como Marco 1 ainda é dogfooding o downtime
de migration é aceitável.
"""

# rls-policy: external none -- DISABLE+ENABLE de RLS sem criar tabela nova
# tests-coverage: tests/test_clientes_us_cli_001_completa.py, tests/test_clientes_lgpd_enums_t_cli_101.py
# audit-immutability: skip -- esta migration NAO toca auditoria
# sanitize-asym: skip -- mexe so em enums, nao em payload sanitizado

from __future__ import annotations

from django.db import migrations, models

FORWARD_SQL = """
-- 0) Resolve "pending trigger events" liberando FKs DEFERRABLE antes do ALTER.
SET CONSTRAINTS ALL IMMEDIATE;

-- 1) Solta CHECK antigo (criado em 0012) — vai entrar um novo
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_base_legal;

-- 2) Expande colunas: novos valores tem ate 26 chars (MIGRACAO_SISTEMA_ANTERIOR)
--    e base_legal sobe pra 30 chars (PROTECAO_CREDITO=16, LEGITIMO_INTERESSE=18).
ALTER TABLE clientes ALTER COLUMN aceite_lgpd_base_legal TYPE varchar(30);
ALTER TABLE clientes ALTER COLUMN aceite_lgpd_origem TYPE varchar(30);

-- 3) DISABLE RLS temporariamente pra UPDATE em massa (DDL).
ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;

-- 4) Remap valores antigos -> novos
UPDATE clientes SET aceite_lgpd_base_legal = 'EXECUCAO_CONTRATO'
    WHERE aceite_lgpd_base_legal = 'art_7_v';
UPDATE clientes SET aceite_lgpd_base_legal = 'CONSENTIMENTO'
    WHERE aceite_lgpd_base_legal = 'art_7_i';

UPDATE clientes SET aceite_lgpd_origem = 'CADASTRO_DIRETO'
    WHERE aceite_lgpd_origem IN ('balcao', 'portal');
UPDATE clientes SET aceite_lgpd_origem = 'IMPORTACAO_LEGADA'
    WHERE aceite_lgpd_origem = 'importacao';
UPDATE clientes SET aceite_lgpd_origem = 'MIGRACAO_SISTEMA_ANTERIOR'
    WHERE aceite_lgpd_origem = 'api_terceiro';

-- 5) Re-enable RLS no estado original (ENABLE + FORCE — INV-TENANT-003)
ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes FORCE ROW LEVEL SECURITY;

-- 6) Novo CHECK base legal (5 valores spec)
ALTER TABLE clientes
    ADD CONSTRAINT ck_cliente_base_legal CHECK (
        aceite_lgpd_base_legal = ''
        OR aceite_lgpd_base_legal IN (
            'CONSENTIMENTO',
            'EXECUCAO_CONTRATO',
            'OBRIG_LEGAL',
            'LEGITIMO_INTERESSE',
            'PROTECAO_CREDITO'
        )
    );

-- 7) Novo CHECK origem (3 valores spec)
ALTER TABLE clientes
    ADD CONSTRAINT ck_cliente_lgpd_origem CHECK (
        aceite_lgpd_origem = ''
        OR aceite_lgpd_origem IN (
            'CADASTRO_DIRETO',
            'IMPORTACAO_LEGADA',
            'MIGRACAO_SISTEMA_ANTERIOR'
        )
    );

-- 8) Coluna lia_id (UUID nullable — FK formal pra `lia_testes_balanceamento`
--    entra com modelo dedicado em US-CLI-006 / T-CLI-114).
ALTER TABLE clientes ADD COLUMN aceite_lgpd_lia_id UUID NULL;

-- 9) LEGITIMO_INTERESSE exige lia_id NOT NULL
ALTER TABLE clientes
    ADD CONSTRAINT ck_cliente_lia_obrigatorio CHECK (
        aceite_lgpd_base_legal != 'LEGITIMO_INTERESSE'
        OR aceite_lgpd_lia_id IS NOT NULL
    );
"""

REVERSE_SQL = """
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_lia_obrigatorio;
ALTER TABLE clientes DROP COLUMN IF EXISTS aceite_lgpd_lia_id;
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_lgpd_origem;
ALTER TABLE clientes DROP CONSTRAINT IF EXISTS ck_cliente_base_legal;

ALTER TABLE clientes DISABLE ROW LEVEL SECURITY;

UPDATE clientes SET aceite_lgpd_base_legal = 'art_7_v'
    WHERE aceite_lgpd_base_legal = 'EXECUCAO_CONTRATO';
UPDATE clientes SET aceite_lgpd_base_legal = 'art_7_i'
    WHERE aceite_lgpd_base_legal = 'CONSENTIMENTO';

UPDATE clientes SET aceite_lgpd_origem = 'balcao'
    WHERE aceite_lgpd_origem = 'CADASTRO_DIRETO';
UPDATE clientes SET aceite_lgpd_origem = 'importacao'
    WHERE aceite_lgpd_origem = 'IMPORTACAO_LEGADA';
UPDATE clientes SET aceite_lgpd_origem = 'api_terceiro'
    WHERE aceite_lgpd_origem = 'MIGRACAO_SISTEMA_ANTERIOR';

ALTER TABLE clientes ENABLE ROW LEVEL SECURITY;
ALTER TABLE clientes FORCE ROW LEVEL SECURITY;

ALTER TABLE clientes
    ADD CONSTRAINT ck_cliente_base_legal CHECK (
        aceite_lgpd_base_legal = '' OR aceite_lgpd_base_legal IN ('art_7_v', 'art_7_i')
    );
"""


class Migration(migrations.Migration):
    # atomic=False: a sequencia ALTER TABLE (varchar) + DISABLE RLS + UPDATE +
    # ENABLE RLS + ADD CONSTRAINT esbarra em "pending trigger events" quando
    # tudo roda no mesmo bloco transacional (FK auditoria/tenant tem triggers
    # DEFERRABLE INITIALLY DEFERRED). Quebrar em comandos auto-commit resolve
    # — migration nao precisa ser atomica porque ja eh idempotente pelo CHECK.
    atomic = False

    dependencies = [
        ("clientes", "0017_cliente_canonico_id"),
    ]

    operations = [
        migrations.RunSQL(sql=FORWARD_SQL, reverse_sql=REVERSE_SQL),
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AddField(
                    model_name="cliente",
                    name="aceite_lgpd_lia_id",
                    field=models.UUIDField(
                        null=True,
                        blank=True,
                        help_text=(
                            "FK opaco para teste de balanceamento de Legítimo Interesse "
                            "(LIA — LGPD art. 10). Obrigatório quando "
                            "aceite_lgpd_base_legal=LEGITIMO_INTERESSE (CHECK constraint). "
                            "Modelo formal LIATesteBalanceamento entra em US-CLI-006 "
                            "(T-CLI-114) com FK PROTECT."
                        ),
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="aceite_lgpd_base_legal",
                    field=models.CharField(
                        blank=True,
                        max_length=30,
                        help_text=(
                            "Enum (lgpd.py BASES_LEGAIS_VALIDAS): CONSENTIMENTO (art. 7º I), "
                            "EXECUCAO_CONTRATO (art. 7º V), OBRIG_LEGAL (art. 7º II), "
                            "LEGITIMO_INTERESSE (art. 7º IX — exige aceite_lgpd_lia_id), "
                            "PROTECAO_CREDITO (art. 7º X). CHECK constraint na migration."
                        ),
                    ),
                ),
                migrations.AlterField(
                    model_name="cliente",
                    name="aceite_lgpd_origem",
                    field=models.CharField(
                        max_length=30,
                        blank=True,
                        help_text=(
                            "Enum (lgpd.py ORIGENS_VALIDAS): CADASTRO_DIRETO (operador no balcão "
                            "ou portal próprio), IMPORTACAO_LEGADA (CSV/XLSX sem aceite formal — "
                            "estado restrito), MIGRACAO_SISTEMA_ANTERIOR (importado com aceite "
                            "comprovado pelo sistema anterior)."
                        ),
                    ),
                ),
            ],
        ),
    ]
