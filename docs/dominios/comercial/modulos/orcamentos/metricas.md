---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: orcamentos
dominio: comercial
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Orçamentos

## KPIs de negócio

| Métrica | Definição | Target MVP-1 | Como medir | Frequência |
|---|---|---|---|---|
| Tempo médio criação | Mediana de minutos entre abrir `/novo` e enviar | < 5 min | Telemetria front (start→submit) | Semanal |
| Taxa conversão → OS | % orçamentos enviados que viram OS em até 30 dias | > 40% | Job noturno calcula coorte | Mensal |
| Taxa expirado sem resposta | % orçamentos enviados que expiram sem cliente abrir o link | < 20% | Estado=expirado AND leituras=0 | Mensal |
| Taxa de leitura do link | % links abertos pelo destinatário (Wave B) | > 70% | Tracking pixel/endpoint | Semanal |
| Ticket médio | Valor médio de orçamento aprovado | medir baseline | Soma valores aprovados / N | Mensal |
| % desconto médio | Desconto médio aplicado sobre bruto | < 12% (alarme se > 18%) | Job sobre orçamentos enviados | Semanal |
| Tempo médio aprovação | Horas entre envio e aprovação do cliente | medir baseline | timestamp_aprovacao - timestamp_envio | Mensal |

## SLI/SLO técnico

| SLI | SLO | Erro mensal |
|---|---|---|
| Disponibilidade endpoint público (link cliente) | 99.5% | ~3h30/mês |
| Latência geração PDF | < 3s | — |
| Taxa erro 5xx em POST `/orcamentos` | < 0.5% | — |

## Dashboards

- Grafana — painel "Orçamentos" (pós-ADR-0001).
- BI interno — funil mensal (criado → enviado → lido → aprovado → convertido).

## Alertas

| Alerta | Quando dispara | Severidade |
|---|---|---|
| `pdf-falha-geracao` | > 3% das gerações PDF falhando em 1h | P1 |
| `link-publico-fora-do-ar` | endpoint `/o/{token}` retorna 5xx > 1% | P0 (cliente não consegue aprovar) |
| `desconto-fora-limite` | Vendedor envia orçamento com desconto > limite configurado | P2 (alerta operacional dono) |
| `aprovacao-suspeita` | Mesmo IP aprova > 5 orçamentos em < 1 min | P1 (possível bot/fraude) |

## Métricas de saúde dos agentes

- Tokens consumidos por US-ORC-NNN.
- Taxa de retrabalho por US.

## Como evolui

Métrica nova → adicionar + coleta. Mudança target → ADR.
