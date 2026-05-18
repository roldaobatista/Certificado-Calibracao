# Catálogo dos auditores-agentes

> **Pra quê:** materializar os auditores que substituem reviewers humanos. Auditor 10 v2 alertou: sem operacionalização, "Família 5 é vaporware".
>
> **Status atual (2026-05-17):** 3 auditores originais materializados em v1.0.0 + 1 auditor adicional criado como parte da aplicação do `plano-defesas-anti-erros-ia.md`:
> - `auditor-seguranca-prompt.md` ✅
> - `auditor-qualidade-prompt.md` ✅
> - `auditor-produto-prompt.md` ✅
> - `auditor-drift-docs-prompt.md` ✅ — novo, sem poder de veto (consultivo)
>
> Os 3 originais ainda dependem da stack final pra calibrar thresholds (ex: % de cobertura mínima do Auditor de Qualidade depende de ADR-0001 fechar). O auditor de drift opera independente de stack.

---

## Os 3 auditores

| Auditor | Lê | Trigger | Poder de veto |
|---|---|---|---|
| **Segurança** | `REGRAS-INEGOCIAVEIS.md` (SEC-*, INV-TENANT-*), `docs/seguranca/`, diff do commit | Pre-commit em código que toca `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`, `.claude/hooks/` | **Bloqueia commit** se SEC-* violado |
| **Qualidade** | `REGRAS-INEGOCIAVEIS.md` (TST-*), `tests/`, diff | Pre-commit em qualquer código | **Bloqueia commit** se TST-* violado ou cobertura abaixo do mínimo |
| **Produto** | `docs/dominios/<mod>/prd.md`, `docs/comum/glossario.md`, US em foco | Pre-merge em feature (após implementação completa) | **Bloqueia merge** se AC binário não passa |
| **Drift de docs** | `docs/`, `.claude/`, `.specify/`, raízes canônicas, `MEMORY.md`, `git log` | Manual (`@auditor-drift-docs`) ou semanal | **Nenhum** — só reporta drifts (D1–D8) |

---

## Como cada auditor é "rodado"

> **A definir formalmente:** prompt completo, modelo (Opus/Sonnet/Haiku?), contexto injetado, output format, integração com CI.

### Auditor de Segurança
- **Modelo:** Sonnet (rápido) com Opus em escalation
- **Trigger:** hook `pre-commit` quando diff toca paths listados em `.github/CODEOWNERS` (10 paths)
- **Contexto injetado:** SEC-*, INV-TENANT-*, `mcp-policy.md`, `agente-input-nao-confiavel.md`, diff
- **Output:** `PASS` | `CONCERNS: <lista>` | `FAIL: <regra violada + linha + sugestão>`
- **Veto:** se `FAIL`, hook bloqueia commit
- **Escalation:** se 3 `CONCERNS` consecutivos na mesma PR, escala pra Opus + alerta no `painel-do-dono.md`

### Auditor de Qualidade
- **Modelo:** Sonnet
- **Trigger:** hook `pre-commit` em qualquer diff de código
- **Contexto injetado:** TST-*, `tests/`, diff, coverage report
- **Output:** mesmo formato
- **Veto:** bloqueia commit se TST-001/002/003/004 violados ou coverage < threshold
- **Threshold de cobertura:** a definir em ADR-0001 (depende de stack/linguagem)

### Auditor de Produto
- **Modelo:** Opus (decisão mais complexa)
- **Trigger:** pre-merge (após implementação completa, antes de virar release)
- **Contexto injetado:** `prd.md` do módulo, glossário comum + módulo, US em foco com todos AC, diff
- **Output:** mesmo formato + check explícito de **non-goals** (LLM tende a fazer mais do que pediu)
- **Veto:** bloqueia merge se algum AC binário falha
- **Escalation:** se conflito com glossário/spec, escala pra Roldão via `painel-do-dono.md`

---

## Onde os auditores VIVEM

**Decidido (2026-05-17):** **híbrido A + B**.
- **A (subagents Claude Code) durante desenvolvimento local:** `.claude/agents/auditor-seguranca.md`, `auditor-qualidade.md`, `auditor-produto.md` — invocados via hook `pre-commit` antes do `git commit` rodar.
- **B (CI GitHub Actions chamando API Anthropic) no servidor:** mesmo prompt versionado, rodando em PR. Garante que mesmo se hook local for desligado, auditor roda na PR.
- **Opção C (MCP server dedicado) rejeitada por agora:** complexidade extra sem ganho — os 3 prompts são autocontidos, não precisam orquestrador externo.

**Critério da decisão:** redundância em profundidade — local (rápido, free pro Roldão) + servidor (autoridade final, pago em tokens API). Custo aceito conscientemente.

**Coexistência com os 4 subagentes humanos-substitutos** (`tech-lead-saas-regulado`, `advogado-saas-regulado`, `corretora-seguros-saas`, `consultor-rbc-iso17025`): **escopos distintos, sem overlap.**
- Os 4 substitutos são **consultores especialistas** que orientam decisões de arquitetura/produto/legal/risco/calibração — invocados sob demanda durante design e revisão estratégica.
- Os 3 auditores são **gatekeepers automáticos** que rodam em pre-commit/pre-merge sobre código e specs — focam em violação de regras/AC/non-goals, não em opinião estratégica.
- Inventário de subagentes técnicos genéricos (code-reviewer, test-runner, security-auditor, doc-writer, performance-profiler) prescrito em `ambiente-claude-code.md` Frente 3 **NÃO será criado** — o trabalho deles está distribuído entre os 4 substitutos + 3 auditores.

---

## Quem orquestra os auditores

Pra coordenar e evitar deadlock:
- **Ordem de execução padrão:** Qualidade → Segurança → Produto (do mais barato pro mais caro em tokens).
- **Em paralelo se possível** — auditores independentes podem rodar simultâneo.
- **Auditor sentinela** (a definir): meta-auditor que valida se os 3 estão rodando, processando, vetando corretamente. Roda 1x/semana ou no postmortem de incidente.

---

## Como medir se os auditores estão entregando

`docs/governanca/metricas-operacao-agentes.md` (a criar) deve trackear:
- Taxa de `PASS` / `CONCERNS` / `FAIL` por auditor
- Falsos positivos (humano discorda do veto) → ajustar prompt
- Falsos negativos (bug entrou apesar de PASS) → adicionar regra ou ajustar prompt
- Tempo médio de auditoria por PR
- Custo médio em tokens por PR

---

## Drill trimestral

A cada 3 meses, simular cenários conhecidos:
- Query SQL sem `tenant_id` → Auditor de Segurança deve vetar
- Teste com `assertTrue(true)` → Auditor de Qualidade deve vetar
- Feature que faz mais do que o PRD pediu → Auditor de Produto deve vetar
- Resultado registrado em `governanca/trilha-auditoria-agentes.md`.

---

## A criar (próximos passos)

- ✅ ~~`auditor-seguranca-prompt.md`~~ — criado v1.0.0 em 17/05/2026
- ✅ ~~`auditor-qualidade-prompt.md`~~ — criado v1.0.0 em 17/05/2026
- ✅ ~~`auditor-produto-prompt.md`~~ — criado v1.0.0 em 17/05/2026
- ✅ ~~`auditor-drift-docs-prompt.md`~~ — criado v1.0.0 em 17/05/2026 (consultivo, sem veto)
- ✅ ~~`.claude/agents/auditor-{seguranca,qualidade,produto,drift-docs}.md`~~ — veículos criados
- ⏳ Hook `pre-commit` que invoca Segurança + Qualidade (Produto roda pre-merge; Drift roda manual/semanal)
- ⏳ GitHub Action `.github/workflows/auditor-{seguranca,qualidade,produto,drift-docs}.yml` (camada B do híbrido)
- ⏳ `docs/governanca/metricas-operacao-agentes.md` — tracking de falsos positivos/negativos
- ⏳ `docs/governanca/trilha-auditoria-agentes.md` — append-only de cada veto/PASS, retenção 2 anos
