---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Onboarding

> Como saber se o módulo de implantação está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Tempo médio de implantação | Dias entre criação do tenant e assinatura do termo de aceite | ≤ 30 dias | data_aceite - data_criacao | mensal |
| Taxa de conclusão | % de implantações iniciadas que chegam a "concluída" em ≤ 60 dias | ≥ 90% | concluidas / iniciadas (janela 60d) | mensal |
| Inconsistências resolvidas pré go-live | % de inconsistências de migração tratadas antes do termo | ≥ 95% | resolvidas / total_inconsistencias | por implantação |
| Treinamentos registrados | Média de horas de treinamento por implantação | ≥ 4h | sum(duracao_treinamento) / implantacoes | mensal |
| NPS do onboarding | Nota do cliente após assinatura do termo | ≥ 8 | survey pós-aceite | por implantação |
| Implantações com sandbox usado | % com pelo menos 1 import-teste no sandbox antes da promoção | 100% | obrigatório | por implantação |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do wizard | 99.9% | 43min/mês |
| Latência p95 do import (até 10k linhas) | < 60s | — |
| Taxa de erro do import | < 1% | — |
| Sandbox provisionado em | < 5min após criação do tenant | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001 (painel "Onboarding em andamento" + "Funil de implantações").
- **Axiom:** logs de imports e validações de ambiente.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Implantação parada >7 dias | status inalterado por 7d | responsável interno + gestor | P2 |
| Validação de ambiente falhou | check automático falha | responsável interno | P1 |
| Import falhou ≥3x mesma planilha | mesmo hash de arquivo, ≥3 erros | responsável interno | P2 |
| Sandbox não provisionado | >5min após criação do tenant | watchdog → agente → Roldão se persistir | P1 |

---

## Métricas de saúde dos AGENTES

- Tokens consumidos por implantação completada.
- Taxa de retrabalho em US de onboarding.
- Tempo médio de entrega de cada US-ONB.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR explicando.
