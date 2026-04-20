# Spec 0016 — Copy-lint no check:all

## Objetivo

Fechar uma lacuna de P0-5: o `copy-lint` deve rodar como gate de repositório inteiro em `pnpm check:all`, além do hook de pre-commit no delta.

## Escopo

- Adicionar script raiz `pnpm copy-lint:check`.
- Incluir `pnpm copy-lint:check` em `pnpm check:all`.
- Adicionar teste `tools/copy-lint-pipeline.test.ts` para impedir drift do pipeline.
- Atualizar `harness/STATUS.md` e o dashboard gerado.

## Critérios de aceite

- O teste falha quando `copy-lint:check` não existe ou não está em `check:all`.
- `pnpm copy-lint:check` varre a cobertura padrão de `packages/copy-lint/src/rules.yaml`.
- `pnpm check:all` executa o scan padrão do `copy-lint`.
- O dashboard lista `copy-lint:check` entre os gates.

## Fora de escopo

- Não altera as regras CL-001..CL-008.
- Não aprova o claim-set completo para go-live.
- Não substitui a revisão jurídica humana de novos claims.
