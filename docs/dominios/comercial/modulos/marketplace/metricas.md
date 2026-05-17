---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Marketplace

> Como saber se o módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa visita → solicitação | solicitações criadas / visitantes únicos | > 2% | analytics + tabela `solicitacao_orcamento` | semanal |
| Taxa solicitação → orçamento fechado | orçamentos aprovados oriundos do marketplace / solicitações | > 30% | join solicitação + orçamento + aprovação | mensal |
| Tempo médio visita → solicitação | tempo entre primeira pageview e envio da solicitação | < 4 min | timestamps de eventos | semanal |
| Ticket médio do marketplace | valor médio dos orçamentos aprovados via marketplace | acompanhar (sem target — comparar com canal manual) | soma valor / qtd | mensal |
| Taxa de adesão a serviço recorrente | clientes que assinaram recorrente / clientes ativos | > 15% (após 6 meses) | tabela `contrato_recorrente` | mensal |
| Taxa de uso da área do cliente | clientes ativos que logaram nos últimos 30d / total | > 40% | log de login | mensal |
| Carrinhos abandonados | carrinhos criados sem envio em 24h | < 60% (referência e-commerce) | tabela `carrinho` com timestamp | semanal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade vitrine pública | 99.5% | ~3h40min/mês |
| Latência TTFB vitrine | p95 < 800ms | — |
| Latência checkout solicitação | p95 < 1.5s | — |
| Taxa de erro 5xx | < 0.5% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.
- **Funil de conversão:** dashboard próprio (visita → carrinho → solicitação → orçamento → fechado).

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Queda brusca de visitantes (> 30%) em 1h | comparativo hora a hora | watchdog → agente → gestor | P2 |
| Taxa de erro de envio de solicitação > 5% em 15min | falha no formulário | watchdog → agente → Roldão se persistir | P1 |
| Vitrine indisponível (5xx > 5%) | impacto reputacional | watchdog → agente | P0 |
| Carrinhos abandonados acima de 80% por 7 dias | sinal de problema de UX | gestor | P3 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature.
- Taxa de retrabalho / feature.
- Tempo médio de entrega de US-MKT-*.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta.
- Métrica obsoleta → marcar `@deprecated`.
- Mudança de target → ADR explicando.
