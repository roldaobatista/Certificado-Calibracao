---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo App do Técnico

> Como saber se o app está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % OS sem retorno à base | OS executadas inteiramente em campo, sem o técnico ter que voltar à base por peça/dado faltante | ≥85% | OS marcadas com retorno_base=false / total OS | semanal |
| Tempo médio chegada→início serviço | Diferença entre check-in GPS e início de serviço | ≤10min | timestamp(início) − timestamp(check-in) | semanal |
| Taxa adoção app | % de técnicos ativos que usam o app diariamente | ≥95% | técnicos com sync nas últimas 24h / total técnicos | semanal |
| Tempo médio aprovação adiantamento | Diferença entre solicitação e aprovação/recusa | ≤4h úteis | timestamp(decisão) − timestamp(solicitação) | mensal |
| % OS com foto + checklist completos | OS fechadas com mínimo de 1 foto e checklist 100% | ≥90% | OS conformes / total OS | mensal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade API sync | 99.5% | ~3h40min/mês |
| Latência p95 sync incremental (1 dia operação) | ≤30s | — |
| Taxa erro sync | ≤2% | — |
| Tempo abertura app (cold start) | p95 ≤3s | — |
| Taxa conflito sync escalonado a humano | ≤2% das operações | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.
- Painel "Saúde da operação de campo" — composição de check-ins, syncs, conflitos.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Técnico offline >12h em dia útil | Sem sync em 12h durante horário comercial | Coordenador (push + email) | P2 |
| Taxa de conflito de sync >5% em 1h | Picos suspeitos | Watchdog → agente → Roldão | P1 |
| API sync caiu | 5xx >10% por 5min | On-call (PagerDuty ou similar) | P0 |
| Bateria do dispositivo do técnico <10% (opt-in) | Telemetria opcional | Próprio técnico | P3 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature do módulo.
- Taxa de retrabalho / feature (re-spec → re-código).
- Tempo médio de entrega de US do app vs média do produto.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR explicando.
