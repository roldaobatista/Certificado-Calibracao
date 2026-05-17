---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Métricas — Módulo Equipamentos do cliente

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo para localizar equipamento | Mediana do tempo entre abrir busca e abrir ficha 360° | ≤ 30s | telemetria UI | semanal |
| % equipamentos com QR impresso | (equip. com flag `qr_impresso=true`) / total | ≥ 90% | query | mensal |
| Taxa de escaneamento QR | scans/mês ÷ total equipamentos ativos | ≥ 60% | log de leituras | mensal |
| % equipamentos com histórico ≥ 1 certificado | (equip. com ≥1 cert.) / total | ≥ 80% após 6m | query | mensal |
| Equipamentos órfãos (sem cliente) | Contagem | = 0 | query | diária |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.9% | 43 min |
| Latência p95 ficha 360° | ≤ 1.5s | — |
| Latência p95 abrir via QR | ≤ 2s | — |
| Taxa de erro | < 0.1% | — |

---

## Dashboards canônicos

- Grafana: [a definir pós ADR-0001]
- Axiom (logs): [a definir]

---

## Alertas

| Alerta | Quando dispara | Severidade |
|---|---|---|
| QR sem destino | Scan em QR que aponta pra equip. inexistente | P2 |
| Tentativa de mutação INV-025 | Bloqueio de edição em campo imutável pós-cert. | P3 |
| Equipamento órfão | Equip. sem `cliente_id` válido | P2 |

---

## Métricas de saúde dos agentes

- Tokens por feature do módulo
- Taxa de retrabalho em US-EQP-*
- Tempo médio de entrega de US-EQP

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR.
