---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contratos
dominio: comercial
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Contratos

## KPIs de negócio

| Métrica | Definição | Target MVP-1 | Como medir | Frequência |
|---|---|---|---|---|
| MRR de contratos | Receita mensal recorrente prevista de contratos ativos | medir baseline | Soma valor_mensal_equiv contratos vigentes | Diária |
| Taxa de renovação | Contratos renovados / contratos elegíveis (vigência fim no período) | > 80% | Coorte mensal | Mensal |
| Churn mensal | Contratos encerrados / total ativo no início do mês | < 3% | Job mensal | Mensal |
| % pré-OS confirmadas em 48h | Pré-OS geradas que viraram OS formal em ≤ 48h | > 90% | Diff timestamps | Semanal |
| % pré-OS para cliente bloqueado | Pré-OS geradas com flag bloqueada | medir baseline (alarme se > 5%) | Job diário | Diária |
| Tempo médio renovação (wizard) | Mediana minutos de uso do wizard de renovação | < 5 min | Telemetria front | Mensal |
| % contratos com aditivo no período | Aditivos / contratos ativos | medir baseline | Job mensal | Mensal |
| Lifetime médio de contrato | Mediana meses entre criação e encerramento | medir baseline | Coorte (terminados) | Trimestral |
| Motivo top de encerramento | Top 3 motivos quando cliente encerra | reportar | Job mensal | Mensal |

## SLI/SLO técnico

| SLI | SLO | Erro mensal |
|---|---|---|
| Disponibilidade `/contratos/*` | 99.5% | ~3h30 |
| Job noturno gera pré-OS sem falhar | > 99.5% | — |
| Latência p95 cadastro contrato | < 1s | — |
| Job de renovação termina em janela noturna | < 30 min para 10k contratos | — |

## Dashboards

- Grafana — painel "Contratos" + alertas de vigência.
- MAPA-DO-DONO — bloco MRR + alertas renovação.

## Alertas

| Alerta | Quando | Severidade |
|---|---|---|
| `pre-os-cliente-bloqueado` | Pré-OS criada com cliente bloqueado | P1 (alerta financeiro + vendedor) |
| `vigencia-vencendo-30d` | Contratos com vigência fim em 30d sem renovação iniciada | P2 (vendedor + dono) |
| `pre-os-nao-confirmada-72h` | Pré-OS gerada há > 72h sem confirmação | P1 (atendente sobrecarregado ou esquecido) |
| `job-pre-os-falhou` | Job noturno terminou com erro | P0 (impacta geração — receita) |
| `encerramento-cliente-massivo` | > 5 encerramentos do mesmo tenant em < 24h | P1 (algo errado — investigar) |

## Métricas de saúde dos agentes

- Tokens / US-CTR-NNN.
- Retrabalho por US.

## Como evolui

Métrica nova → adicionar + coleta.
