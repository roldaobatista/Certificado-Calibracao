---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Suporte SaaS

> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPIs de community/satisfação (engajamento roadmap, CSAT, deflexão) → **painel-do-dono / e-mail Roldão**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — mas portal de suporte é caminho crítico para tenants pagantes, então elevado para **99.9%** (alinhado com Financeiro).

| SLI | SLO | Erro orçamento (mensal) | Origem |
|---|---|---|---|
| Disponibilidade do portal de suporte | 99.9% | 43min/mês | OTel |
| Latência abertura de ticket p95 | < 1s | — | OTel |
| Latência busca BC p95 | < 500ms | — | OTel |
| Latência resposta IA chat p95 | < 3s | — | OTel + LiteLLM |
| Taxa de erro em criação de ticket | < 0.1% | — | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Portal indisponível (5xx > 5%) | falha API | page oncall + Roldão | P0 |
| TPR > 2x target | degradação SLA técnico | page oncall + equipe suporte | P2 |
| Acesso remoto > 4h sem revogação | sessão suspeita | page oncall + tenant admin + auditoria | P1 |
| Manutenção sem aviso T-24h | violação processo | page oncall + Roldão | P1 |
| Latência chat IA > 8s por 10min | degradação LLM | page oncall | P2 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono** + relatório trimestral Roldão. **NÃO acionam pager.**

> **Convenção canônica de tempo** (ver `docs/comum/glossario-roldao.md`):
> - **TPR** (Tempo Médio de Primeira Resposta) = abertura → 1ª resposta humana/IA
> - **TMA** (Tempo Médio de Atendimento) = início efetivo → encerramento da interação
> - **TMR** (Tempo Médio de Resolução) = abertura → fechamento final
>
> Neste módulo usamos TPR e TMR (escopo: ticket de suporte SaaS).

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| Taxa de deflexão (BC eficácia) | % consultas resolvidas via BC sem ticket | > 40% | eventos "resolveu via artigo" / consultas | semanal | painel-do-dono |
| Cumprimento de SLA (operação suporte) | % tickets resolvidos dentro do SLA do plano | > 95% | `resolved_em ≤ deadline` | semanal | painel-do-dono |
| CSAT (satisfação) | Avaliação pós-ticket (1-5) | > 4.5 | pesquisa pós-fechamento | mensal | painel-do-dono + relatório Roldão |
| TPR — canônico, escopo: ticket | min abertura → 1ª resposta humana/IA | < 30min P3, < 4h P1 (Pro) | observabilidade | diário | painel-do-dono |
| TMR — canônico, escopo: ticket | abertura → resolução final (inclui fila + execução + retorno) | varia por categoria/plano | observabilidade | semanal | painel-do-dono |
| Tickets por tenant ativo (qualidade produto) | total/mês | < 3/tenant | query | mensal | painel-do-dono |
| Reincidência de bug (qualidade produto) | mesmo bug reportado por > 1 tenant | < 5 reincidências/mês | agrupamento por tag | semanal | painel-do-dono + engenharia |
| Engajamento de roadmap (community) | % usuários que votaram em ≥1 item/trim | > 20% | tracking de voto | trimestral | relatório trimestral Roldão |
| Aceitação de manutenção (community) | % tenants sem reclamação pós-aviso | > 95% | tickets pós-manutenção / total | por janela | painel-do-dono |

**Política de alerta KPI:** variação anômala → **e-mail Roldão / equipe** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| Backlog de tickets P1 > 10 | acumulando | e-mail equipe suporte + Roldão (não-page; vira P1 técnico se SLA viola) |
| SLA violado em > 5% dos tickets na semana | tendência negativa | e-mail Roldão semanal (não-page) |
| CSAT < 4.0 em janela 7 dias | queda satisfação | e-mail Roldão semanal (não-page) |
| Engajamento roadmap < 10% trimestral | community fraca | relatório trimestral Roldão (não-page) |
| Deflexão BC < 30% por 1 mês | BC desatualizada | e-mail Roldão + equipe BC (não-page) |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** painel `suporte-saas` operacional — destino oncall
- **Painel-do-dono KPIs:** "Suporte — CSAT, deflexão, engajamento" — destino Roldão
- **Axiom:** filtro `module=suporte-saas`

---

## Métricas de saúde dos agentes (suporte IA)

- % tickets resolvidos só pela IA (sem handoff).
- Taxa de handoff IA→humano por categoria.
- Tokens consumidos por ticket atendido.
- Acurácia de classificação automática (categoria/prioridade).

---

## Como evolui

Métrica nova → coleta + CHANGELOG. Mudança de target → ADR.
