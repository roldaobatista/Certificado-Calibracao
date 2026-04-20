# ADR 0011 — Gate do roadmap vertical V1-V5

Status: Aprovado

Data: 2026-04-20

## Contexto

O P1-4 substitui o roadmap otimista por fatias verticais auditáveis. Sem artefato executável, V1 poderia começar sem gate anterior, sem dossiê alvo ou sem release-norm previsto.

## Decisão

Criar `compliance/roadmap/v1-v5.yaml` como fonte operacional do roadmap e `tools/roadmap-check.ts` como gate estrutural.

O gate exige:

- ordem estrita V1-V5;
- dependência sequencial;
- política de gate anterior obrigatório;
- release-norm por fatia;
- dossiê por fatia;
- pacote normativo obrigatório;
- escopo, agentes primários e gates de saída por fatia.

`pnpm roadmap-check` entra em `pnpm check:all` e no pre-commit quando arquivos P1-4 mudam.

## Consequências

Nenhuma fatia V1 pode iniciar sem que o roadmap canônico esteja versionado e verde. Cada fatia ainda precisará de spec própria e dossiê de validação antes de release.
