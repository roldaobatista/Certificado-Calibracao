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

> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPI financeiro/gestão (margem, prazo, aditivos) → **painel-do-dono + e-mail gerente**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — disponibilidade **99.5%**, latência p99 < 1s. Vínculo OS↔Projeto é crítico (impacta custeio real).

| SLI | SLO | Erro orçamento mensal | Origem |
|---|---|---|---|
| Disponibilidade do Gantt | 99.5% | ~3.6h/mês | OTel |
| Latência p95 dashboard projeto | < 800ms (consulta agrega vários módulos) | — | OTel |
| Taxa de erro em vínculo OS↔Projeto | 0% (crítico — afeta custeio) | — | OTel + auditoria |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem notifica | Severidade |
|---|---|---|---|
| Erro vínculo OS↔Projeto > 0 | qualquer ocorrência | page oncall + Auditor Qualidade | P0 |
| Latência dashboard > 3s por 10min | degradação | page oncall | P2 |
| 5xx > 0.5% em 5min | falha API | page oncall | P1 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono semanal** + gerente de projetos. **NÃO acionam pager.**

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| % projetos no prazo (gestão) | Concluídos com data_fim_real ≤ data_fim_prevista (com aditivos) ÷ total | ≥ 70% | Comparação de datas | mensal | painel-do-dono |
| Margem média (lucratividade) | Média margem realizada nos concluídos | ≥ 20% | Σ(receita − custo) / projeto | mensal | painel-do-dono + BI |
| Projetos em zona de risco (gestão) | Custo realizado ≥ 80% previsto sem etapa equivalente | ≤ 10% | Cron diário | semanal | painel-do-dono |
| % aceites no prazo (operação comercial) | Etapas com aceite ≤ 7d após conclusão ÷ total | ≥ 80% | Diff timestamps | mensal | painel-do-dono |
| Tempo médio aprovação aditivo (gestão) | Data aprov − data abertura | ≤ 10 dias úteis `[baseline-em-construcao]` — meta provisória; revisar após 3 projetos concluídos com aditivo | Eventos `Aditivo.Aprovado` | mensal | painel-do-dono |
| Valor médio aditivos (financeiro) | Σ valor aditivos ÷ qtd | benchmark interno | Eventos `Aditivo.Aprovado` | trimestral | relatório trimestral |
| Risco materializado (qualidade) | Riscos cadastrados que viraram ocorrência real no projeto. **Fonte:** tabela `Risco` com campo `estado` enum `[identificado, mitigado, materializado]`. **Fórmula:** `count(Risco.estado=materializado) ÷ count(Risco) por projeto`. **N-mínimo:** ≥ 5 riscos cadastrados no projeto pra calcular. | < 30% | Query agregada por projeto, com cruzamento de eventos `Risco.Materializado` no diário de bordo | trimestral | relatório trimestral |
| Reincidência de cliente (KPI semestral painel-do-dono) | Clientes com ≥ 2 projetos cujo `margem_realizada < 0` (prejuízo). **Fonte:** view `vw_projetos_por_cliente` agregando `margem_realizada` de `Projeto` fechado. **Não é SLO** — métrica observacional pra decisão comercial (renovação, blacklist). | sinal de atenção (sem target rígido) | Dashboard portfólio — listar clientes com 2+ ocorrências em janela 12m | **semestral** | painel-do-dono |
| Schedule variance — SV (prazo) | Variação % entre prazo realizado e prazo planejado (baseline) por projeto concluído. **Fórmula:** `(data_fim_real − data_fim_planejada_baseline) ÷ duracao_planejada × 100`. Positivo = atraso, negativo = adiantamento. | mediana \|SV\| ≤ 10% | Diff timestamps `projeto.cronograma.baseline` vs realizado | mensal | painel-do-dono + gerente |
| Budget variance — BV (custo) | Variação % entre custo realizado e orçado por projeto concluído. **Fórmula:** `(custo_real − custo_orcado) ÷ custo_orcado × 100`. Positivo = estouro, negativo = economia. | mediana \|BV\| ≤ 10% | Σ custos realizados (custeio-real) vs `projeto.orcamento.baseline` | mensal | painel-do-dono + gerente |

**Política de alerta KPI:** variação anômala → **e-mail gerente / Roldão** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| Custo > 80% do previsto sem entrega equivalente | cron diário | e-mail Gerente projeto + Roldão (não-page) |
| Etapa atrasada > 5 dias úteis | cron diário | e-mail responsável (não-page) |
| Aceite pendente > 15 dias | cron diário | e-mail gerente (não-page) |
| Aditivo pendente aprovação > 7 dias | cron diário | e-mail gerente + Roldão (não-page) |
| Risco ALTO sem mitigação | cadastro | e-mail responsável (não-page) |
| Margem média < 15% por 2 meses | mensal | e-mail Roldão (não-page) |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** pós ADR-0001 — destino oncall
- **Painel "Portfolio" (KPIs):** todos projetos com semáforo por prazo e budget — destino Roldão/gerente

---

## Métricas de saúde dos agentes

- Tokens / feature
- Taxa de retrabalho / feature
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + coleta + bump CHANGELOG.
