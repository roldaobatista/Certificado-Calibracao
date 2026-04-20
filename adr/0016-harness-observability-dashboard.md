# ADR 0016 — Dashboard de observabilidade do harness

Status: Aprovado

Data: 2026-04-20

## Contexto

P2-3 pedia observabilidade do harness. O status existia em `harness/STATUS.md`, mas faltava uma visão operacional gerada que mostrasse o estado agregado, cobertura do dossiê e gates ativos no pipeline.

## Decisão

Criar `tools/harness-dashboard.ts` com modos `check` e `write`, gerando `compliance/harness-dashboard.md` a partir de:

- `harness/STATUS.md`;
- `compliance/validation-dossier/coverage-report.md`;
- script `check:all` em `package.json`.

O dashboard gerado entra em `pnpm check:all` e no pre-commit para evitar drift.

## Consequências

O repositório passa a ter uma visão resumida e versionada do estado do harness. Qualquer alteração no status, cobertura ou pipeline principal exige regenerar o dashboard.

## Limitação

Esta fatia entrega observabilidade estática em Markdown. Métricas temporais, histórico de duração e painéis externos ficam para uma fatia futura, quando houver execução contínua suficiente para análise.
