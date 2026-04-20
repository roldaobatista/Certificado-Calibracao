# 17 — Operação dual: Claude Code + Codex CLI

> **P0-13**: projeto opera com as duas ferramentas sem dependência mútua. Usuário escolhe (ou o sistema escolhe) qual rodar conforme a tarefa.

## Por que usar as duas

Não é redundância — cada uma é melhor em algo:

| Dimensão | Claude Code | Codex CLI |
|----------|-------------|-----------|
| Qualidade de código em tarefas complexas | **67% win rate** em testes cegos; 80.9% SWE-bench Verified | 77.3% Terminal-Bench; 58.4% Spark (trade-off velocidade) |
| Velocidade e custo | Referência | **2–3× mais eficiente em tokens** |
| Multi-agente coordenado | **Agent Teams** (único hoje) | Single-agent com task queuing |
| Sandbox | Aplicacional (hooks ricos) | **Kernel** (Seatbelt/Landlock/seccomp) — mais forte |
| Cloud exec | Não nativo | `codex cloud exec` (async longa duração) |
| Reasoning profundo / contexto 1M | **Opus 4.7, produção** | GPT-5.4 1M experimental |
| Governança programável | **17 hook events** | Hooks mais simples |
| Padrão aberto de config | CLAUDE.md (proprietário) | **AGENTS.md (Linux Foundation, 60k+ projetos)** |

**Conclusão prática**: Claude Code orquestra raciocínio regulatório e governance; Codex drena backlog autônomo e roda sandbox forte. Os dois leem o mesmo `AGENTS.md`.

## Arquitetura de configuração

```
AGENTS.md                    ← FONTE DE VERDADE (universal)
├─ .claude/
│  ├─ CLAUDE.md              ← thin wrapper; @import ../AGENTS.md + ajustes Claude
│  ├─ agents/                ← 13 agentes em formato Claude (frontmatter YAML)
│  │  ├─ backend-api.md
│  │  ├─ regulator.md
│  │  ├─ metrology-auditor.md
│  │  └─ ... (13)
│  ├─ settings.json          ← hooks, permissions, MCP servers
│  └─ commands/              ← slash-commands
└─ .codex/
   ├─ config.toml            ← configuração principal + MCP servers
   ├─ agents/                ← 13 agentes em formato Codex (TOML)
   │  ├─ backend-api.toml
   │  ├─ regulator.toml
   │  └─ ... (13)
   └─ hooks/                 ← scripts de hook
```

**Regra dura**: `AGENTS.md` na raiz muda primeiro. `.claude/` e `.codex/` são gerados a partir dele por script de sincronização. Não editar `.claude/agents/*.md` ou `.codex/agents/*.toml` manualmente — editar AGENTS.md + spec do agente, re-sincronizar.

## Sincronização automática

Script `tools/sync-agents.ts` (a ser implementado como parte do bootstrap):
- Lê a matriz de agentes em `harness/03-agentes.md` + definições em `harness/16-*.md`.
- Gera `.claude/agents/<nome>.md` com frontmatter Claude.
- Gera `.codex/agents/<nome>.toml` com frontmatter Codex (`name`, `model`, `model_reasoning_effort`, `sandbox_mode`, `mcp_servers`).
- Compara diff; se humano editou manualmente, falha com aviso.
- Rodado em CI e em hook `PreCommit`.

## MCP servers compartilhados

Mesmos MCP servers registrados em ambas as ferramentas:
- `context-mode` — gestão de context window.
- `github` — PRs, issues.
- `postgres` — schema introspection, RLS.
- `context7` — docs de Next.js, Prisma, Kotlin.
- `playwright` — E2E.
- `vitest` — testes e cobertura.

Codex pode também atuar como MCP server para Claude Code (há documentação oficial — `codex-mcp`). Isso habilita um padrão avançado: Claude Code orquestra, Codex executa task sandbox/paralela via tool call.

## Regra de roteamento por tarefa

Quando uma tarefa entra no harness, o orquestrador (ou o agente humano se for sessão manual) escolhe:

| Tipo | Ferramenta |
|------|------------|
| Escrever/revisar spec (L1) | Claude Code (raciocínio) |
| Plano de fatia vertical (L2) | Claude Code |
| Implementar feature em `apps/api` ou `packages/engine-uncertainty` | Claude Code (Agent Teams cross-cutting) |
| Implementar componente de UI isolado em `apps/web/ui/components` | **Codex CLI** (autônomo + cheap) |
| Refactor mecânico em massa (renomear, mover, reformatar) | **Codex CLI** |
| DevOps, scripts de infra, migrations | **Codex CLI** (sandbox kernel) |
| Gerar fixtures sintéticas | **Codex CLI** |
| Rodar `codex cloud exec` para backlog overnight | **Codex CLI** |
| Pré-auditoria (metrology-auditor, legal-counsel) | Claude Code (Opus) |
| Code review crítico (senior-reviewer) | **Ambos em paralelo** = dupla checagem natural |
| Release-norm (product-governance) | Claude Code |

Se o usuário abre a ferramenta "errada" para uma tarefa, o sistema sinaliza mas não bloqueia — ele pode insistir. A regra é recomendação, não gate.

## Divisão equivalente Tier 1 / Tier 2 / Tier 3

A pilha de 3 tiers (ver `02-arquitetura.md`) ganha variantes por ferramenta:

| Tier | Claude Code | Codex CLI |
|------|-------------|-----------|
| 1 — built-in | Subagentes via Task tool + Agent Teams | Subagents (`agents.max_depth=1`) via config |
| 2 — worktrees externos | Conductor, Claude Squad, Vibe Kanban | `codex exec` em múltiplos diretórios |
| 3 — cloud | Claude Code Web | **`codex cloud exec`** — nativo, preferido |

Política de Tier 3 (`09-cloud-agents-policy.md`) vale para ambos: allowlist, blocklist, provenance attestation, sanitização de fixtures.

## Equivalência de hooks

| Evento | Claude Code | Codex CLI |
|--------|-------------|-----------|
| SessionStart | `.claude/settings.json` hooks | `.codex/hooks/session_start.sh` |
| PreToolUse | `.claude/settings.json` hooks | Via sandbox (Seatbelt/Landlock) + hook script |
| PostToolUse | `.claude/settings.json` hooks | `.codex/hooks/post_tool.sh` |
| PreCommit | Hook git + Claude settings | Hook git + Codex config |

Os gates duros (§05, §06) são implementados como **git hooks** (pre-commit, pre-push) + **CI jobs** — roda independente da ferramenta de IA usada. Isso garante que a conformidade não depende de qual CLI o usuário abriu.

## Auditoria e observabilidade

- Cada sessão (Claude ou Codex) grava em `compliance/sessions-log/<YYYY-MM-DD>/<tool>-<session-id>.jsonl`.
- Métricas de budget (§11) são agregadas por ferramenta.
- Relatório semanal comparativo: qual ferramenta usou o quê, quanto custou, quantos PRs gerou, qual taxa de aceitação.

## Limitações honestas

- **Agent Teams** (coordenação P2P entre agentes) é só Claude Code hoje. Tarefas cross-cutting que exigem comunicação entre agentes ficam com Claude Code.
- **Sandbox kernel** é só Codex. Tarefas com código não-confiável (fixtures externas, scripts de terceiros, PoCs de vulnerabilidade) ficam com Codex.
- **Cloud exec async** é só Codex nativo. Claude Code Web existe mas tem perfil diferente.
- **Hooks programáveis profundos** (ex.: budget tracker custom complexo) são mais ricos em Claude Code.
- **Rate limiting**: queixa #1 sobre Claude Code. Em rate limit, fallback automático para Codex em tarefas compatíveis.

## Fallback automático

Configuração de fallback em `tools/tool-router.ts`:
1. Se Claude Code está rate-limited e tarefa é compatível → **retry em Codex**.
2. Se Codex falha por sandbox em tarefa que precisa de tool de rede não permitido → **retry em Claude Code**.
3. Se ambos falham no mesmo gate → **escalação ao usuário** (bloqueio real).

## Sessões paralelas

Usuário pode ter Claude Code e Codex CLI abertos simultaneamente no mesmo repo, em branches ou worktrees diferentes. Git resolve conflito. Ambas ferramentas respeitam CODEOWNERS e gates — se uma tenta mergear sem aprovação do `product-governance`, falha.

## Bootstrap de dual-tooling

Sequência de criação:
1. `AGENTS.md` na raiz — **pronto** (este PR).
2. `tools/sync-agents.ts` script.
3. `.claude/agents/*.md` gerados a partir do harness.
4. `.codex/agents/*.toml` gerados a partir do harness.
5. `.claude/settings.json` + `.codex/config.toml` com MCPs idênticos.
6. `.codex/hooks/` e Claude hooks com os gates de `05-guardrails.md` + `06-copy-lint.md`.
7. CI verifica que `.claude/` e `.codex/` estão sincronizados com AGENTS.md (drift detection).

## Como o usuário (não-técnico) opera na prática

### Opção A — uma ferramenta só (simples)
Abrir **Claude Code** por padrão. Ele é o orquestrador principal. Para tarefas que se beneficiam do Codex, o próprio Claude Code pode invocar Codex como MCP tool (`codex-mcp`).

### Opção B — alternância manual
- Abrir **Claude Code** quando for: novo módulo, nova spec, release, decisão arquitetural.
- Abrir **Codex CLI** quando for: "tenho 50 arquivos para renomear", "rodar testes a noite inteira", "gerar 200 fixtures", "arrumar formatação".

### Opção C — paralelo
Uma janela de cada. Claude Code em `main`, Codex em worktree/branch separada. Git faz a costura.

**Em nenhuma das opções você precisa lembrar qual ferramenta faz o quê na hora.** O `AGENTS.md` + guardrails garantem que qualquer caminho chega ao mesmo padrão de qualidade e conformidade.

## Revisão da estratégia

A cada fim de fatia vertical (V1–V5), relatório comparativo em `compliance/dual-tooling-review/<fatia>.md`:
- Tempo por tipo de tarefa em cada ferramenta.
- Custo por tipo.
- Bugs detectados por cada uma.
- Ajuste da tabela de roteamento se dados mostrarem padrão inesperado.

## Fontes

- [OpenAI — AGENTS.md guide](https://developers.openai.com/codex/guides/agents-md)
- [OpenAI — Codex Subagents](https://developers.openai.com/codex/subagents)
- [OpenAI — Codex MCP](https://developers.openai.com/codex/mcp)
- [OpenAI — Advanced Config](https://developers.openai.com/codex/config-advanced)
- [Anthropic — Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Blake Crosley — Codex vs Claude Code: Architecture Deep Dive 2026](https://blakecrosley.com/blog/codex-vs-claude-code-2026)
- [NxCode — Claude Code vs Codex CLI 2026](https://www.nxcode.io/resources/news/claude-code-vs-codex-cli-terminal-coding-comparison-2026)
