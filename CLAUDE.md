# CLAUDE.md — Aferê

> Thin wrapper para Claude Code. Fonte de verdade: [`AGENTS.md`](./AGENTS.md) (padrão aberto multi-tool).
> Em `.codex/` há espelho equivalente para Codex CLI.

## Leitura obrigatória ao iniciar sessão

1. [`AGENTS.md`](./AGENTS.md) — contexto canônico do projeto (produto, princípios, agentes, estrutura, regras duras).
2. [`PRD.md`](./PRD.md) — requisitos do produto (v1.8).
3. [`harness/README.md`](./harness/README.md) — índice dos 17 arquivos de design operacional; ler os relevantes para a task.
4. [`harness/STATUS.md`](./harness/STATUS.md) — status de aprovação de cada decisão P0/P1/P2.

## Leitura por papel (antes de agir em área sensível)

- Agente toca `apps/api/src/domain/emission/**` ou `audit/**` → ler `harness/04-compliance-pipeline.md` + `harness/05-guardrails.md` + `compliance/guardrails.md`.
- Agente toca `packages/normative-rules/**` → ler `harness/04-compliance-pipeline.md` Parte A + `compliance/normative-packages/README.md`.
- Agente toca `packages/engine-uncertainty/**` → ler PRD §7.8 + `harness/14-verification-cascade.md`.
- Agente toca copy (`apps/web/**`, `apps/portal/**`, e-mails, README, PRD) → ler `harness/06-copy-lint.md` + `compliance/approved-claims.md`.
- Agente toca `compliance/**` → exige ADR em `adr/` + aprovação de `product-governance`.

## Subagentes

Definições em [`.claude/agents/`](./.claude/agents/). Allowlist dura — invocar apenas:

`backend-api`, `regulator`, `metrology-calc`, `web-ui`, `android`, `db-schema`, `qa-acceptance`, `lgpd-security`, `copy-compliance`, `product-governance`, `metrology-auditor`, `legal-counsel`, `senior-reviewer`.

Auditores (`metrology-auditor`, `legal-counsel`, `senior-reviewer`) **nunca** editam o artefato que auditam. Emitem parecer em `compliance/audits/<area>/<slug>.md`; executor corrige e resubmete.

## Hooks e gates

Configurados em [`.claude/settings.json`](./.claude/settings.json):

- `SessionStart` — valida leitura deste arquivo + specs sincronizadas.
- `PreToolUse` — bloqueia `git push --force`, `rm -rf`, edição cross-ownership, budget tokens/custo excedido.
- `PostToolUse` — dispara quality gates do pacote tocado (lint, type, test).
- `PreCommit` (git hook) — `copy-lint`, `tenant-safe-sql`, `audit-hash-chain` no delta.

Gates duros em git hooks + CI rodam independentes da ferramenta de IA usada. Ver `harness/05-guardrails.md` (7 gates) e `harness/06-copy-lint.md`.

## Regras duras (repetidas de AGENTS.md — fail-closed)

- Nunca `git push --force` em branches protegidas.
- Nunca `--no-verify` em commits.
- `compliance/**` e `PRD.md` só mudam com PR + ADR.
- Regra de emissão só existe em `apps/api/src/domain/emission/**`. Web/Android/Portal consomem via `packages/contracts`, nunca via `packages/normative-rules` direto.
- Verificar antes de afirmar: rodar o comando de verificação antes de dizer "pronto"/"implementado".

## Roteamento entre ferramentas

| Tarefa | Preferência |
|--------|-------------|
| Raciocínio regulatório profundo, épico novo, release de fatia, Agent Teams | **Claude Code** |
| Refactor mecânico, teste em lote, DevOps, backlog autônomo, cloud exec | **Codex CLI** |
| Code review crítico em área blocker | **Ambos** (dupla checagem) |

## Primeira execução após clone

```bash
# 1. Instala dependências do workspace
pnpm install

# 2. Instala git hooks canônicos (core.hooksPath → .githooks/)
#    Ativa PreCommit para copy-lint + ownership-lint em QUALQUER CLI
bash tools/install-hooks.sh

# 3. Registra MCP servers (só Claude, ou só Codex, ou ambos)
bash tools/install-mcp.sh both      # ver tools/setup-mcp.md para detalhes

# 4. Sobe dev stack (Postgres + Redis) se for trabalhar em apps/api
docker compose up -d postgres redis

# 5. Valida:
pnpm check:all                      # typecheck + agents drift
```

## Como iniciar sessão

```bash
cd "Certificado de calibracao"
claude
```

Claude Code carrega CLAUDE.md → `AGENTS.md` → `.claude/agents/*.md` → `.claude/settings.json`.

## Sanidade contínua

- `pnpm check:drift` — garante que `.claude/agents/*.md` e `.codex/agents/*.toml` estão em sincronia após edições manuais.
- `pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts` — roda copy-lint em toda a cobertura.
- `pnpm --filter @afere/ownership-lint exec node --import tsx src/cli.ts` — roda Gate 6.
- `SKIP_GATES=1 git commit ...` — emergência apenas; justifique na commit message.
