---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Relatórios Financeiros

> Como saber se o módulo entrega valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Adoção semanal pelo gestor | % gestores que abrem o módulo ≥ 1×/semana | ≥ 80% | event tracking por papel | semanal |
| Tempo médio para fechar o mês | Da virada do mês ao fechamento contábil terceirizado | redução ≥ 30% vs. baseline manual | timestamp evento `fechamento.finalizado` | mensal |
| % números com drill-down funcional | Quantidade de células agregadas que abrem detalhe | 100% (invariante) | teste automatizado | release |
| Diferenças encontradas em conciliação | Linhas divergentes / total importado | tendência de queda mês a mês | log de conciliação | mensal |
| Exports gerados | Quantos PDF/XLSX/CSV saem do módulo / mês | tendência de alta nos primeiros 3 meses (adoção) | event tracking | mensal |

---

## SLI/SLO técnico

Ver `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade | 99,9% | 43 min |
| Latência DRE mensal p95 | < 2 s | — |
| Latência aging p95 | < 1 s | — |
| Latência fluxo projetado 90 dias p95 | < 3 s | — |
| Latência drill-down p95 | < 800 ms | — |
| Taxa de erro 5xx | < 0,1% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001
- **Axiom (logs):** a definir

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Materialized view atrasada > 2 h | Refresh não rodou na janela esperada | Watchdog → on-call | P1 |
| DRE > 5 s p95 por 10 min | Performance degradada | On-call | P2 |
| Falha de import OFX > 10% | Importações falhando | Financeiro + on-call | P2 |
| Divergência entre soma da view e soma dos lançamentos | Quebra de consistência | On-call (P0 — corrompe relatório) | P0 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature.
- Taxa de retrabalho / feature.
- Tempo médio de entrega de US-RFN-NNN.

---

## Como esta lista evolui

- Nova métrica → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
