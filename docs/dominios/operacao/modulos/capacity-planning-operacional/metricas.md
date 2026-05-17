---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Métricas — Capacity Planning Operacional

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % promessas cumpridas | OS entregues dentro do prazo prometido / total | ≥ 92% | join OS prazo × entrega | semanal |
| Antecedência detecção gargalo | Dias entre 1ª sinalização e ocupação > 100% | ≥ 14 dias | timestamps | mensal |
| % distribuição aceita | Sugestões aceitas sem alteração / sugestões emitidas | ≥ 60% | log distribuição | semanal |
| Erro de tempo previsto | |previsto − realizado| / previsto, mediana | ≤ 20% | join OS | mensal |
| Taxa média de ocupação | Média ponderada ocupação dos recursos | 70-85% (saudável) | cálculo diário | semanal |
| Recursos em sobrecarga | Nº recursos com ocupação > 100% | 0 | painel | diário |
| Lead time decisão de contratação | Dias entre indicação e abertura da vaga | ≤ 30 dias | log + RH | trimestral |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade painel | 99.5% | 3h36min/mês |
| Latência painel p95 | < 2s | — |
| Atraso recálculo | < 60s após evento | — |

---

## Dashboards canônicos

- Grafana: a definir pós ADR-0001
- Painel Capacity: dentro do próprio módulo (UI Tela 1)

---

## Alertas

| Alerta | Quando dispara | Notificado | Severidade |
|---|---|---|---|
| Sobrecarga prevista | recurso ultrapassa 100% em janela ≤ 14d | gerente operações | P1 |
| Gargalo iminente | recurso > 85% por 14d contínuos | gerente operações | P2 |
| Tempo previsto descalibrado | erro mediano > 30% em 30d | dono produto | P3 |
| Painel travado | recálculo > 5min sem completar | watchdog → agente | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos por feature
- Taxa de retrabalho por US
- Tempo médio de entrega
