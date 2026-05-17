---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Métricas do módulo OS

> KPIs de negócio + SLI/SLO técnico. Detalhe operacional em `../../../operacao/observabilidade.md` (quando criado).

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % OS no prazo | OS CONCLUIDA até a data prometida ÷ total CONCLUIDA no período | ≥ 85% | query banco filtrando `concluida_at <= prazo_prometido` | semanal |
| Tempo médio RASCUNHO→CONCLUIDA | Média (em horas úteis) por tipo de OS | calibração ≤ 48h; manutenção ≤ 24h | timestamp transições da máquina de estados | semanal |
| Taxa de retrabalho | OS-filha (reaberta) ÷ total CONCLUIDA no período anterior | ≤ 5% | contagem de `os_origem_id` preenchido | mensal |
| Taxa de NC | OS de calibração com NC marcada ÷ total OS calibração | ≤ 8% | flag `nao_conformidade=true` | mensal |
| % OS canceladas | CANCELADA ÷ total criadas no período | ≤ 10% | máquina de estados | semanal |
| OSs sem checklist completo bloqueando conclusão | Tentativas de conclusão bloqueadas por checklist | tendência ↓ | log de bloqueio | semanal |
| Tempo de sync mobile→servidor | p95 do delay entre conclusão offline e chegada no servidor | ≤ 5min (com rede) | timestamp evento vs timestamp criação local | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade API OS | 99.9% | 43min/mês |
| Latência p95 GET /os | < 500ms | — |
| Taxa de erro 5xx | < 0.1% | — |
| Perda de dado mobile→servidor | 0% | absoluto (zero tolerância — ADR-0004) |

---

## Dashboards canônicos

- **Grafana:** [link a definir pós ADR-0001]
- **Axiom (logs):** [link]

---

## Alertas

| Alerta | Quando dispara | Notificado | Severidade |
|---|---|---|---|
| Sync mobile parou | > 30min sem evento de sync de um device ativo | Watchdog → agente | P2 |
| Pico de OS canceladas | > 20% em 1 dia | gerente operacional | P3 |
| OS travada em EM_EXECUCAO | > 72h sem transição | gerente operacional | P3 |

---

## Métricas de saúde dos agentes neste módulo

- Tokens consumidos / US-OS-NNN entregue
- Taxa de retrabalho IA (US reaberta após "concluída")
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
