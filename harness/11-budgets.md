# 11 — Budgets mensuráveis e circuit breakers

> **P0-7**: transforma o princípio "budgets são feature de produto" em valores concretos, versionados e aplicáveis por hook/CI.
>
> Valores abaixo são **baseline** — revistos a cada fim de fatia vertical (V1–V5) com dados reais.

## 1. Tetos de tokens

| Escopo | Soft cap (alerta) | Hard cap (bloqueio) |
|--------|-------------------|---------------------|
| Por tool call isolado | 20k | 50k |
| Por task (subagente) | 100k | 200k |
| Por PR completo (soma de sessões) | 350k | 500k |
| Por sessão de orquestrador | `/compact` forçado aos 50% | `/clear` obrigatório aos 70% |
| Context rot threshold (modelo 1M) | 300k | 400k |

**Enforcement:** hook `PreToolUse` consulta contador de tokens acumulado; ao ultrapassar hard cap, bloqueia a chamada e exige `/compact` ou `/clear`.

## 2. Tetos de custo (USD)

| Escopo | Alerta | Bloqueio |
|--------|--------|----------|
| Por dev / dia | $15 | $30 |
| Por dev / semana | $60 | $120 |
| Por PR | $8 | $15 |
| Por tenant (dogfood) / mês | $50 | $100 |
| Por cloud agent task (Tier 3) | $3 | $5 |

**Enforcement:** cost tracker em `.claude/hooks/cost-tracker.ts` lê metadata da API Anthropic e escreve em `compliance/budget-log/`; bloqueio é *fail-closed*.

## 3. Paralelismo

| Tier | Máx concorrente | Motivo |
|------|-----------------|--------|
| Tier 1 — subagentes do orquestrador | 5 | Limita crescimento de context do pai |
| Tier 2 — worktrees concorrentes | 3 | Evita contenção de CI e revisão humana |
| Tier 3 — cloud agents concorrentes | 2 | Superfície de exposição reduzida |

**Enforcement:** gate no orquestrador bloqueia `Agent(...)` além do limite; worktrees coordenados por Conductor/Claude Squad.

## 4. Retries e circuit breakers

| Gatilho | Ação |
|---------|------|
| 3 tool errors consecutivos na mesma task | Abort task; exige intervenção humana |
| 5 edits consecutivos no mesmo arquivo em < 10 min | Pausa; suspeita de loop |
| 2 falhas consecutivas em `evals/regulatory/` na mesma branch | Freeze da branch até *root cause* documentado |
| 1 falha em `evals/tenancy/` | Freeze imediato; incidente aberto |
| 1 divergência de hash-chain | Freeze **global** de releases |
| Worktree sem heartbeat por 4h | Sinaliza humano e persiste trace |

## 5. Política de `/compact`

- **Manual preferido**: agente chama `/compact` com *hint* ao chegar em 50% do context window. Hint descreve o que manter (decisões, código tocado) e o que descartar (outputs de tool verbosos, exploração).
- **Auto-compact** só como último recurso; registrado em log.
- **Rewind > correct**: se último turno foi ruim, `/rewind` antes de corrigir — evita poluir contexto com tentativas falhas.

## 6. Política de modelo

| Modelo | Usar para |
|--------|-----------|
| Opus | `regulator`, `metrology-calc`, `product-governance`, tasks com raciocínio multipass |
| Sonnet | Engenharia geral (default) |
| Haiku | Varreduras (copy-lint em batch, indexação de specs, classificação de issues) |

**Downgrade forçado**: se uma task Opus consumir > 150k tokens sem entregar, sistema força replan com Sonnet + *scratchpad* reduzido.

## 7. Timeouts

| Operação | Timeout |
|----------|---------|
| Tool call individual | 120s (default) |
| Bash de longa duração | 10 min (deve rodar em `run_in_background`) |
| Task de subagente | 30 min; após, escala para humano |
| Worktree ativo | 4h; após, revisa e encerra |
| Cloud agent task | 2h; após, cancelado e revisado |

## 8. Registro e auditoria

- `compliance/budget-log/YYYY-MM-DD.jsonl` — linha por evento de budget (consumo, alerta, bloqueio).
- Relatório semanal gerado por CI em `compliance/budget-log/weekly/<semana>.md`.
- Revisão mensal pelo `product-governance` com ajuste dos caps se necessário (ADR obrigatória).

## 9. Revisão dos valores

Os números aqui são hipóteses iniciais. Ao fim de cada fatia vertical:
1. Extrair consumo real do `budget-log`.
2. Comparar com cap proposto.
3. Ajustar para percentil 95 real + margem de 20%.
4. Registrar decisão em `adr/<n>-budget-revision-v<n>.md`.
