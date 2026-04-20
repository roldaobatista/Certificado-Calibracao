# Spec 0012 — Slash-commands regulatórios

## Objetivo

Implementar a primeira fatia funcional do P2-2: padronizar e validar os slash-commands regulatórios usados para diff normativo, evidência de AC, copy-lint, tenancy fuzz e dry-run de emissão.

## Escopo

- Comandos canônicos em `.claude/commands/`:
  - `/spec-norm-diff`
  - `/ac-evidence`
  - `/claim-check`
  - `/tenant-fuzz`
  - `/emit-cert-dry`
- Frontmatter obrigatório por comando: `description`, `owner`, `risk_level`, `required_commands`.
- Seções obrigatórias: `Objetivo`, `Execução`, `Evidência`, `Escalonamento`, `Referências`.
- Gate `tools/slash-commands-check.ts`.
- Testes em `tools/slash-commands-check.test.ts`.
- Integração em `pnpm check:all` e pre-commit.

## Critérios de aceite

- O gate falha se qualquer comando regulatório estiver ausente.
- O gate falha se frontmatter obrigatório estiver ausente ou inválido.
- O gate falha se `owner` não for agente canônico.
- O gate falha se `risk_level` não for `low`, `medium`, `high` ou `blocker`.
- O gate falha se o comando não tiver bloco executável na seção `Execução`.
- `/emit-cert-dry` mantém fail-closed honesto enquanto o pipeline real de emissão ainda não existir.

## Fora de escopo

- Não implementa o pipeline real de emissão dry-run.
- Não cria suporte de slash-commands específico para Codex CLI; a fonte operacional desta fatia é `.claude/commands/`.
- Não substitui gates já existentes; os comandos apenas tornam execuções manuais padronizadas e auditáveis.
