# tools/setup-mcp.md — Registrando MCP servers nas CLIs

> Requer: **Claude Code** e/ou **Codex CLI** já instalados e autenticados.
>
> MCP servers são registrados na ferramenta (Claude / Codex), não no repo.

## MCP servers canônicos do Aferê

| Server | Pacote | Requer credencial? |
|--------|--------|---------------------|
| `context-mode` | plugin Claude Code (marketplace) | não |
| `github` | `@modelcontextprotocol/server-github` | `GITHUB_PERSONAL_ACCESS_TOKEN` |
| `postgres` | `@modelcontextprotocol/server-postgres` | `POSTGRES_URL` |
| `context7` | `@upstash/context7-mcp` | não |
| `playwright` | `@playwright/mcp` | não |
| `vitest` | *sem MCP oficial (2026-04)* | — |

## Atalho

```bash
# Escolha: claude | codex | both
bash tools/install-mcp.sh both

# Com credenciais:
GITHUB_TOKEN=ghp_... bash tools/install-mcp.sh both
```

## Sintaxe manual

### Codex CLI (2026+)

Sintaxe obrigatória: `codex mcp add <NAME> -- <command...>` (o `--` separa o comando que o Codex vai executar).

```bash
# GitHub
codex mcp add github \
  --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_xxx \
  -- npx -y @modelcontextprotocol/server-github

# Postgres
codex mcp add postgres \
  --env POSTGRES_URL="postgresql://afere:afere@localhost:5433/afere?schema=public" \
  -- npx -y @modelcontextprotocol/server-postgres \
     "postgresql://afere:afere@localhost:5433/afere?schema=public"

# Playwright
codex mcp add playwright -- npx -y @playwright/mcp@latest

# Context7 (docs)
codex mcp add context7 -- npx -y @upstash/context7-mcp
```

Verificação: `codex mcp list`. Remoção: `codex mcp remove <NAME>`.

### Claude Code

Aceita forma explícita (como Codex) ou marketplace:

```bash
# Marketplace (interativo)
claude /plugin install context-mode

# Explícito — mesmo comando de Codex, mas via claude:
claude mcp add playwright -- npx -y @playwright/mcp@latest
claude mcp add postgres \
  --env POSTGRES_URL="postgresql://afere:afere@localhost:5433/afere?schema=public" \
  -- npx -y @modelcontextprotocol/server-postgres \
     "postgresql://afere:afere@localhost:5433/afere?schema=public"
```

Verificação: `claude mcp list`.

### Codex como MCP server do Claude (avançado)

Segundo `harness/17-multi-tooling.md`, Codex pode atuar como MCP server do Claude, permitindo Claude orquestrar raciocínio regulatório enquanto Codex executa sandbox/paralelo.

```bash
claude mcp add codex-mcp -- codex mcp-serve
```

Não necessário para uso básico.

## Pacotes sem MCP público (workarounds)

- **vitest** — sem MCP oficial. Use `pnpm test` direto, ou em Codex `codex exec -- pnpm test`.
- **context-mode** — plugin **específico do Claude Code** (marketplace). Codex não tem versão nativa; use o modo "Codex-como-MCP-do-Claude" se quiser contexto compartilhado.

## Problemas comuns

- **`command not found: claude|codex`** — instale: `npm i -g @anthropic-ai/claude-code` ou `npm i -g @openai/codex`.
- **`error: --env with stdio only`** — você passou `--env` mas usou `--url`. `--env` é só para stdio servers (os que usam `--`).
- **Postgres: `connection refused`** — seu `docker compose up -d postgres` não está rodando.
- **GitHub: `Bad credentials`** — gere novo PAT em github.com/settings/tokens (scopes: `repo`, `read:org`).
- **`codex` exige formato `<NAME> -- <cmd>`** — se rodar `codex mcp add github` sem `--`, recebe "required args not provided".

## Referências

- `.claude/settings.json` e `.codex/config.toml` — declaração dos servers.
- `harness/17-multi-tooling.md` — estratégia dual.
- `AGENTS.md` §2.2 — lista canônica.
