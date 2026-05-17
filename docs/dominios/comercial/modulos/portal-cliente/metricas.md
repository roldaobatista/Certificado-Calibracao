---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
relacionados:
  - docs/AGENTS.md
---

# Métricas do módulo Portal do Cliente

> Como saber se o Portal do Cliente está entregando valor (e descongestionando o tenant).
>
> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPI de negócio (NPS, adoção, engajamento) → **painel-do-dono + e-mail Roldão**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — disponibilidade **99.5%**, latência p99 < 1s. Portal cliente é caminho externo (cliente final do tenant), então erro/lentidão = reputacional.

| SLI | SLO | Erro orçamento (mensal) | Origem |
|---|---|---|---|
| Disponibilidade portal | 99.5% | ~3h36min | OTel |
| Latência p95 dashboard cliente | < 2s | — | OTel |
| Latência p95 mobile em 3G | < 3s | — | OTel |
| Taxa de erro 5xx | < 0.5% | — | OTel |
| Sucesso de login (login OK ÷ tentativas legítimas) | ≥ 99% | — | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Tentativa de cross-tenant detectada | acesso retorna dado de outro tenant_id | page oncall + Auditor Segurança + Roldão | P0 |
| Spike de login bloqueado | > N contas bloqueadas/hora | page oncall + Atendente do tenant | P1 |
| Webhook de notificação falhou 5x | provider externo (e-mail/WhatsApp) caiu | page oncall (operador) | P2 |
| Aprovação de orçamento sem evento WORM | rastreabilidade falhou | page oncall + Auditor Qualidade | P1 |
| Tempo p95 acima do SLO | performance | page oncall (operação) | P2 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono semanal** + relatório trimestral Roldão. **NÃO acionam pager.**

> **Convenção canônica de adoção/uso** (ver `docs/comum/glossario-roldao.md`):
> - **Taxa de adoção inicial** = % novos clientes/tenants usando nos primeiros 30 dias
> - **Taxa de uso recorrente** = % ativos por mês/semana (engajamento contínuo)
> - **Taxa de customização** = % tenants que customizaram (configurações-sistema)
>
> Neste módulo usamos `taxa_uso_recorrente` (engajamento mensal do cliente final) e `feature_adoption_curve` (adoção por feature).

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| Taxa de uso recorrente — canônico, escopo: cliente final / mês | Clientes únicos logados no mês ÷ total ativos | ≥ 40% | log de login | mensal | painel-do-dono |
| % orçamentos aprovados via portal (conversão) | Aprovados portal ÷ total aprovados. **Fórmula:** `count(orcamento.aprovado_em_portal=true) ÷ count(orcamento.status=aprovado)`. | `[baseline-em-construcao]` — ≥ 0% no go-live (nenhuma base prévia); meta interna de ≥ 60% após 6 meses pós-go-live, revisar com dado real | evento `OrcamentoAprovadoPeloCliente` + flag `aprovado_em_portal` | mensal | painel-do-dono |
| Redução de chamados pedindo "status" (deflexão) | Variação % de chamados "como tá minha OS" | ≥ -30% | pesquisa qualitativa + tags | trimestral | relatório trimestral |
| Tempo médio aprovação de orçamento | Mediana de horas entre envio e aprovação | ≤ 48h | timestamps no evento | semanal | painel-do-dono |
| NPS do portal (satisfação cliente final) | Pesquisa pós-uso (1 pergunta + comentário) | ≥ 40 | módulo pesquisa | trimestral | relatório trimestral Roldão |
| Taxa de boletos quitados via 2ª via portal (conversão financeira) | 2ª via portal pagos ÷ total 2ª via | ≥ 70% | reconciliação Financeiro | mensal | painel-do-dono |
| Session duration (proxy UX) | Mediana de tempo entre login e logout/inatividade (>30min) | ≥ 4 min (engajamento mínimo) | timestamps `sessao.inicio`/`sessao.fim`; analytics frontend | semanal | painel-do-dono |
| Bounce rate por seção (UX) | % sessões que abrem 1 página da seção (orçamentos, OSs, financeiro, certificados) e saem em <30s | ≤ 30% por seção | analytics + tracking de tempo na rota | mensal | painel-do-dono |
| Feature adoption curve (adoção) | % clientes ativos que usaram cada feature-chave (aprovar orçamento, baixar certificado, pagar 2ª via, abrir chamado) nos últimos 30d | ≥ 50% das features-chave usadas por ≥ 30% dos ativos em 90d | eventos `Feature.Usada` por feature_id × cliente único | mensal | painel-do-dono |

**Política de alerta KPI:** variação anômala → **e-mail Roldão** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| NPS caindo | Queda > 10 pontos trimestre/trimestre | e-mail Roldão trimestral |
| Adoção caindo | < 30% por 2 meses seguidos | e-mail Roldão mensal |
| Deflexão piorando | Chamados "status" subindo trimestre/trimestre | relatório trimestral |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** link pós-ADR-0001 — destino oncall
- **Painel-do-dono KPIs:** link pós-ADR-0001 — destino Roldão
- **Axiom (logs):** link pós-ADR-0001

---

## Métricas de saúde dos AGENTES neste módulo

(Família 5 Governança IA)

- Tokens consumidos / feature Portal nova
- Taxa de retrabalho / US-POR-*
- Tempo médio de entrega de US-POR-*

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR explicando.
