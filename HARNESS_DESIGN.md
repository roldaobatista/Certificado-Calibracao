# Harness de Desenvolvimento — Plataforma Kalibrium

> **Objetivo:** montar um ambiente multi-agente de alto nível para desenvolver o produto descrito no PRD v1.8 do zero, com orquestrador + agentes especializados, spec-driven development e *guardrails* compatíveis com um domínio regulado (ISO/IEC 17025, Inmetro/Cgcre).
>
> **Base:** pesquisa em fóruns, blogs e documentação oficial (abril/2026). Fontes no final.
> **Pré-requisitos declarados pelo produto:** Next.js (web) + Android (Kotlin) + PostgreSQL, offline-first, multitenant, assinatura eletrônica, PDF/A, DCC-ready.

---

## 1. Princípios do harness (não-negociáveis)

1. **Conformidade por arquitetura também no harness.** Assim como o produto bloqueia emissão fora da norma (PRD §9), o harness bloqueia *commits* que violem regras automatizáveis: lint, types, testes de AC, schema drift, políticas LGPD/segurança.
2. **Spec-as-source, não spec-first descartável.** Cada módulo (§7.x do PRD) vira um *spec file* versionado com os 6 elementos do SDD (outcomes, scope, constraints, prior decisions, task breakdown, verification). Agentes leem a spec antes de editar código. — *Augment Code, Martin Fowler SDD*
3. **Estado fora do processo.** Sessões de agente são efêmeras; a verdade vive em Git + Postgres + artefatos versionados (specs, ADRs, eval reports). — *Claude Agent SDK production patterns*
4. **Budgets são feature de produto.** Caps de custo por task, por usuário, por tenant — no harness, não no billing. Circuit breakers em loops e tool errors.
5. **Context rot é inimigo.** `/compact` manual aos 50%, `/clear` entre tasks, *rewind > correct*, e subagentes para isolar explorações. Não deixar a sessão passar de ~300–400k tokens em trabalhos sensíveis.
6. **Evaluation harness > "parece bom".** Cada AC do PRD §13 vira um teste executável. *Done* = AC verde, não opinião.

---

## 2. Arquitetura do harness

### 2.1 Três camadas (tier model 2026)

| Camada | Uso | Ferramentas |
|--------|-----|-------------|
| **Tier 1 — Built-in** (90% do trabalho) | Orquestrador + subagentes dentro de uma sessão Claude Code. Exploração, edição, TDD rápido. | Claude Code CLI, Task tool, Agent Teams (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`) |
| **Tier 2 — Orquestrador externo** | 3–10 agentes em *worktrees* paralelos em sprints conhecidos (ex.: gerar 8 módulos em paralelo após specs aprovadas). | Conductor, Claude Squad, Vibe Kanban, `EnterWorktree` |
| **Tier 3 — Cloud agents** | Drain de *backlog* overnight (bugs Sev-3, refactors mecânicos). | Claude Code Web, Copilot Coding Agent, Jules |

### 2.2 Orquestrador (a "brain")

Claude Code CLI na raiz do monorepo, com:
- `CLAUDE.md` raiz + `CLAUDE.md` por pacote (conforme padrão `AGENTS.md`).
- **Restrição de allowlist** de subagentes: `Agent(regulator, metrology, web-ui, android, db, qa, lgpd-security, docs)` — evita *rogue spawns*.
- **Hooks** em `.claude/settings.json`: `PreToolUse` bloqueia `git push --force` e `rm -rf`; `PostToolUse` roda quality gates; `SessionStart` lê `CLAUDE.md` e valida specs atualizadas.
- **MCP servers**: `context-mode` (context window), `github`, `postgres` (schema introspection), `context7` (docs Next.js/Prisma/Kotlin), `playwright` (E2E), `vitest`.

### 2.3 Subagentes especializados (roles = módulos do PRD)

Cada subagente tem `.claude/agents/<nome>.md` com *description*, *allowed_tools*, *model*, *system_prompt* escopado:

| Agente | Escopo | Specs de referência |
|--------|--------|---------------------|
| **regulator** | Interpretar DOQ-CGCRE, NIT-DICLA, Portaria 157/2022, ILAC P10/G8. Valida regras §9 e §16. | PRD §4, §16 |
| **metrology-calc** | Engine de incerteza (k=2), balanço, regra de decisão ILAC G8, testes com padrões EURAMET. | PRD §7.8 |
| **web-ui** | Next.js SSR/SSG, wizard de revisão, portal do cliente, e-mails transacionais. | PRD §7.2–7.15, §17 |
| **android** | Kotlin, offline-first, SQLCipher, sync eventos idempotente. | PRD §7.7, §11.3 |
| **db-schema** | Postgres, multitenancy, *audit log* imutável, *normative package* por certificado. | PRD §10, §16.1 |
| **qa-acceptance** | Testes E2E de cada AC (§13), fixtures de dados, property tests da engine. | PRD §13 |
| **lgpd-security** | Base jurídica, assinatura eletrônica, retenção, hardening do audit log. | PRD §11.3, §11.4 |
| **docs** | ADRs, changelog, atualização de specs após merge. | Todo o repo |

**Regra:** um agente só escreve em seu escopo. Mudanças cross-cutting passam por Agent Teams com *file locking*.

### 2.4 Estrutura de repositório (monorepo)

```
kalibrium/
├─ AGENTS.md                 # contexto canônico (espelha CLAUDE.md)
├─ CLAUDE.md                 # instruções globais de harness
├─ .claude/
│  ├─ agents/                # definições dos 8 subagentes
│  ├─ settings.json          # hooks, permissions, MCP
│  └─ commands/              # slash-commands (/spec-new, /ac-check, /emit-cert-dry)
├─ specs/                    # spec-driven dev (source-of-truth de cada feature)
│  ├─ 0001-cliente-module.md
│  ├─ 0002-equipamento-module.md
│  └─ ...
├─ adr/                      # decisões arquiteturais
├─ apps/
│  ├─ web/                   # Next.js (owner: web-ui)
│  ├─ android/               # Kotlin (owner: android)
│  └─ portal/                # Next.js, portal do cliente
├─ packages/
│  ├─ engine-uncertainty/    # owner: metrology-calc
│  ├─ normative-rules/       # owner: regulator
│  ├─ db/                    # Prisma + migrations (owner: db-schema)
│  ├─ audit-log/             # owner: db-schema + lgpd-security
│  └─ contracts/             # tRPC/zod schemas compartilhados
├─ evals/                    # harness de avaliação
│  ├─ ac/                    # um teste por AC do §13
│  ├─ regulatory/            # cenários de bloqueio do §9
│  └─ snapshots/             # PDFs de referência (regressão)
└─ infra/                    # Terraform, pipelines
```

---

## 3. Spec-driven flow (ciclo de feature)

1. **`/spec-new <módulo>`** → cria arquivo em `specs/` com template de 6 elementos + âncoras para PRD.
2. **Elicitação** via MCP: se AC ambíguo, agente abre diálogo estruturado antes de codar.
3. **Plan mode** no Claude Code → aprovação humana.
4. **Execução paralela** (Tier 2 quando viável): worktrees por pacote, sem conflito.
5. **Quality gates** (hooks): `pnpm lint && pnpm typecheck && pnpm test --filter <pkg>`.
6. **AC check** (`/ac-check <spec>`): roda suite de aceitação; PR bloqueado se falhar.
7. **Review**: `security-review` e `review` (skills nativos) + *dry-run* de emissão com dataset sintético.
8. **Merge** → agente `docs` atualiza ADR, changelog e marca spec como *implementada*.

---

## 4. Eval harness específico do domínio

- **Regulatory eval**: 40+ cenários do §9 (padrão vencido, signatário sem competência, ambiente fora da faixa, Tipo B tentando símbolo Cgcre…) — devem **todos bloquear**.
- **Metrology eval**: casos EURAMET cg-18 com resultado esperado de incerteza k=2; tolerância numérica documentada.
- **Offline sync eval**: gerar 10k eventos offline, injetar perda de rede, validar idempotência e reconciliação.
- **PDF/A eval**: snapshot de 3 templates por perfil regulatório; diff pixel-a-pixel + validação de QR code.
- **LGPD eval**: DSAR simulado, retenção, logs de acesso a dados pessoais.

---

## 5. Budgets e circuit breakers

| Controle | Valor inicial |
|----------|---------------|
| Tokens por task | 200k (hard cap) |
| Custo/dia/dev | US$ 15 (alerta) / US$ 30 (bloqueio) |
| Loop detection | Tool error 3× consecutivo → abort |
| Context | `/compact` automático aos 50%, `/clear` entre specs |
| Timeout de worktree | 4h → sinaliza humano |

---

## 6. Roadmap de bootstrap (4 semanas)

| Semana | Entrega |
|--------|---------|
| 1 | Monorepo + `CLAUDE.md` + `.claude/agents/*` + hooks + specs das 8 primeiras features |
| 2 | `packages/db` + `engine-uncertainty` + eval regulatory (seed dos 40 cenários) |
| 3 | `apps/web` esqueleto com wizard de revisão + portal de cliente v0 |
| 4 | `apps/android` offline-first stub + sync idempotente + CI completo + Tier 2 ativo |

---

## 7. Framework de orquestração externa (opcional, Fase 2)

Se precisar ir além do Claude Code puro:
- **LangGraph** como *top-level orchestrator* (stateful, checkpointing, LangSmith observability) em tarefas multi-repo/multi-dia — chamado via Agent SDK quando o fluxo ultrapassar a sessão.
- **CrewAI** para *pipelines* pontuais de geração de conteúdo (e-mails transacionais, docs de onboarding).
- **AutoGen/AG2** *não recomendado* para este domínio (custo 5–6×, comportamento estocástico incompatível com regras duras).

> *Framework loyalty não dirige arquitetura* — mistura é aceitável se cada um ficar no que faz melhor.

---

## Fontes

- [Anthropic — Multi-agent coordination patterns](https://claude.com/blog/multi-agent-coordination-patterns)
- [Claude Code Docs — Agent Teams](https://code.claude.com/docs/en/agent-teams)
- [Anthropic — Building agents with the Claude Agent SDK](https://www.anthropic.com/engineering/building-agents-with-the-claude-agent-sdk)
- [Claude Agent SDK: Complete Production Patterns Guide 2026 — Digital Applied](https://www.digitalapplied.com/blog/claude-agent-sdk-production-patterns-guide)
- [Shipyard — Multi-agent orchestration for Claude Code in 2026](https://shipyard.build/blog/claude-code-multi-agent/)
- [Addy Osmani — The Code Agent Orchestra](https://addyosmani.com/blog/code-agent-orchestra/)
- [MindStudio — Agent Teams vs Sub-Agents](https://www.mindstudio.ai/blog/claude-code-agent-teams-vs-sub-agents)
- [InfoQ — Spec-Driven Development at Enterprise Scale](https://www.infoq.com/articles/enterprise-spec-driven-development/)
- [Augment Code — What Is Spec-Driven Development?](https://www.augmentcode.com/guides/what-is-spec-driven-development)
- [Augment Code — 6 Best Spec-Driven Development Tools 2026](https://www.augmentcode.com/tools/best-spec-driven-development-tools)
- [Martin Fowler — Understanding SDD: Kiro, spec-kit, Tessl](https://martinfowler.com/articles/exploring-gen-ai/sdd-3-tools.html)
- [GitHub Blog — Spec Kit](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)
- [Spectro Cloud — Will AI turn 2026 into the year of the monorepo?](https://www.spectrocloud.com/blog/will-ai-turn-2026-into-the-year-of-the-monorepo)
- [ChatPRD — Best Practices for Using PRDs with Claude Code in 2026](https://www.chatprd.ai/learn/PRD-for-Claude-Code)
- [DataCamp — CrewAI vs LangGraph vs AutoGen](https://www.datacamp.com/tutorial/crewai-vs-langgraph-vs-autogen)
- [DEV.to — LangGraph vs CrewAI vs AutoGen (2026 guide)](https://dev.to/pockit_tools/langgraph-vs-crewai-vs-autogen-the-complete-multi-agent-ai-orchestration-guide-for-2026-2d63)
- [Medium — Claude Agents SDK: Best Practices (Robert Mill)](https://bertomill.medium.com/claude-agents-sdk-best-practices-from-the-team-that-built-it-63580d1a0c3b)
