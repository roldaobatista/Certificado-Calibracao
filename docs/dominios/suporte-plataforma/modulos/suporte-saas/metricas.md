---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Suporte SaaS

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de deflexão | % consultas resolvidas via BC sem abrir ticket | > 40% | eventos "resolveu via artigo" / consultas totais | semanal |
| Cumprimento de SLA | % tickets resolvidos dentro do SLA do plano | > 95% | resolved_em ≤ deadline | semanal |
| CSAT | Avaliação pós-ticket (1-5) | > 4.5 | pesquisa pós-fechamento | mensal |
| Tempo médio de primeira resposta | minutos do abertura à primeira resposta humana/IA | < 30min P3, < 4h P1 (plano Pro) | observabilidade | diário |
| Tempo médio de resolução | abertura → resolução | varia por categoria/plano | observabilidade | semanal |
| Tickets por tenant ativo | total/mês | < 3/tenant — indicador de qualidade do produto | query | mensal |
| Reincidência de bug | mesmo bug reportado por > 1 tenant | < 5 reincidências/mês | agrupamento por tag | semanal |
| Engajamento de roadmap | % usuários que votaram em ao menos 1 item/trimestre | > 20% | tracking de voto | trimestral |
| Aceitação de manutenção | % tenants que não reclamam após aviso adequado | > 95% | tickets pós-manutenção / total tenants | por janela |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do portal de suporte | 99.9% | 43min/mês |
| Latência abertura de ticket p95 | < 1s | — |
| Latência busca BC p95 | < 500ms | — |
| Latência resposta IA chat p95 | < 3s | — |
| Taxa de erro em criação de ticket | < 0.1% | — |

---

## Dashboards canônicos

- **Grafana:** painel `suporte-saas`.
- **Axiom:** filtro `module=suporte-saas`.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Backlog de tickets P1 > 10 | acumulando | equipe suporte + Roldão | P1 |
| SLA violado em > 5% dos tickets na semana | tendência negativa | Roldão | P2 |
| Tempo médio de primeira resposta > 2x target | degradação | equipe suporte | P2 |
| Acesso remoto > 4h sem revogação | sessão suspeita | tenant admin + auditoria | P1 |
| CSAT < 4.0 em janela de 7 dias | queda satisfação | Roldão | P2 |
| Manutenção sem aviso T-24h | violação processo | Roldão | P1 |

---

## Métricas de saúde dos agentes (suporte IA)

- % tickets resolvidos só pela IA (sem handoff).
- Taxa de handoff IA→humano por categoria.
- Tokens consumidos por ticket atendido.
- Acurácia de classificação automática (categoria/prioridade).

---

## Como evolui

Métrica nova → coleta + CHANGELOG. Mudança de target → ADR.
