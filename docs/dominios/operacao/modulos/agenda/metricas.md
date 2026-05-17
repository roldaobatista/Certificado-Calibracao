---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Métricas do módulo Agenda

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % ocupação técnico | Horas alocadas em eventos ÷ horas úteis disponíveis | 70-85% (saudável); > 95% = sobrecarga; < 50% = ocioso | sum slots ocupados / capacidade | semanal |
| Conflitos bloqueados | Tentativas de agendamento rejeitadas por conflito | informativa (tendência ↓ indica disciplina) | log de validação | semanal |
| Violações INV-020 bloqueadas | Tentativas de agendamento que feririam Lei 13.103 | informativa; > 5/semana = revisar treinamento | hook INV-020 conta | semanal |
| Reagendamentos por OS | Média de transições de slot por OS antes de CONCLUIDA | ≤ 1.3 | contar eventos de move por os_id | mensal |
| Tempo médio para reagendar | Segundos entre clique do gerente e notificação enviada ao cliente | ≤ 60s | timestamp | semanal |
| % OS no slot original | OS concluída no slot inicialmente alocado ÷ total CONCLUIDA | ≥ 70% | comparar slot inicial × slot na conclusão | mensal |
| Deslocamento médio entre OS | Minutos médios entre fim e início da próxima OS do mesmo técnico | informativa (otimização rota) | sum tempos calculados | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento |
|---|---|---|
| Disponibilidade API Agenda | 99.9% | 43min/mês |
| Latência p95 validação INV-020 | < 200ms (UI fluida no drag) | — |
| Latência p95 GET /agenda/semana (20 técnicos) | < 800ms | — |
| Job recorrência | execução diária; falha = P1 | — |

---

## Dashboards

- **Grafana:** % ocupação por técnico + heatmap semana
- **Axiom:** logs de validação INV-020

---

## Alertas

| Alerta | Quando dispara | Notificado | Severidade |
|---|---|---|---|
| Job recorrência falhou | cron diário não rodou | Watchdog → agente | P1 |
| Técnico passou 95% ocupação | 3 dias seguidos | gerente | P3 |
| Violação INV-020 em produção (não bloqueada) | falha do hook | dev + DPO + auditor | P0 |
| Cluster de conflitos em 1 técnico | > 10 rejeições/dia | gerente + RH | P3 |

---

## Métricas de saúde dos agentes

- Tokens / US-AG-NNN entregue
- Tempo médio entrega de US

---

## Como evolui

Métrica nova → adicionar + configurar coleta.
