---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Métricas — Base de Conhecimento

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de aceitação de sugestão | % das sugestões dentro de Chamado/OS que o usuário abre | ≥ 35% | clicks / sugestões exibidas | semanal |
| Cobertura por equipamento | % dos equipamentos top-50 com ≥ 1 artigo publicado | ≥ 80% em 6 meses | join equipamentos × artigos | mensal |
| Tempo médio de resolução com artigo | Tempo OS/Chamado fechado quando consumiu artigo | < 70% do tempo sem artigo | comparar buckets | mensal |
| Artigos desatualizados | Nº de artigos sem revisão > 12 meses | < 10% do total | query date diff | mensal |
| Latência aprovação | Mediana de horas entre submissão e aprovação | < 48h | timestamps | semanal |
| Utilidade média | (% útil) / (% útil + % não útil) por artigo | ≥ 75% no top 20 | agregado de votos | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.5% | 3h36min/mês |
| Latência busca p95 | < 800ms | — |
| Taxa de erro upload | < 0.5% | — |

---

## Dashboards canônicos

- Grafana: link a definir pós ADR-0001
- Axiom (logs): link

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Aprovação parada | artigo > 7 dias em revisão | aprovador + gerente | P2 |
| Sugestão zerada | nenhuma sugestão aceita em 7d consecutivos | dono produto | P3 |
| Upload falhando | > 5% erros em 1h | watchdog → Roldão | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos por feature
- Taxa de retrabalho por US
- Tempo médio de entrega
