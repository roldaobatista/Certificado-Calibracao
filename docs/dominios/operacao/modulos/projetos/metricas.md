---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
modulo: projetos
dominio: operacao
---

# Métricas — Módulo Gestão de Projetos

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % projetos no prazo | Projetos concluídos com data_fim_real ≤ data_fim_prevista (com aditivos) ÷ total | ≥ 70% | Comparação de datas no fechamento | mensal |
| Margem média | Média de margem realizada nos projetos concluídos no período | ≥ 20% | Somatório receita − custo / projeto | mensal |
| Projetos em zona de risco | Projetos com custo_realizado ≥ 80% do previsto sem etapa equivalente concluída | ≤ 10% | Cron diário | semanal |
| % aceites no prazo | Etapas com aceite ≤ 7 dias após conclusão ÷ total | ≥ 80% | Diferença de timestamps | mensal |
| Tempo médio de aprovação de aditivo | Data aprovação − data abertura | ≤ 10 dias úteis | Eventos `Aditivo.Aprovado` | mensal |
| Valor médio de aditivos | Soma do valor de aditivos ÷ qtd | benchmark interno | Eventos `Aditivo.Aprovado` | trimestral |
| Risco materializado | Riscos cadastrados que viraram ocorrência | < 30% | Cruzamento com diário | trimestral |
| Reincidência de cliente | Clientes com ≥ 2 projetos em rota de prejuízo | sinal de atenção | Dashboard portfólio | trimestral |

---

## SLI/SLO técnico

Ver `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade do Gantt | 99.5% | ~3.6h/mês |
| Latência p95 dashboard projeto | < 800ms (consulta agrega vários módulos) | — |
| Taxa de erro em vínculo OS↔Projeto | 0% (crítico) | — |

---

## Dashboards canônicos

- Grafana: a definir pós ADR-0001
- Painel "Portfolio" — todos projetos com semáforo (verde/amarelo/vermelho) por prazo e budget

---

## Alertas

| Alerta | Quando dispara | Quem notifica | Severidade |
|---|---|---|---|
| Custo > 80% do previsto sem entrega equivalente | cron diário | Gerente de projeto + Dono | P1 |
| Etapa atrasada > 5 dias úteis | cron diário | Responsável da etapa | P2 |
| Aceite pendente > 15 dias | cron diário | Gerente | P2 |
| Aditivo pendente de aprovação > 7 dias | cron diário | Gerente + Dono | P2 |
| Risco com nível ALTO sem mitigação | cadastro | Responsável | P1 |

---

## Métricas de saúde dos agentes

- Tokens / feature
- Taxa de retrabalho / feature
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + coleta + bump CHANGELOG.
