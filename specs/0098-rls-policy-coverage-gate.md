# 0098 - Gate de cobertura RLS para tabelas multitenant

## Contexto

A análise geral encontrou uma lacuna entre o princípio de multitenancy fail-closed e o histórico de migrations: tabelas com `organization_id` adicionadas nas fatias V4, V5 e pós-V5 não tinham `ENABLE ROW LEVEL SECURITY` nem policy de isolamento registrada em SQL.

Os testes sintéticos de RLS e o `tenant-lint` continuavam verdes porque validavam cenários de avaliação e queries sem provar que toda tabela nova do schema real recebeu policy no migration trail.

## Objetivo

Garantir que qualquer tabela criada em `packages/db/prisma/migrations/**/migration.sql` com coluna `organization_id` tenha:

1. `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`;
2. `CREATE POLICY ... ON ...` contendo `organization_id`;
3. vínculo explícito com `app.current_organization_id`.

## Escopo

- Adicionar migração corretiva para as tabelas multitenant já criadas sem RLS/policy.
- Criar `tools/rls-policy-check.ts` para inspecionar o conjunto completo de migrations.
- Expor `pnpm rls-policy-check`.
- Incluir `pnpm tenant-lint`, `pnpm test:tenancy` e `pnpm rls-policy-check` no `pnpm check:all`.
- Acionar o novo gate no pre-commit quando migrations, checker ou pipeline mudarem.

## Fora de escopo

- Substituir os testes RLS smoke/fuzz existentes.
- Alterar o modelo Prisma além das migrations.
- Introduzir `FORCE ROW LEVEL SECURITY` em todas as tabelas existentes.
- Criar papéis de banco de produção ou rotação de credenciais.

## Regras

1. Tabela com `organization_id` sem RLS é blocker.
2. Tabela com `organization_id` sem policy tenant-aware é blocker.
3. O gate deve olhar o histórico completo de migrations, não apenas o delta.
4. O `check:all` deve executar os gates de tenancy junto dos demais hard gates.

## Critérios de aceite

- `pnpm exec tsx --test tools/rls-policy-check.test.ts` falha antes do checker/migração e passa após a correção.
- `pnpm rls-policy-check` passa no repositório atual.
- `pnpm check:all` executa `tenant-lint`, `test:tenancy` e `rls-policy-check`.
- As tabelas `certificate_publications`, `nonconformities`, `nonconforming_work_cases`, `internal_audit_cycles`, `management_review_meetings`, `organization_compliance_profiles` e `quality_indicator_snapshots` ficam cobertas por RLS/policy.
