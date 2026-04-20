# Spec 0011 — Frontmatter padrão dos agentes

## Objetivo

Implementar a primeira fatia funcional do P2-1: tornar o frontmatter dos 13 agentes uma interface versionada, validável e sincronizada entre Claude Code e Codex CLI.

## Escopo

- Schema v1 documentado em `harness/03-agentes.md`.
- Frontmatter v1 nos 13 arquivos `.claude/agents/*.md`.
- Gate `tools/agent-frontmatter-check.ts`.
- Testes em `tools/agent-frontmatter-check.test.ts`.
- Integração em `pnpm check:all` e pre-commit.
- Regeneração dos espelhos `.codex/agents/*.toml` a partir dos agentes Claude.

## Critérios de aceite

- Cada agente declara `schema_version: 1`.
- `name` é kebab-case, bate com o nome do arquivo e pertence à lista canônica de 13 agentes.
- `role` é `executor` ou `auditor`.
- Auditores externos declaram `role: auditor`, `model: opus` e não possuem ferramentas de escrita.
- `model` fica restrito a `haiku`, `sonnet` ou `opus`.
- `tools`, `owner_paths`, `blocked_write_paths` e `handoff_targets` são listas não vazias.
- `handoff_targets` referencia apenas agentes canônicos.
- O gate falha fechado quando há agente ausente, agente extra, campo ausente ou alvo de handoff inválido.

## Fora de escopo

- Não substitui `ownership-lint`; o novo gate valida metadados dos agentes, não imports ou paths alterados em PR.
- Não altera o schema suportado pelo Codex CLI; `.codex/agents/*.toml` continua contendo apenas campos aceitos pelo Codex atual.
- Não muda a política de auditores externos além de refletir seus limites no frontmatter.
