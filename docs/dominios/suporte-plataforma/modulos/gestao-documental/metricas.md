---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Gestão Documental

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Adoção do módulo | % tenants ativos que fizeram >= 1 upload nos últimos 30 dias | > 70% | query no banco | semanal |
| Documentos com versão duplicada | % docs com hash igual e nomes diferentes | < 5% | job de detecção | semanal |
| Renovações no prazo | % docs com validade renovados antes do vencimento | > 90% | comparação data_validade vs data_renovacao | mensal |
| Tempo médio de busca | p95 do tempo entre query e primeiro resultado | < 2s | observabilidade | diário |
| Cobertura OCR | % PDFs digitalizados com texto indexado | > 98% | job verificação | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade da biblioteca | 99.5% | 3h36/mês |
| Latência de upload p95 (até 50MB) | < 30s | — |
| Latência de busca p95 | < 2s | — |
| Tempo de OCR p95 | < 5min | — |
| Taxa de erro em upload | < 0.5% | — |

---

## Dashboards canônicos

- **Grafana:** painel `gestao-documental` (link pós ADR-0001)
- **Axiom (logs):** filtro `module=gestao-documental`

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| OCR backlog > 100 docs | fila acumulando | agente → Roldão se >1h | P2 |
| Falha de upload > 1% em 5min | erros em sequência | agente → Roldão se >15min | P1 |
| Storage do tenant > 80% quota | aproximação do limite | tenant admin + agente | P3 |
| Acesso a doc com ACL restrita por não autorizado | tentativa de acesso negada | tenant admin (audit) | P2 |

---

## Métricas de saúde dos agentes

- Tokens consumidos por feature do módulo.
- Taxa de retrabalho por feature.
- Tempo médio de entrega de US.

---

## Como esta lista evolui

Métrica nova → configurar coleta + bump CHANGELOG. Mudança de target → ADR.
