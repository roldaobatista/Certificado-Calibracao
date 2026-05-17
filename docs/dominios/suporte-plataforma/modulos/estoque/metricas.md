---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Métricas — Módulo Estoque

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo para localizar peça | mediana abrir busca → mostrar local + saldo | ≤ 30s | telemetria | semanal |
| % transferências com foto | (transferências aceitas c/ foto) / (transferências aceitas) | = 100% | query | diária |
| Acuracidade de inventário | 1 − (Σ|diferença| / Σ saldo) após inventário | ≥ 95% | query | mensal |
| Tempo médio em trânsito | mediana entre emissão e aceite | ≤ 48h | query | semanal |
| Transferências recusadas | (recusadas) / (emitidas) | ≤ 5% | query | mensal |
| Itens em estoque mínimo | contagem | reduzir vs mês anterior | query | semanal |
| Lotes vencidos consumidos | contagem (deveria ser zero por regra) | = 0 | query | diária |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade | 99.9% | 43 min |
| Latência p95 lista saldos | ≤ 1s | — |
| Latência p95 kardex | ≤ 1.5s | — |
| Upload foto (até 5MB) | p95 ≤ 5s | — |
| Taxa de erro em movimento | < 0.1% | — |

---

## Dashboards

- Grafana: [pós ADR-0001]
- Axiom: [pós ADR-0001]

---

## Alertas

| Alerta | Quando | Severidade |
|---|---|---|
| Tentativa consumo lote vencido | sistema bloqueia + alerta | P1 |
| Transferência em trânsito > 7 dias | sem aceite | P2 |
| Mínimo de item atingido | configurável por item/local | P2 |
| Diferença inventário > 10% | após contagem | P2 |
| Foto rejeitada (storage falhou) | erro upload | P1 |

---

## Métricas de saúde dos agentes

- Tokens por US-EST-*
- Retrabalho
- Tempo médio entrega

---

## Como evolui

- Métrica nova → coleta + CHANGELOG.
- Target → ADR.
