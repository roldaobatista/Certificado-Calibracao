# tools/setup-mcp.md — Registrando MCP servers nas CLIs

> Requer: **Claude Code** e/ou **Codex CLI** já instalados e autenticados.
>
> MCP servers são registrados na ferramenta (Claude / Codex), não no repo. Rode os comandos abaixo **uma vez por máquina**.

## MCP servers canônicos do Aferê

Declarados em `AGENTS.md` §2.2 e `harness/02-arquitetura.md`:

| Server | Finalidade | Requer autenticação externa? |
|--------|-----------|------------------------------|
| `context-mode` | Gestão de context window | não (plugin local) |
| `github` | PRs, issues, CODEOWNERS | sim — token GitHub |
| `postgres` | Schema introspection + RLS | sim — `POSTGRES_URL` |
| `context7` | Docs Next.js, Prisma, Kotlin | não |
| `playwright` | E2E web/portal | não |
| `vitest` | Execução e cobertura de testes | não |

## Claude Code

### Claude-como-plugin marketplace (recomendado para os oficiais)

```bash
# context-mode (gestão de contexto)
claude mcp add context-mode

# github
claude mcp add github
# vai pedir seu personal access token

# context7 (docs de libs)
claude mcp add context7

# playwright
claude mcp add playwright

# vitest
claude mcp add vitest
```

### Postgres (requer URL local de dev)

```bash
claude mcp add postgres \
  -e POSTGRES_URL="postgresql://afere:afere@localhost:5433/afere?schema=public"
```

Essa URL bate com o `docker-compose.yml` desta branch. Se for apontar para outro DB, ajuste.

### Listar e testar

```bash
claude mcp list
claude /mcp           # abre o picker interativo dentro de uma sessão
```

## Codex CLI

### Comandos equivalentes

```bash
# context-mode
codex mcp add context-mode

# github
codex mcp add github

# postgres
codex mcp add postgres --env POSTGRES_URL="postgresql://afere:afere@localhost:5433/afere?schema=public"

# context7
codex mcp add context7

# playwright
codex mcp add playwright

# vitest
codex mcp add vitest
```

### Verificação

```bash
codex mcp list
```

### Codex como MCP para Claude Code (avançado)

Conforme `harness/17-multi-tooling.md`, o Codex pode atuar **como** MCP server para o Claude Code, habilitando um padrão de orquestração onde Claude raciocina e Codex executa sandbox/paralelo.

Se quiser esse modo:

```bash
claude mcp add codex-mcp -- codex mcp-serve
```

Isso não é necessário para o uso básico.

## Tudo-de-uma-vez (opcional)

Script `tools/install-mcp.sh` roda todos os comandos de uma só vez. Edite o bloco `POSTGRES_URL` se seu dev postgres estiver em outro endpoint.

```bash
bash tools/install-mcp.sh claude   # só Claude
bash tools/install-mcp.sh codex    # só Codex
bash tools/install-mcp.sh both     # ambos
```

## Solução de problemas

- **`command not found: claude` ou `codex`** — instale a CLI antes (`npm i -g @anthropic-ai/claude-code` ou `npm i -g @openai/codex`).
- **`MCP server failed to connect`** — execute o servidor standalone primeiro para ver o erro (`npx @modelcontextprotocol/server-postgres`).
- **postgres: `connection refused`** — seu `docker compose up -d postgres` não está rodando.
- **github: `Bad credentials`** — gere novo PAT em github.com/settings/tokens (scope mínimo: `repo`, `read:org`).

## Referências

- `.claude/settings.json` — declaração dos MCP servers.
- `.codex/config.toml` — declaração equivalente.
- `harness/17-multi-tooling.md` — estratégia dual.
- `AGENTS.md` §2.2 — lista canônica.
