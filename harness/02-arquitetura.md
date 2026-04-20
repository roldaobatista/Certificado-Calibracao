# 02 — Arquitetura do harness

> **Correção P0-1 aplicada**: `apps/api` agora é peça de primeira classe.

## Tier model (2026)

| Tier | Uso | Ferramentas | % do trabalho |
|------|-----|-------------|---------------|
| **1 — Built-in** | Orquestrador + subagentes dentro de uma sessão Claude Code. Edição, TDD, exploração. | Claude Code CLI, Task tool, Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` na v2.1.32+) | ~90% |
| **2 — Orquestrador externo** | 3–10 agentes em *worktrees* paralelos em sprints com specs prontas. | Conductor, Claude Squad, Vibe Kanban, `EnterWorktree` | ~8% |
| **3 — Cloud agents** | Drain de backlog *low-risk* conforme política (ver `09-cloud-agents-policy.md`). | Claude Code Web, Copilot Coding Agent, Jules | ~2% |

## Estrutura do monorepo

```
afere/
├─ AGENTS.md                    # contexto canônico (espelha CLAUDE.md)
├─ CLAUDE.md                    # instruções globais do harness
├─ .claude/
│  ├─ agents/                   # 10 definições (ver 03-agentes.md)
│  ├─ settings.json             # hooks, permissions, MCP
│  └─ commands/                 # slash-commands regulatórios
├─ specs/                       # spec-driven development
│  ├─ 0001-cliente.md
│  ├─ 0002-equipamento.md
│  └─ ...
├─ adr/                         # decisões arquiteturais
├─ apps/
│  ├─ api/                      # ← P0-1: backend técnico (owner: backend-api)
│  │  ├─ src/domain/            # regras de negócio, emissão, workflows OS
│  │  ├─ src/infra/             # persistência, filas, assinatura, QR
│  │  └─ src/interfaces/        # HTTP/tRPC/GraphQL
│  ├─ web/                      # Next.js back-office (owner: web-ui)
│  ├─ portal/                   # Next.js portal do cliente (owner: web-ui)
│  └─ android/                  # Kotlin offline-first (owner: android)
├─ packages/
│  ├─ engine-uncertainty/       # owner: metrology-calc
│  ├─ normative-rules/          # owner: regulator (library consumida APENAS por apps/api)
│  ├─ db/                       # Prisma + migrations (owner: db-schema)
│  ├─ audit-log/                # owner: db-schema + lgpd-security
│  └─ contracts/                # tRPC/zod schemas compartilhados
├─ evals/
│  ├─ ac/                       # 1 teste por AC do PRD §13
│  ├─ regulatory/               # cenários §9 (bloqueios)
│  ├─ tenancy/                  # RLS + anti-vazamento
│  ├─ sync-simulator/           # ver 08-sync-simulator.md
│  └─ snapshots/                # PDFs/A de referência
├─ compliance/                  # ← P0-3/P0-4/P0-5/P0-6
│  ├─ normative-packages/
│  ├─ validation-dossier/
│  ├─ release-norm/
│  ├─ legal-opinions/
│  ├─ approved-claims.md
│  ├─ cloud-agents-policy.md
│  └─ guardrails.md
└─ infra/                       # Terraform, pipelines
```

## Regra dura de ownership

- **Regra de emissão** só existe em `apps/api/src/domain/emission/**`.
- `apps/web`, `apps/portal`, `apps/android` consomem via `packages/contracts` — nunca duplicam regra.
- `packages/normative-rules` é **library**. Só é carregada pelo `apps/api`. Web/Android não importam.
- Violação dessa regra é detectada por lint customizado (ver `05-guardrails.md`).

## MCP servers ativos

| Server | Finalidade |
|--------|-----------|
| `context-mode` | Gestão de context window (batch execute, search, execute) |
| `github` | PRs, issues, CODEOWNERS |
| `postgres` | Schema introspection, policy RLS |
| `context7` | Docs de Next.js, Prisma, Kotlin, libs metrológicas |
| `playwright` | E2E de web e portal |
| `vitest` | Execução e cobertura de testes |

## Hooks em `.claude/settings.json`

- **SessionStart** → valida que `CLAUDE.md` foi lido e specs estão sincronizadas.
- **PreToolUse** → bloqueia `git push --force`, `rm -rf`, edição cross-ownership.
- **PostToolUse** → roda quality gates afetados (lint, type, test do pacote tocado).
- **PreCommit** → roda `copy-lint`, `tenant-safe-sql`, `audit-hash-chain` no delta.
