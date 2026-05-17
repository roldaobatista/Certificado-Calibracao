---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Billing SaaS

> Como saber se este módulo está entregando valor. KPIs de negócio + métricas técnicas.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| MRR | Receita recorrente mensal (soma das assinaturas ativas normalizadas a mês) | crescimento mês a mês | soma `assinatura.valor_mensal_normalizado` WHERE status=ativa | semanal |
| Churn mensal | % de assinaturas que cancelaram no mês / ativas no início | ≤ 3% | (canceladas/mês) ÷ (ativas início mês) | mensal |
| Taxa de conversão trial→pago | % de trials que viraram pagantes | ≥ 30% | (trials convertidos) ÷ (trials encerrados) | mensal |
| Taxa de inadimplência | % de faturas vencidas há >7 dias | ≤ 5% | faturas atrasadas ÷ faturas emitidas no período | semanal |
| ARPU | Average Revenue Per User (tenant) — MRR ÷ tenants ativos | crescimento | MRR ÷ count(tenants ativos) | mensal |
| LTV | Lifetime Value estimado (ARPU ÷ churn) | crescimento | calculado | mensal |
| Taxa de upgrade | % de tenants que fizeram upgrade no período | medir baseline | count(upgrades) ÷ ativos | mensal |
| Taxa de downgrade | % de tenants que fizeram downgrade no período | ≤ 2% | count(downgrades) ÷ ativos | mensal |

---

## SLI/SLO técnico (operação)

Detalhes em `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade painel billing | 99.9% | 43min/mês |
| Job de cobrança não duplica | 100% (zero duplicações) | 0 |
| Webhook gateway processado em <30s | 99% | — |
| Latência painel de uso p95 | < 500ms | — |

---

## Dashboards canônicos

- **Grafana:** dashboard "Billing SaaS" — MRR, churn, faturas em aberto, falhas de webhook.
- **Axiom (logs):** filtro `module:billing-saas`.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Webhook gateway falhou >5x | mesmo evento falha 5x | Watchdog → agente → Roldão | P1 |
| Job de cobrança não rodou | esperava rodar e não rodou (heartbeat) | Watchdog → Roldão direto | P0 |
| Tenant suspenso por engano (reativação manual ≥3 em 24h) | possível bug de bloqueio | Operador comercial + Roldão | P1 |
| Churn semanal acima de baseline + 2 desvios | anomalia | Roldão | P2 |
| Trial expirando hoje sem método pagamento | informativo | tenant (email) | P3 |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA)

- Tokens consumidos / feature do módulo
- Taxa de retrabalho / feature
- Tempo médio de entrega de US

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR explicando.
