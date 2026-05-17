---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
relacionados:
  - docs/AGENTS.md
  - docs/novas funcionalidades.txt
---

# Métricas do módulo BI

> Como saber se o módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Adoção do dashboard executivo | % de donos (P1) que abriram o dashboard ≥ 4 vezes/semana | ≥ 70% | log de acesso à tela home | semanal |
| Relatórios customizados criados/cliente/mês | Nº de relatórios construídos no builder no período | ≥ 1 | tabela `bi_relatorio` por tenant | mensal |
| Envios agendados ativos / cliente | Quantos relatórios cada tenant tem agendados | ≥ 1 | tabela `bi_agendamento` | mensal |
| Erros silenciosos em KPI (divergência) | Casos em que KPI diverge da fonte transacional | 0 (zero) | reconciliação automática diária | diário |
| % de dashboards públicos com proteção (senha OU expiração) | Quantos links públicos têm pelo menos 1 proteção ativa | ≥ 95% | tabela `bi_link_publico` | semanal |

---

## SLI/SLO técnico (operação)

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do módulo BI | 99,5% | ~3h36min/mês |
| Latência p95 dashboard executivo | < 2s | — |
| Latência p95 builder de relatório (≤ 100k linhas) | < 5s | — |
| Defasagem máxima dashboard executivo | ≤ 15 min | — |
| Defasagem máxima operacional ao vivo | ≤ 1 min | — |
| Taxa de erro 5xx em endpoints BI | < 0,5% | — |

---

## Dashboards canônicos

- **Grafana:** link a definir pós-ADR-0001
- **Axiom (logs):** link a definir pós-ADR-0001

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| KPI executivo defasado > 30 min | job de materialização atrasou | Watchdog → agente → Roldão se persistir | P2 |
| Link público acessado e dados vazios | possível falha de filtro tenant | Auditor Segurança + Roldão | P1 |
| Envio agendado falhou 3x seguidas | falha de e-mail / geração de PDF | analista responsável (tenant) | P3 |
| Divergência KPI vs fonte transacional | reconciliação detectou diferença | Auditor Qualidade | P1 |
| Tentativa de acesso a métrica sem RBAC | possível abuso interno | Auditor Segurança | P2 |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA)

- Tokens consumidos / feature BI nova
- Taxa de retrabalho / US-BI-*
- Tempo médio de entrega de US-BI-*

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → marcar `@deprecated`.
- Mudança de target → ADR explicando.
