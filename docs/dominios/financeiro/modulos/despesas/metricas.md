---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Despesas

> Como saber se o módulo entrega valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo médio de aprovação | Da criação à primeira decisão (aprovar/rejeitar) | ≤ 3 dias úteis | timestamp `criada_em` vs. `decidida_em` | semanal |
| Tempo médio de reembolso | Da aprovação à liquidação em `contas-pagar/` | ≤ 7 dias úteis | timestamp `aprovada_em` vs. `liquidada_em` | semanal |
| % despesas com comprovante | Comprovante obrigatório (invariante) | 100% | count(comprovante_hash != null) / total | diário |
| % rejeição | Despesas rejeitadas / total lançadas | ≤ 8% | contagem direta | mensal |
| % despesas vinculadas a OS quando de campo | Vínculo presente quando categoria for de campo | ≥ 90% | filtro por categoria de campo | mensal |
| Gasto por centro de custo vs. orçado | Comparativo com orçamento (quando existir) | — | join com módulo orçamento futuro | mensal |

---

## SLI/SLO técnico

Ver `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade | 99,9% | 43 min |
| Latência p95 listagem | < 800 ms | — |
| Latência p95 upload de comprovante | < 3 s (até 5 MB) | — |
| Taxa de erro 5xx | < 0,1% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001
- **Axiom (logs):** a definir

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Backlog de despesas pendentes > 30 | Mais de 30 despesas pendentes há > 5 dias úteis | Watchdog → financeiro | P2 |
| Falha upload de comprovante > 5% | Taxa de falha em 1 h | Watchdog → on-call | P1 |
| Despesa aprovada > 30 dias sem reembolso | Estoque "aprovada" envelhecendo | Financeiro | P2 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature.
- Taxa de retrabalho / feature.
- Tempo médio de entrega de US-DSP-NNN.

---

## Como esta lista evolui

- Nova métrica → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
