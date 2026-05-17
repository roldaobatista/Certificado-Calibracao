---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Custeio Real

> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPI financeiro (margem, deficitárias, retrabalho) → **painel-do-dono + e-mail Roldão**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **Financeiro** em `docs/operacao/observabilidade.md` — disponibilidade **99.95%**, latência p99 < 2s, erro 5xx < 0.1%. Apuração é caminho crítico (impacta painel financeiro do dono).

| SLI | SLO | Erro orçamento (mensal) | Origem |
|---|---|---|---|
| Apuração consome evento `Operacao.OSEncerrada` em <5min | 99% | — | fila procrastinate |
| Idempotência da apuração (re-execução = mesmo resultado) | 100% | 0 | testes contrato |
| Latência relatório agregado p95 | < 5s | — | OTel |
| Disponibilidade dashboards margem | 99.9% | 43min/mês | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem | Severidade |
|---|---|---|---|
| Apuração não rodou (lag >1h) | evento consumido com atraso | page oncall + Watchdog → Roldão | P1 |
| Idempotência quebrada (re-exec = resultado diferente) | qualquer ocorrência | page oncall + Auditor Qualidade | P0 |
| Dashboard margem indisponível > 5min | falha API | page oncall | P1 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono semanal/mensal** + gestor operacional. **NÃO acionam pager.**

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| % OSs com custo apurado em ≤24h (operação financeira) | OSs com custo real calculado ≤24h após encerramento | ≥ 95% | (apuradas ≤24h) ÷ (encerradas) | semanal | painel-do-dono |
| % OSs deficitárias revisadas em ≤7d (gestão) | OSs deficitárias com intervenção gestor ≤7d | ≥ 90% | (deficitárias revisadas) ÷ (detectadas) | mensal | painel-do-dono |
| Aderência apuração (qualidade do cálculo) | % aderência custo sistema vs revisão manual amostral | ≥ 95% | amostra mensal | mensal | painel-do-dono |
| Margem real média da empresa (lucratividade) | Margem % consolidada do mês | tendência crescente | Σ margem / Σ receita | mensal | painel-do-dono + BI |
| % OSs deficitárias (financeiro) | OSs encerradas com margem negativa | ≤ 10% | (margem<0) ÷ (encerradas) | mensal | painel-do-dono |
| % retrabalho por técnico (qualidade) | Horas retrabalho ÷ horas totais técnico | ≤ 5% | calculado | mensal | painel-do-dono |
| % garantia por tipo de serviço (qualidade) | Custo garantia ÷ receita do serviço | ≤ 8% | calculado | mensal | painel-do-dono |
| Gross Margin por segmento de cliente (lucratividade) | Margem bruta % consolidada por segmento (porte, setor, plano contratual) | benchmark interno após 6m | Σ(receita−custo) por segmento ÷ Σ receita do segmento; segmento de `cliente.segmento` | mensal | painel-do-dono + BI |
| Forecast accuracy (precisão orçamentária) | 1 − \|orçado − real\| ÷ orçado, agregado por categoria (custo, receita) | ≥ 90% (≤10% de desvio) | comparação `orcamento.valor_previsto` × custeio realizado por período | mensal | painel-do-dono |

**Política de alerta KPI:** variação anômala → **e-mail Roldão / gestor** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| OS deficitária encerrada | margem real < threshold do tenant | e-mail gestor operacional (não-page) |
| Cluster de OSs deficitárias mesmo cliente | ≥3 deficitárias / 30d mesmo cliente | e-mail Roldão + gestor (não-page) |
| Custo apurado divergente da revisão manual >5% | qualidade caiu | e-mail Roldão (não-page) |
| Margem média caindo 2 meses seguidos | tendência | e-mail Roldão mensal |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** pós ADR-0001 — destino oncall
- **Painel-do-dono "Custeio Real" (KPIs):** margem do mês, OSs deficitárias, % retrabalho — destino Roldão
- **Axiom:** filtro `module:custeio-real`

---

## Métricas de saúde dos AGENTES

(Família 5 Governança IA)

- Tokens / feature
- Taxa de retrabalho de feature do módulo
- Tempo médio entrega de US

---

## Como esta lista evolui

- Métrica nova → adicionar + coleta + CHANGELOG.
- Mudança de target → ADR.
