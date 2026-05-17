# Catálogo dos 3 auditores-agentes

> **Pra quê:** materializar os 3 auditores que substituem reviewers humanos. Auditor 10 v2 alertou: sem operacionalização, "Família 5 é vaporware".
>
> **Status atual:** esqueleto. Prompts completos em `auditor-*-prompt.md` (a criar quando stack for definida, porque algumas validações dependem de ferramenta).

---

## Os 3 auditores

| Auditor | Lê | Trigger | Poder de veto |
|---|---|---|---|
| **Segurança** | `REGRAS-INEGOCIAVEIS.md` (SEC-*, INV-TENANT-*), `docs/seguranca/`, diff do commit | Pre-commit em código que toca `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`, `.claude/hooks/` | **Bloqueia commit** se SEC-* violado |
| **Qualidade** | `REGRAS-INEGOCIAVEIS.md` (TST-*), `tests/`, diff | Pre-commit em qualquer código | **Bloqueia commit** se TST-* violado ou cobertura abaixo do mínimo |
| **Produto** | `docs/dominios/<mod>/prd.md`, `docs/comum/glossario.md`, US em foco | Pre-merge em feature (após implementação completa) | **Bloqueia merge** se AC binário não passa |

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

A definir quando stack for escolhida:
- **Opção A:** subagents do Claude Code em `.claude/agents/{seguranca,qualidade,produto}.md`
- **Opção B:** scripts CI (GitHub Actions, GitLab CI) chamando API Anthropic
- **Opção C:** MCP server dedicado que orquestra os 3

**Decisão entra na ADR-0001 ou ADR-0004.**

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

## A criar (Rodada 4)

- `auditor-seguranca-prompt.md` — prompt completo do Auditor 1
- `auditor-qualidade-prompt.md` — prompt completo do Auditor 2
- `auditor-produto-prompt.md` — prompt completo do Auditor 3
- Hook `pre-commit` que invoca auditores
- Hook `pre-merge` (ou GitHub Action) que invoca auditor de produto
