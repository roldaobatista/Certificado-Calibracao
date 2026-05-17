---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Métricas do módulo Chamados

> KPIs negócio + SLI/SLO técnico.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo médio de triagem | Média (segundos) entre criação e estado TRIADO | ≤ 30s (p50); ≤ 60s (p95) | timestamps de transição | semanal |
| % SLA cumprido | Chamados resolvidos dentro do prazo SLA ÷ total fechados | ≥ 90% | comparar `fechado_at` × `sla_alvo_at` | semanal |
| % chamados que viram OS | Chamados com `os_id` ≠ null ÷ total | informativa (estabilizar tendência) | flag conversão | mensal |
| % duplicados detectados | Sugestões aceitas pela atendente ÷ duplicados que existiam | ≥ 80% | comparar sugestões × confirmações humanas | mensal |
| % SLA escalado pra gerente | Chamados que bateram 100% do SLA antes de fechar ÷ total | ≤ 5% | flag escalonamento | semanal |
| Chamados por canal | Distribuição WhatsApp / tel / portal / email | informativa | enum canal_origem | mensal |
| Taxa de fechamento sem OS | FECHADO + `os_id=null` ÷ total fechado | informativa | flag | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade API Chamados | 99.9% | 43min/mês |
| Latência p95 POST /chamados | < 500ms | — |
| Latência p95 detecção duplicado | < 300ms (sincrono na UI) | — |
| Job de escalonamento SLA | execução de minuto em minuto, lag p99 < 2min | — |

---

## Dashboards

- **Grafana:** mapa de calor de SLA (chamados aproximando do limite por cor)
- **Axiom:** logs de escalonamento

---

## Alertas

| Alerta | Quando dispara | Notificado | Severidade |
|---|---|---|---|
| Job de SLA travou | > 5min sem execução do cron | Watchdog → agente | P1 |
| Pico de chamados | > 200% da média/hora | gerente operacional | P3 |
| Cliente abriu 3 chamados em 24h | sinal de cliente insatisfeito | gerente + comercial | P3 |

---

## Métricas de saúde dos agentes neste módulo

- Tokens / US-CH-NNN entregue
- Tempo médio entrega de US
- Retrabalho IA

---

## Como evolui

Métrica nova → adicionar + configurar coleta.
