---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Métricas — Módulo Catálogo

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Cobertura de catálogo | % de linhas de OS com item do catálogo (não "à mão") | ≥ 95% | query | mensal |
| Itens ativos | Contagem de itens ativos | — (informativo) | query | diária |
| Atualização de preço | dias desde última atualização de preço por item | ≤ 180d para top-20 | query | mensal |
| Importação inicial | taxa de sucesso por linha na importação | ≥ 90% | log importação | sob demanda |
| Itens órfãos | itens sem categoria | = 0 | query | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade | 99.9% | 43 min |
| Latência p95 lista | ≤ 1s | — |
| Latência p95 cadastro | ≤ 800ms | — |
| Importação 500 linhas | ≤ 30s | — |

---

## Dashboards

- Grafana: [pós ADR-0001]
- Axiom: [pós ADR-0001]

---

## Alertas

| Alerta | Quando | Severidade |
|---|---|---|
| Tentativa de mutação INV-026 | Cliente tentou alterar preço retroativo | P2 |
| Importação falhou > 30% das linhas | em importação | P2 |
| Item sem categoria | criado sem categoria | P3 |

---

## Métricas de saúde dos agentes

- Tokens por US-CAT-*
- Retrabalho em US-CAT
- Tempo médio entrega

---

## Como evolui

- Métrica nova → coleta + CHANGELOG.
- Target → ADR.
