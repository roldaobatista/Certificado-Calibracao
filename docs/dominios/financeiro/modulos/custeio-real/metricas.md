---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Custeio Real

> KPIs de negócio + SLI/SLO técnico.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % OSs com custo apurado em ≤24h | OSs cujo custo real foi calculado em até 24h após encerramento | ≥ 95% | (count apuradas ≤24h) ÷ (count encerradas) | semanal |
| % OSs deficitárias revisadas em ≤7d | OSs marcadas deficitárias que tiveram intervenção do gestor em até 7 dias | ≥ 90% | (deficitárias revisadas) ÷ (deficitárias detectadas) | mensal |
| Aderência apuração | % de aderência entre custo apurado pelo sistema e custo revisado manualmente em amostragem | ≥ 95% | amostra mensal | mensal |
| Margem real média da empresa | Margem % consolidada do mês | tendência crescente | sum margem / sum receita | mensal |
| % OSs deficitárias | Quantas OSs encerraram com margem negativa | ≤ 10% | (count margem<0) ÷ (count encerradas) | mensal |
| % retrabalho por técnico | Horas de retrabalho ÷ horas totais do técnico | ≤ 5% | calculado | mensal |
| % garantia por tipo de serviço | Custo garantia ÷ receita do serviço | ≤ 8% | calculado | mensal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Apuração consome evento `Operacao.OSEncerrada` em <5min | 99% | — |
| Idempotência da apuração (re-execução = mesmo resultado) | 100% | 0 |
| Latência relatório agregado p95 | < 5s | — |
| Disponibilidade dashboards margem | 99.9% | 43min/mês |

---

## Dashboards canônicos

- **Grafana:** "Custeio Real" — margem do mês, OSs deficitárias do mês, % retrabalho por técnico.
- **Axiom:** filtro `module:custeio-real`.

---

## Alertas configurados

| Alerta | Quando dispara | Quem | Severidade |
|---|---|---|---|
| OS deficitária encerrada | margem real < threshold do tenant | gestor operacional | P2 |
| Cluster de OSs deficitárias do mesmo cliente | ≥3 deficitárias / 30 dias mesmo cliente | dono + gestor | P1 |
| Apuração não rodou (lag >1h) | evento consumido com atraso | Watchdog → agente → Roldão | P1 |
| Custo apurado divergente da revisão manual >5% (amostra) | qualidade da apuração caiu | dono | P2 |

---

## Métricas de saúde dos AGENTES

(Família 5 Governança IA)

- Tokens / feature
- Taxa de retrabalho de feature do módulo
- Tempo médio entrega de US

---

## Como esta lista evolui

- Métrica nova → adicionar + coleta + CHANGELOG.
- Mudança de target → ADR.
