---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Precificação

> Como saber se o módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % orçamentos com margem ≥ alvo | orçamentos cuja margem realizada ≥ margem-alvo / total | > 70% | join orçamento + custeio-real | mensal |
| Gap margem alvo vs realizada | margem-alvo − margem média realizada | ≤ 5pp | dashboard de margem | mensal |
| % descontos aprovados | aprovados / total solicitados | > 60% (calibração saudável) | tabela `aprovacao_desconto` | mensal |
| Tempo médio de aprovação | timestamp aprovação − timestamp pedido | < 4h úteis | tabela `aprovacao_desconto` | semanal |
| % orçamentos bloqueados por preço mínimo | tentativas de salvar abaixo do mínimo bloqueadas / total | acompanhar (sinaliza pressão de mercado) | log de bloqueio | mensal |
| Margem média realizada | média ponderada da margem dos orçamentos fechados | ≥ 18% (default; configurável por tenant) | dashboard | mensal |
| Receita salva por bloqueio de preço mínimo | valor estimado evitado em prejuízo | acompanhar (story-telling) | (custo − preço solicitado) × qtd bloqueada | mensal |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do motor de precificação | **99.9%** | ~43min/mês |
| Latência cálculo de preço (p95) | < 200ms | — |
| Latência cálculo de preço (p99) | < 500ms | — |
| Taxa de erro 5xx | < 0.2% | — |

> **Justificativa do SLO 99.9%** (acima do default 99.5% do domínio Comercial): motor de precificação é **bloqueador de fluxo de caixa** — sem ele, orçamentos não fecham e não viram OS/fatura. Criticidade intermediária entre CRM puro (99.5%) e Financeiro (99.95%). SLO anterior (99.7%) era valor "inventado" sem ancoragem na tabela canônica de `docs/operacao/observabilidade.md`.

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.
- **Dashboard de margem:** ranking de itens/clientes/vendedores por margem realizada.
- **Funil de aprovação:** pedidos abertos, aprovados, negados, tempo médio.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Orçamento abaixo da margem mínima salvo | margem < piso | gestor de pricing | P2 |
| Pedido de aprovação sem resposta > 24h úteis | SLA estourado | aprovador + gestor | P2 |
| Latência cálculo > 500ms (p99) por 15min | impacto na UX | watchdog → agente | P1 |
| Motor indisponível (5xx > 1%) | bloqueia orçamento | watchdog → agente → Roldão | P0 |
| Tabela publicada com erro de fórmula | regra inválida | gestor | P1 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / feature.
- Taxa de retrabalho / feature.
- Tempo médio de entrega de US-PRC-*.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
