---
owner: roldao
revisado-em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
---

# Métricas do módulo OS

> KPIs de negócio + SLI/SLO técnico. Detalhe operacional em `../../../operacao/observabilidade.md` (a criar — GATE-OBS-OS-1 Wave A).
>
> **Revisado em 2026-05-23 (ADR-0023 + auditoria 10 lentes):** métricas reorientadas por `AtividadeDaOS` em vez de por OS atômica; `tenant_id` declarado como label obrigatório (OBS-002); adicionadas métricas de OS combinada e sync mobile backlog.

---

## KPIs de negócio (por AtividadeDaOS)

Toda métrica carrega `tenant_id` como label/dimensão obrigatória (OBS-002 — INV-OBS-002).

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % atividades no prazo (Onda 6 auditor 5 — A1) | `AtividadeDaOS.CONCLUIDA` até `SLA.prazo_prometido` (entidade SLA — vide `modelo-de-dominio.md`) ÷ total CONCLUIDA no período; agrupável por `SLA.prioridade` | ≥ 85% global; alta/emergencia ≥ 95% | query JOIN `atividade × sla` filtrando `atividade.concluida_at <= sla.prazo_prometido` | semanal |
| Tempo médio PENDENTE→CONCLUIDA por TipoAtividade | Média (em horas úteis) por tipo de atividade | calibracao ≤ 48h; manutencao_corretiva ≤ 24h; manutencao_preventiva ≤ 48h; instalacao ≤ 16h; verificacao_inmetro ≤ 8h; vistoria ≤ 4h | timestamps transições da máquina de estados da atividade | semanal |
| Taxa de retrabalho | OS-filha (reaberta) ÷ total OS CONCLUIDA no período anterior | ≤ 5% | contagem de `os_origem_id` preenchido | mensal |
| Taxa de NC em calibração | Atividades tipo=calibracao com estado=NAO_CONFORME ÷ total atividades tipo=calibracao | ≤ 8% | máquina de estados da atividade + estado terminal NAO_CONFORME | mensal |
| Taxa de NC por padrão | Atividades NC ÷ total atividades por padrão usado (rolling 90d) | ≤ 5% por padrão | join atividade × `PadraoUsado` | mensal |
| Taxa de NC por cliente | Atividades NC ÷ total atividades por cliente (rolling 90d) | tendência ↓ | join atividade × `OS.cliente_id` | mensal |
| Taxa de NC por executor | Atividades NC ÷ total atividades por `tecnico_executor_id` (rolling 90d) | identificar outlier | join atividade × executor | mensal |
| % OS canceladas | CANCELADA ÷ total OS criadas no período | ≤ 10% | máquina de estados OS | semanal |
| Tentativas de conclusão bloqueadas por checklist | Por TipoAtividade | tendência ↓ | log de bloqueio | semanal |
| Tempo de sync mobile→servidor | p95 do delay entre conclusão offline e chegada no servidor | ≤ 5min (com rede) | timestamp evento vs `client_event_created_at` | semanal |
| **Backlog de sync mobile** (TEMA-OBS-5) | Atividades concluídas offline pendentes de sync no momento T | gauge — alerta se > 20 atividades em 1 device por > 4h | endpoint /heartbeat mobile reporta backlog | tempo real |
| **% OS combinadas (ADR-0023)** | OS com ≥2 atividades ÷ total OS criadas | métrica de saúde — sem target inicial | count atividades por OS | mensal |
| **Tempo médio entre atividades** | `atividade_N+1.iniciada_at − atividade_N.concluida_at` na mesma OS | ≤ 4h (caso manutenção+calibração) | sequence query | mensal |

---

## SLI/SLO técnico

Todas SLI também carregam `tenant_id` como dimensão.

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade API OS | 99.9% | 43min/mês |
| Latência p95 GET /os | < 500ms | — |
| Latência p95 POST /os | < 1s | — |
| Latência p95 POST /os/{id}/atividades/{aid}/iniciar | < 800ms | — |
| Latência p95 POST /os/{id}/atividades/{aid}/concluir | < 1.2s | — |
| Taxa de erro 5xx | < 0.1% | — |
| Perda de dado mobile→servidor | 0% | absoluto (zero tolerância — ADR-0004) |

---

## Dashboards canônicos (por persona)

> TEMA-OBS-2 pendente — implementar em Wave A após Grafana real plugar. Esqueleto:

| Persona | Painel | Métricas-chave |
|---|---|---|
| P-OP-04 gerente operacional | "Fila operacional" | OS abertas por estado + atividades por estado por técnico + atividades atrasadas + redistribuição rápida |
| P-OP-02 metrologista | "Fila de calibração" | atividades tipo=calibracao em PENDENTE/EM_EXECUCAO + revisão pendente + NC abertas + padrão vencendo |
| RT signatário (P-METR-02) | "2ª conferência pendente" | calibrações aguardando 2ª conferência + tempo desde 1ª revisão + SLA |
| P-OP-03 atendente | "Recepção hoje" | OS criadas hoje + tempo médio de cadastro + AceiteAtividade pendente |
| P-OP-01 técnico de campo | "Minhas atividades" | atividades AGENDADA do dia + sync status + backlog offline |

- **Grafana:** [link a definir pós ADR-0001]
- **Axiom (logs):** [link]

---

## Alertas

Toda alerta carrega `tenant_id` na notificação (OBS-002).

| Alerta | Quando dispara | Notificado | Severidade | Ação acionável |
|---|---|---|---|---|
| Sync mobile parou | > 30min sem evento de sync de um device ativo | Watchdog → agente | P2 | verificar conectividade do técnico; reagendar |
| Backlog mobile elevado | device com > 20 atividades concluídas offline há > 4h | gerente operacional | P2 | priorizar sync; risco de perda |
| Pico de OS canceladas | > 20% em 1 dia | gerente operacional | P3 | analisar razões + dashboard cliente |
| Atividade travada em EM_EXECUCAO | > 72h sem transição | gerente operacional | P3 | reatribuir técnico ou cancelar |
| OS combinada parada por gate de sequência | atividade tipo=calibracao em PENDENTE há > 24h e atividade tipo=manutencao_corretiva na mesma OS em EM_EXECUCAO | gerente operacional | P3 | acelerar manutenção ou desabilitar gate |
| Atividade tipo=calibracao em NAO_CONFORME | qualquer NC marcada | RT + gerente | P2 | abrir fluxo CAPA (TEMA-B.2 pendente) |
| Reincidência NC por padrão | mesmo padrão com > 5 NC em 30d | RT | P1 | calibração externa antecipada do padrão |

---

## Métricas de saúde dos agentes neste módulo

- Tokens consumidos / US-OS-NNN entregue
- Taxa de retrabalho IA (US reaberta após "concluída")
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + configurar coleta + bump CHANGELOG. Após Foundation F-C entrar (Grafana plugado), promover SLOs a métricas regulatórias (CGCRE) onde aplicável.
