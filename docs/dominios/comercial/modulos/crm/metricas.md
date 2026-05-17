---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
audiencia: dono
---

# Métricas — Módulo CRM

## KPIs de negócio

| Métrica | Definição | Target MVP-1 | Como medir | Frequência |
|---|---|---|---|---|
| Taxa conversão lead → cliente | Leads convertidos em cliente master / leads totais | > 25% | Coorte mensal | Mensal |
| Taxa conversão oportunidade → vendido | Oportunidades em "fechado-ganho" / total movido no mês | medir baseline | Funil mensal | Mensal |
| NPS médio | Média das respostas NPS últimos 90d | ≥ 60 (zona "promotor") | Job semanal | Semanal |
| Tempo médio resposta NPS detrator | Horas entre resposta detrator e primeiro contato do vendedor | < 4h | Diff timestamps | Semanal |
| % automações testadas em sandbox | Automações ativas que passaram por sandbox / total | 100% (obrigatório) | Flag no registro | Diária |
| Tarefas atrasadas | Tarefas com prazo vencido sem ação | < 10% do total ativo | Job diário | Diária |
| % clientes com último contato > 90d | Carteira ativa sem nenhum contato em 90d | < 30% | Job semanal | Semanal |
| Lead scoring distribuição | % leads alta prioridade (>70 pontos) | medir baseline | Job diário | Semanal |
| Motivos de perda — Top 3 | Motivos mais frequentes nos últimos 90d | reportar Top 3 | Job mensal | Mensal |

## SLI/SLO técnico

| SLI | SLO | Erro mensal |
|---|---|---|
| Disponibilidade `/crm/*` | 99.5% | ~3h30 |
| Latência p95 "lista do dia" | < 2s | — |
| Latência drag-and-drop kanban | < 500ms | — |
| Job NPS pós-OS — sucesso | > 99% | — |

## Dashboards

- Grafana — painel "CRM" (pós-ADR-0001).
- MAPA-DO-DONO consolidado (visão dono dos KPIs CRM).

## Alertas

| Alerta | Quando dispara | Severidade |
|---|---|---|
| `automacao-disparo-massivo` | Automação envia > 100 mensagens em < 5 min (suspeita) | P0 (bloqueia + notifica dono) |
| `automacao-ativada-sem-sandbox` | Ativação sem flag sandbox_ok=true | P0 (R-novo CRM-1 ativo) |
| `nps-detrator-sem-tarefa` | NPS detrator sem tarefa criada em 30 min | P1 |
| `tarefa-orfa` | Tarefa sem responsável atribuído > 1h | P2 |
| `caixa-entrada-acumulada` | Caixa de entrada > 50 leads pendentes | P2 (sobrecarga atendente) |

## Métricas de saúde dos agentes

- Tokens / US-CRM-NNN.
- Retrabalho por US.
- Tempo médio implementação.

## Como evolui

Métrica nova → adicionar + coleta + dashboard.
