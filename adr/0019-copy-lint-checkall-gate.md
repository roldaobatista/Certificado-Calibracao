# ADR 0019 — Copy-lint no check:all

Status: Aprovado

Data: 2026-04-20

## Contexto

P0-5 exige que claims regulatórios proibidos sejam bloqueados por hook e CI. O pre-commit já executava o `copy-lint` no delta, e o PRD passou a ter regressão específica, mas o `check:all` ainda não executava o scan padrão de todo o repositório.

Isso deixava uma diferença prática entre validação local ampla e o gate principal usado em PRs.

## Decisão

Adicionar o script raiz `copy-lint:check`:

```bash
pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts
```

e incluí-lo em `pnpm check:all` logo após `pnpm test:tools`.

Adicionar `tools/copy-lint-pipeline.test.ts` para garantir que o script e sua presença em `check:all` não sejam removidos sem quebrar testes.

## Consequências

O required-gates passa a varrer toda a cobertura padrão do `copy-lint` em cada execução de `check:all`, não apenas os arquivos staged do pre-commit.

## Limitação

O gate garante ausência de padrões proibidos conhecidos. Ele não substitui revisão jurídica humana para novos claims nem transforma `compliance/approved-claims.md` em lista final aprovada.
