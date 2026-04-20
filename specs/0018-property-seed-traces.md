# Spec 0018 — Traces determinísticos por seed de property testing

## Objetivo

Fechar a lacuna de P0-11 em que seeds canônicos de property testing existiam na configuração, mas não geravam evidência versionada por seed.

## Escopo

- Adicionar `trace_path` em cada entrada de `evals/property-config.yaml`.
- Gerar artefatos JSONL determinísticos em `compliance/validation-dossier/evidence/property-traces/`.
- Fazer `tools/redundancy-check.ts` bloquear ausência de `trace_path`, trace ausente ou trace desatualizado.
- Adicionar o script raiz `pnpm redundancy-check:trace`.
- Ampliar `tools/redundancy-check.test.ts` com regressões de trace ausente, stale e script raiz.

## Critérios de aceite

- O teste falha quando `trace_path` não é declarado.
- O teste falha quando o JSONL de trace diverge dos seeds canônicos.
- `pnpm redundancy-check:trace` reescreve os traces determinísticos.
- `pnpm redundancy-check` valida os traces versionados.
- Os artefatos de trace ficam em `compliance/validation-dossier/evidence/property-traces/`.

## Fora de escopo

- Não classifica flakes automaticamente.
- Não executa self-consistency real entre agentes.
- Não altera branch protection ou políticas GitHub.
