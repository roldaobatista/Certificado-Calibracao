---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Automações & BPM

> Como saber se o módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % aprovações no prazo | aprovações concluídas dentro do SLA / total | ≥ 95% | log de execução vs SLA | semanal |
| Tempo médio editor → produção | tempo entre publicar fluxo e 1ª execução real | ≤ 1 dia | timestamps versão vs primeira instância | mensal |
| Taxa de reprocessamento bem-sucedido | reprocessamentos OK / total tentado | ≥ 90% | log de execução | semanal |
| % regras em "shadow mode" promovidas | regras shadow que viram "ativo" | ≥ 70% | estado da regra | mensal |
| Fluxos ativos por tenant | número médio de fluxos publicados por tenant | crescer 10%/mês nos 6 primeiros meses | contagem direta | mensal |
| Pendências escalonadas | pendências que estouraram SLA e foram escaladas | ≤ 5% do total | log de escalonamento | semanal |

---

## SLI/SLO técnico

Detalhe em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do editor | 99.5% | ~3,6h/mês |
| Disponibilidade do painel de pendências | 99.9% | ~43min/mês |
| Latência avaliação de condição p95 | < 100ms | — |
| Latência render painel pendências p95 | < 500ms | — |
| Taxa de erro de execução | < 1% | — |

---

## Dashboards canônicos

- **Grafana:** painel "BPM — execuções, falhas, SLA" (link pós ADR-0001).
- **Axiom (logs):** query saved `module:bpm` (link pós ADR-0001).

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Spike de falhas de execução | > 5% em janela 15min | Watchdog → agente → Roldão se persistir | P1 |
| SLA estourado em massa (> 20 pendências) | janela 1h | Watchdog → gestor do tenant | P2 |
| Regra com loop (instância > 50 etapas) | imediato | Watchdog → suspende regra + agente | P1 |
| Gateway de notificação fora | dependência indisponível | Watchdog → operador suporte | P2 |
| Editor visual fora | health-check 3 falhas seguidas | Watchdog → agente | P1 |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA)

- Tokens consumidos / feature do módulo.
- Taxa de retrabalho / feature (US re-aberta após "concluída").
- Tempo médio de entrega de US-BPM-NNN.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → marcar `@deprecated`.
- Mudança de target → ADR.
