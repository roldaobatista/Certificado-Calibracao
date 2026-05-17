---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Métricas — Módulo Fornecedores

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Cotações em paralelo | % de pedidos de compra > teto que vieram de cotação ≥ 3 fornecedores | ≥ 80% | query | mensal |
| Tempo médio de cotação | mediana entre criação e escolha | ≤ 5 dias úteis | query | mensal |
| Taxa de resposta de fornecedor | (cotações respondidas) / (enviadas) | ≥ 60% | query | mensal |
| Economia em cotação | (preço mais alto − preço escolhido) / preço mais alto | ≥ 5% médio | query | mensal |
| Avaliação média fornecedor | média rolling 12m por fornecedor | ≥ 7/10 | query | mensal |
| Fornecedores ativos | contagem | — (informativo) | query | semanal |
| Pedidos sem cotação prévia (acima de teto) | violação de regra | = 0 | query | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade | 99.9% | 43 min |
| Latência p95 comparativo | ≤ 1.5s | — |
| Latência p95 cadastro | ≤ 800ms | — |
| Latência p95 envio cotação (e-mail) | ≤ 30s | — |
| Taxa de erro | < 0.1% | — |

---

## Dashboards

- Grafana: [pós ADR-0001]
- Axiom: [pós ADR-0001]

---

## Alertas

| Alerta | Quando | Severidade |
|---|---|---|
| Contrato / credenciamento vencendo | ≤ 30d | P2 |
| Cotação enviada e sem resposta após 5 dias | sem ação | P3 |
| Avaliação caiu abaixo de 5/10 | últimas 3 entregas | P2 |
| Pedido > teto sem cotação | violação | P1 |
| Token de resposta de cotação expirou sem resposta | informativo | P3 |

---

## Métricas de saúde dos agentes

- Tokens por US-FOR-*
- Retrabalho
- Tempo médio de entrega

---

## Como evolui

- Métrica nova → coleta + CHANGELOG.
- Target → ADR.
