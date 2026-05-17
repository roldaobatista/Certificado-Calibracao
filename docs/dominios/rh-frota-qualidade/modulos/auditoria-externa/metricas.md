---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Auditoria Externa

> Como saber se o módulo está reduzindo risco de perda de certificação.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % auditorias sem NC maior | Auditorias concluídas com 0 não-conformidade maior | ≥80% | auditorias_sem_nc_maior / total | anual |
| Tempo médio fechamento NC menor | Diff entre data NC e data aprovação fechamento | ≤30 dias | média(fechamento − abertura) | trimestral |
| Tempo médio fechamento NC maior | Idem para NC maior | ≤60 dias | média | trimestral |
| % docs exigidos vigentes | Documentos cadastrados como exigidos com status válido | 100% | vigentes / total | semanal |
| % requisitos com evidência válida (norma X) | Cláusulas com evidência não-vencida | ≥95% | por norma | mensal |
| Aderência prazos pré-auditoria | % evidências entregues antes do prazo | ≥90% | entregues_no_prazo / total | mensal |
| Reincidência de NC | % NCs que reaparecem em auditorias posteriores | ≤5% | NCs_reincidentes / total | anual |

---

## SLI/SLO técnico

Detalhes em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.5% | ~3h40min |
| Latência p95 painel prontidão | ≤2s | — |
| Latência p95 carregar checklist | ≤1s | — |
| Falha em alerta de doc vencido | 0 (alerta deve disparar 100% das vezes) | — |

---

## Dashboards canônicos

- **Painel de prontidão** (a definir pós ADR-0001) — semáforo por norma.
- **Painel histórico de auditorias** — séries temporais NCs maior/menor.
- **Grafana técnico** — saúde da API e jobs de alerta.

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Doc exigido vencido | Vencimento atingido | RQ + responsável do doc | P1 |
| NC maior próxima de vencer plano de ação | 7 dias antes do prazo | RQ + responsável + diretoria | P0 |
| NC menor próxima de vencer plano | 3 dias antes do prazo | RQ + responsável | P1 |
| Auditoria <7 dias e <90% checklist completo | Janela crítica | RQ + diretoria | P1 |
| Auditoria <30 dias e <60% checklist completo | Janela amarela | RQ | P2 |
| Painel de prontidão vermelho | Qualquer norma ativa fica vermelha | RQ + diretoria | P1 |

---

## Métricas de saúde dos AGENTES neste módulo

- Tokens consumidos / drill executado pelo agente Família 5 Qualidade.
- Taxa de gaps detectados pelo drill vs gaps que apareceriam na auditoria real (avalia precisão do agente).
- Tempo médio do drill vs janela disponível antes da auditoria.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR explicando.
