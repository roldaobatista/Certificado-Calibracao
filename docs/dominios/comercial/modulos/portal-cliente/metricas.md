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

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % clientes ativos com acesso/mês | Clientes únicos que logaram no mês ÷ total de clientes ativos do tenant | ≥ 40% | log de login | mensal |
| % orçamentos aprovados via portal | Orçamentos aprovados pelo portal ÷ total aprovados (portal + manual) | ≥ 60% | evento `OrcamentoAprovadoPeloCliente` vs aprovações internas | mensal |
| Redução de chamados pedindo "status" | Variação % de chamados/WhatsApp tipo "como tá minha OS" antes vs depois | ≥ -30% | pesquisa qualitativa pós-3 meses + tags de chamados | trimestral |
| Tempo médio aprovação de orçamento | Mediana de horas entre envio do orçamento e aprovação | ≤ 48h | timestamps no evento | semanal |
| NPS do portal | Pesquisa pós-uso (1 pergunta + comentário opcional) | ≥ 40 | módulo pesquisa | trimestral |
| Taxa de boletos quitados via 2ª via portal | 2ª via portal pagos ÷ total 2ª via emitidas | ≥ 70% | reconciliação Financeiro | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade portal | 99,5% | ~3h36min |
| Latência p95 dashboard cliente | < 2s | — |
| Latência p95 mobile em 3G | < 3s | — |
| Taxa de erro 5xx | < 0,5% | — |
| Sucesso de login (login bem-sucedido ÷ tentativas legítimas) | ≥ 99% | — |

---

## Dashboards canônicos

- **Grafana:** link a definir pós-ADR-0001
- **Axiom (logs):** link a definir

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Tentativa de cross-tenant detectada | acesso retorna dado de outro tenant_id | Auditor Segurança + Roldão | P0 |
| Spike de login bloqueado | > N contas bloqueadas/hora | Atendente do tenant + Segurança | P1 |
| Webhook de notificação falhou 5x | provider externo (e-mail/WhatsApp) caiu | Watchdog → operador | P2 |
| Aprovação de orçamento sem evento WORM | rastreabilidade falhou | Auditor Qualidade | P1 |
| Tempo p95 acima do SLO | performance | Operação | P2 |

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
