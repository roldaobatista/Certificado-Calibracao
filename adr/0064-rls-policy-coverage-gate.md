# ADR 0064 — Gate de cobertura RLS para migrations multitenant

## Status

Aceito

## Contexto

O Aferê já possuía `tenant-lint`, testes RLS smoke/fuzz e policies nas primeiras migrations. Mesmo assim, a análise de 2026-04-24 mostrou que algumas tabelas criadas depois da V3 com `organization_id` não tinham `ENABLE ROW LEVEL SECURITY` nem policy de isolamento no SQL versionado.

Esse tipo de lacuna é perigoso porque o dossiê pode continuar verde por validar o mecanismo em cenários sintéticos, sem provar que todas as tabelas reais do schema receberam a proteção.

## Decisão

Adicionar uma camada explícita de verificação estrutural:

1. Criar `tools/rls-policy-check.ts` para varrer todas as migrations de Prisma.
2. Marcar como blocker qualquer `CREATE TABLE` com coluna `organization_id` sem RLS habilitado em alguma migration versionada.
3. Marcar como blocker qualquer tabela multitenant sem `CREATE POLICY` que use `organization_id` e `app.current_organization_id`.
4. Corrigir as tabelas V4/V5/post-V5 que escaparam por meio da migration `202604230050_rls_for_late_multitenant_tables`.
5. Colocar `tenant-lint`, `test:tenancy` e `rls-policy-check` dentro de `pnpm check:all` para que a verificação de tenancy deixe de ser opcional.
6. Acionar o gate no pre-commit quando migrations ou o próprio checker mudarem.

## Consequências

### Positivas

- O histórico SQL passa a provar cobertura RLS para todas as tabelas multitenant conhecidas.
- Novas migrations com `organization_id` sem policy bloqueiam antes de commit.
- `check:all` passa a representar melhor os hard gates de tenancy descritos no harness.

### Limitações honestas

- O gate verifica estrutura de migrations, não substitui testes reais contra banco com papéis de aplicação.
- O gate não introduz `FORCE ROW LEVEL SECURITY`; essa decisão deve ser tratada em spec própria quando o papel de conexão de produção estiver definido.
- A proteção efetiva em produção ainda depende de conexão sem privilégio de bypass e de configurar corretamente `app.current_organization_id` por transação/sessão.
