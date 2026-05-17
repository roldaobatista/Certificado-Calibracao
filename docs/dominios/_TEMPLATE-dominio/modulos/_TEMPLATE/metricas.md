---
owner: roldao
revisado_em: 2026-05-16
proximo_review: 2026-08-16
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo [NOME] (TEMPLATE)

> Como saber se este módulo está entregando valor. KPIs de negócio + métricas técnicas.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| [Métrica primária] | ... | ... | ... | semanal |
| [Métrica secundária] | ... | ... | ... | mensal |

---

## SLI/SLO técnico (operação)

Detalhes em `../../../operacao/observabilidade.md`. Aqui só resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | [ex: 99.9%] | [43min/mês] |
| Latência p95 | [ex: < 500ms] | — |
| Taxa de erro | [ex: < 0.1%] | — |

---

## Dashboards canônicos

- **Grafana:** [link a definir pós ADR-0001]
- **Axiom (logs):** [link]

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| [nome] | ... | Watchdog `acionamento-agente.md` → agente → Roldão se persistir | [P0/P1/P2/P3] |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA, mas refletido aqui pro contexto)

- Tokens consumidos / feature do módulo
- Taxa de retrabalho / feature
- Tempo médio de entrega de US

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → marcar `@deprecated`.
- Mudança de target → ADR explicando.
