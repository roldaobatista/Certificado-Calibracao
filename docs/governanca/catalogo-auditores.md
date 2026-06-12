# Catálogo dos auditores-agentes

> **Pra quê:** materializar os auditores que substituem reviewers humanos. Auditor 10 v2 alertou: sem operacionalização, "Família 5 é vaporware".
>
> **Inventário atual: 11 prompts** em `docs/governanca/auditor-*-prompt.md` — os **10 da Família 5** invocados no ritual fim-de-fase (seguranca, qualidade, produto, drift-docs, llm-correctness, performance, observabilidade, idempotencia, supplychain, conformidade-lgpd) + **1 transversal Tier 4** (`bus-integrity` v1.0.0 stable, criado 2026-05-22 — bloqueia commit no mesmo nível de idempotencia/supplychain; rastreado separadamente porque cobre INV-INT cross-módulo, não escopo de uma fase).
>
> **Status atual (2026-05-27):** **10 auditores em operação stable** — provados em 5+ ciclos PASS (F-A, F-B, M1 clientes, M2 equipamentos, F-C1, M3 OS, M4 calibração). Marco 4 (2026-05-27) exercitou os 10 em 2 passadas completas: 1ª passada 2 PASS / 1 CONCERNS / 7 FAIL (41 C/A/M) → 6 batches conserto causa-raiz → 2ª passada 8 PASS + 2 CONCERNS BAIXO carryover. LLM-correctness subiu CONCERNS→PASS. Convergência observada após o ritual S1..S6.1.
>
> **Motivação do Tier 1+2+3:** o bug 2026-05-19 do `sanitizar_payload_audit` (UUID redigido como PII em ~8% dos clientes) **passou em PASS dos 3 auditores 1.0.0** porque a função era exercitada só via teste de integração com input aleatório. Lacuna concreta provou que precisamos endurecer (Tier 1: TST-005..007 + SEC-SANITIZE-001) e expandir cobertura (Tier 2: LLM correctness; Tier 3: performance, observabilidade, idempotência, supply chain, LGPD mecânico).
>
> **Atualizado 2026-06-12 — auditoria de cerimônia (aprovação Roldão — pacote B R7):** drift-docs aposentado do fechamento; supplychain roteado por diff de deps; conformidade-lgpd roteado por diff PII. Ver §"Roteamento pós-reforma" abaixo.

---

## Roteamento pós-reforma (emenda R7 2026-06-12 — auditoria de cerimônia)

| Auditor | Status no fechamento | Novo gatilho | Evidência de decisão |
|---|---|---|---|
| **drift-docs** | **APOSENTADO do fechamento** | Varredura semântica mensal autônoma (pendência stale, ADR proposta superada, draft fossilizado, link quebrado) + gate mecânico `scripts/status-projeto.sh --check` | 32 achados históricos / **0 bugs de produto** (100% contagem/status) — sem valor de fechamento |
| **supplychain** | Roteado — **SOMENTE por diff** | Roda quando diff toca `pyproject.toml`, `poetry.lock`, `package*.json`, `Dockerfile`, `.github/workflows/**`. Fora disso: não roda | **0 achados MÉDIO+ em toda a história** do projeto |
| **conformidade-lgpd** | Roteado — **SOMENTE por diff PII** | Roda quando diff toca `models.py`, `serializers.py`, `migrations/**` ou `src/domain/**` com campo de pessoa física, ou eventos com payload de pessoa | Formaliza prática observada de M6 a M9 — já era assim na prática; agora é norma escrita |

---

## Os 10 auditores

| # | Auditor | Lê | Trigger | Poder de veto | Modelo |
|---|---|---|---|---|---|
| 1 | **Segurança** v1.1.0 | `REGRAS-INEGOCIAVEIS.md` (SEC-*, INV-TENANT-*, SEC-SANITIZE-*), `docs/seguranca/`, diff | Pre-commit em `financeiro/`, `auth/`, `tenant/`, `kms/`, `migrations/`, `audit/`, `.claude/hooks/`, `.github/workflows/` | **Bloqueia commit** | Sonnet 4.6 / Opus 4.7 escalation |
| 2 | **Qualidade** v1.1.0 | `REGRAS-INEGOCIAVEIS.md` (TST-001..007), `tests/`, diff, coverage | Pre-commit em qualquer código | **Bloqueia commit** | Sonnet 4.6 |
| 3 | **Produto** v1.1.0 | `docs/dominios/<mod>/prd.md`, glossário, US em foco | Pre-merge | **Bloqueia merge** | Opus 4.7 |
| 4 | **Drift de docs** v1.0.0 | `docs/`, `.claude/`, `.specify/`, raízes canônicas, `MEMORY.md` | Manual / semanal | **Nenhum** — consultivo | Sonnet 4.6 |
| 5 | **LLM Correctness** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (LLM-*), `AGENTS.md` §3, diff | Pre-commit em `src/**`, `tests/**` | **Bloqueia commit** | Opus 4.7 |
| 6 | **Performance** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (PERF-*), diff, `pyproject.toml` | Pre-commit em `views.py`/`services.py`/`use_cases.py`/`src/domain/**` | **Bloqueia commit** | Sonnet 4.6 |
| 7 | **Observabilidade** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (OBS-*), `audit/services.py`, estado F-C | Pre-commit em paths sensíveis e `views.py` | **Bloqueia commit** | Sonnet 4.6 |
| 8 | **Idempotência** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (IDEMP-*), ADR-0015 | Pre-commit em `views.py`/`handlers.py`/`tasks.py`/`consumers.py` | **Bloqueia commit** | Sonnet 4.6 |
| 9 | **Supply Chain** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (DEP-*), commit message, estado Wave A | Pre-commit em manifests/Dockerfile/workflows | **Bloqueia commit** | Sonnet 4.6 |
| 10 | **Conformidade LGPD (mecânico)** v1.0.0 | `REGRAS-INEGOCIAVEIS.md` (LGPD-MEC-*), `retencao-matriz.md`, `audit/services.py` | Pre-commit em `models.py`/`views.py`/`serializers.py`/`migrations/**`/`src/domain/**` | **Bloqueia commit** | Sonnet 4.6 / Opus 4.7 escalation |

**Severidade consistente com INV-RITUAL-001:** os 10 auditores classificam achado como CRÍTICO/ALTO/MÉDIO/BAIXO. MÉDIO+ bloqueia fechamento de Fase/Marco/Story. Apenas BAIXO vira `GATE-<auditor>-NNN` rastreado.

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

- ✅ ~~`auditor-{seguranca,qualidade,produto}-prompt.md` v1.0.0~~ — 2026-05-17
- ✅ ~~`auditor-drift-docs-prompt.md` v1.0.0~~ — 2026-05-17 (consultivo)
- ✅ ~~`auditor-{seguranca,qualidade}-prompt.md` v1.1.0 stable~~ — 2026-05-19 (TST-005..007, SEC-SANITIZE-001)
- ✅ ~~`auditor-produto-prompt.md` v1.1.0 stable~~ — 2026-05-19 (bump versão; conteúdo mantido)
- ✅ ~~`auditor-llm-correctness-prompt.md` v1.0.0~~ — 2026-05-19 (Tier 2)
- ✅ ~~`auditor-{performance,observabilidade,idempotencia,supplychain,conformidade-lgpd}-prompt.md` v1.0.0~~ — 2026-05-19 (Tier 3)
- ✅ ~~`.claude/agents/auditor-{seguranca,qualidade,produto,drift-docs,llm-correctness,performance,observabilidade,idempotencia,supplychain,conformidade-lgpd}.md`~~ — 10 veículos criados
- ⏳ Hook `pre-commit` que invoca o pipeline dos 10 (orquestração paralela quando independentes — ver §"Quem orquestra")
- ⏳ GitHub Actions `.github/workflows/auditor-*.yml` (camada B do híbrido) — 1 por auditor
- ⏳ `docs/governanca/metricas-operacao-agentes.md` — tracking de falsos positivos/negativos
- ⏳ `docs/governanca/trilha-auditoria-agentes.md` — append-only de cada veto/PASS, retenção 2 anos
- ⏳ Drill semestral consolidado dos 10 — substitui o drill trimestral individual
