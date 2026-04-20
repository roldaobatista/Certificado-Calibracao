# Spec 0015 — Correção de claims proibidos no PRD

## Objetivo

Fechar o finding `FINDING-2026-04-19-001` removendo do `PRD.md` os claims proibidos detectados pelo `copy-lint` sem alterar requisitos técnicos do produto.

## Escopo

- Reescrever os textos comerciais do `PRD.md` §16.7 e §17.1.3 que acionavam CL-001, CL-002 e CL-006.
- Adicionar regressão executável `tools/copy-lint-prd.test.ts`.
- Registrar a decisão em ADR.
- Atualizar o finding em `compliance/validation-dossier/findings/`.
- Atualizar `harness/STATUS.md` e o dashboard gerado.

## Critérios de aceite

- `pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts PRD.md` retorna `errors: 0`.
- `pnpm exec tsx --test tools/copy-lint-prd.test.ts` passa.
- `pnpm test:tools` inclui a regressão do PRD.
- O finding `FINDING-2026-04-19-001` deixa claro que a mitigação foi verificada por comando.

## Fora de escopo

- Não revisar todo o posicionamento comercial do site.
- Não aprovar o claim-set inteiro como definitivo; `compliance/approved-claims.md` continua draft até revisão humana.
- Não alterar requisitos normativos, critérios de aceite ou escopo do MVP.
