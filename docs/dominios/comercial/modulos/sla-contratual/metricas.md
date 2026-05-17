---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo SLA Contratual

> Como saber se o módulo entrega valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % SLA cumprido | (SLAs cumpridos / SLAs ativos no período) × 100 | ≥ 95% | agregação eventos `SLA.Cumprido` vs `SLA.Estourou` | semanal |
| Tempo médio de detecção de risco | minutos entre alerta de 80% e ação do atendente | ≤ 15 min | timestamp alerta vs ação | semanal |
| Taxa de escalonamento desnecessário | escalonamentos sem ação necessária / total escalonamentos | ≤ 10% | revisão pós-incidente | mensal |
| % penalidades aplicadas via evento | (penalidades aplicadas via evento / penalidades calculadas) × 100 | 100% | comparação Financeiro vs eventos | mensal |
| Cobertura de evidência | OS encerradas vinculadas a SLA com ≥1 evidência / total | ≥ 90% | query | mensal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do cronômetro de SLA | 99.9% | 43min/mês |
| Latência atualização cronômetro | < 1s p95 | — |
| Taxa de evento `SLA.*` perdido | 0% | zero tolerância |

---

## Dashboards canônicos

- **Grafana:** painel "SLA — Cumprimento por Cliente" (a definir pós ADR-0001).
- **Grafana:** painel "SLA — Risco em Tempo Real".
- **Axiom (logs):** trilha de pausas/despausas.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| SLA em 80% | cronômetro atinge 80% do limite | atendente responsável | P2 |
| SLA em 90% | cronômetro atinge 90% | atendente + gerente | P1 |
| SLA estourado | tempo > limite | gerente + financeiro + diretoria | P0 |
| Pausa de SLA suspeita | pausa > 24h sem despause | gerente | P2 |
| Cronômetro indisponível | sensor de heartbeat falha | watchdog → agente → Roldão | P0 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos por feature SLA.
- Taxa de retrabalho por US.
- Tempo médio de entrega por US.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
