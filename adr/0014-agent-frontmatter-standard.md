# ADR 0014 — Frontmatter padrão dos agentes

Status: Aprovado

Data: 2026-04-20

## Contexto

O P2-1 exige nomenclatura e frontmatter padronizados para os agentes. Antes desta decisão, os agentes tinham `name`, `description`, `model` e `tools`, mas ownership, papel e handoffs dependiam do corpo Markdown, dificultando validação automática e drift controlado.

## Decisão

Adotar `schema_version: 1` nos 13 agentes Claude e validar o schema com `tools/agent-frontmatter-check.ts`:

- `name` deve bater com o arquivo e com a lista canônica de agentes;
- `role` explicita separação entre executor e auditor;
- `owner_paths` e `blocked_write_paths` tornam boundaries legíveis por ferramenta;
- `handoff_targets` restringe handoffs a agentes existentes;
- auditores externos ficam obrigatoriamente read-only quanto a ferramentas de edição.

O gate entra em `pnpm check:all` e no pre-commit. O `sync-agents` continua gerando os arquivos Codex apenas com campos suportados pelo Codex CLI, usando `.claude/agents/*.md` como fonte canônica.

## Consequências

Mudanças em agentes passam a falhar fechado se romperem o schema v1. A padronização facilita os próximos P2, especialmente slash-commands regulatórios e dashboard de observabilidade do harness.

## Limitação

Esta decisão valida metadados e coerência nominal. Enforcement de escrita por path continua sendo responsabilidade de `ownership-lint`, CODEOWNERS e demais gates do harness.
