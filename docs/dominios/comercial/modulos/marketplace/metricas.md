---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Marketplace

> Como saber se o módulo está entregando valor.
>
> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPI de conversão/UX (carrinhos, ticket médio, adoção) → **painel-do-dono**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — disponibilidade **99.5%**. Vitrine é caminho público (cliente final), erro = perda de receita + reputação.

| SLI | SLO | Erro orçamento (mensal) | Origem |
|---|---|---|---|
| Disponibilidade vitrine pública | 99.5% | ~3h40min/mês | OTel |
| Latência TTFB vitrine | p95 < 800ms | — | OTel |
| Latência checkout solicitação | p95 < 1.5s | — | OTel |
| Taxa de erro 5xx | < 0.5% | — | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Vitrine indisponível (5xx > 5%) | impacto reputacional | page oncall + Roldão | P0 |
| Taxa de erro envio solicitação > 5% em 15min | falha no formulário | page oncall + Roldão se persistir | P1 |
| Latência TTFB > 2s por 10min | degradação UX | page oncall | P2 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono semanal/mensal**. **NÃO acionam pager.**

> **Convenção canônica de adoção/uso** (ver `docs/comum/glossario-roldao.md`):
> - **Taxa de adoção inicial** = % novos clientes/tenants usando nos primeiros 30 dias
> - **Taxa de uso recorrente** = % ativos por mês/semana
> - **Taxa de customização** = configurações-sistema
>
> Neste módulo usamos `taxa_uso_recorrente` (escopo: área do cliente no marketplace).

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| Taxa visita → solicitação (conversão) | Solicitações criadas / visitantes únicos | > 2% | analytics + tabela `solicitacao_orcamento` | semanal | painel-do-dono |
| Taxa solicitação → orçamento fechado (conversão) | Orçamentos aprovados / solicitações | > 30% | join solicitação + orçamento + aprovação | mensal | painel-do-dono |
| Tempo médio visita → solicitação (UX) | Pageview → envio | < 4 min | timestamps de eventos | semanal | painel-do-dono |
| Ticket médio do marketplace (financeiro) | Valor médio orçamentos aprovados | acompanhar (sem target) | soma valor / qtd | mensal | painel-do-dono |
| Taxa de adesão a serviço recorrente (adoção) | Assinantes recorrente / clientes ativos | `[baseline-em-construcao]` — monitorar 6 meses sem target rígido; definir meta interna após dado real (target inicial 15% era invenção sem histórico) | tabela `contrato_recorrente` | mensal | painel-do-dono |
| Taxa de uso recorrente — canônico, escopo: área do cliente no marketplace | Ativos logados em 30d / total | > 40% | log de login | mensal | painel-do-dono |
| Taxa de conversão solicitação → orçamento aprovado (UX/conversão) | Substituição da métrica "carrinhos abandonados" (carrinho não é conceito B2B — solicitação é). **Fórmula:** `count(orcamento.status=aprovado AND origem=marketplace) ÷ count(solicitacao_orcamento.origem=marketplace) em janela 30d`. | `[baseline-em-construcao]` — coletar 3 meses pra definir baseline interno; sem target rígido até lá | join `solicitacao_orcamento` × `orcamento` (FK origem) | semanal | painel-do-dono |
| Search → click rate (relevância de busca) | % buscas na vitrine que resultam em clique em item da SERP em 30s | ≥ 40% (busca relevante) | eventos `Busca.Executada` + `Item.Clicado` (mesma `sessao_id`) | semanal | painel-do-dono |
| CAC marketplace vs canal manual (financeiro) | Custo de aquisição médio de cliente vindo do marketplace × custo de aquisição via canal manual (vendedor/indicação) | marketplace ≤ canal manual | (Σ custos marketplace ÷ count clientes novos marketplace) vs (Σ custos vendas ÷ count clientes novos canal manual) | mensal | painel-do-dono |

**Política de alerta KPI:** variação anômala → **e-mail Roldão / dashboard** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| Queda brusca de visitantes (> 30%) em 1h | comparativo hora a hora | dashboard gestor (NÃO page) |
| Conversão solicitação→orçamento abaixo do baseline interno por 2 semanas (após baseline definido) | sinal de UX ruim ou catálogo desatualizado | painel-do-dono + e-mail Roldão |
| Conversão visita→solicitação < 1% em 2 semanas | degradação funil | e-mail Roldão semanal |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** pós ADR-0001 — destino oncall
- **Painel-do-dono KPIs / Funil:** pós ADR-0001 (visita → carrinho → solicitação → orçamento → fechado) — destino Roldão
- **Axiom (logs):** pós ADR-0001

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature.
- Taxa de retrabalho / feature.
- Tempo médio de entrega de US-MKT-*.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta.
- Métrica obsoleta → marcar `@deprecated`.
- Mudança de target → ADR explicando.
