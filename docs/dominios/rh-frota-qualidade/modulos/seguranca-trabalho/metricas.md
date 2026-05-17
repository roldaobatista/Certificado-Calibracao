---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
modulo: seguranca-trabalho
---

# Métricas — Módulo Segurança do Trabalho

> Como saber se o módulo está reduzindo risco trabalhista, operacional e jurídico.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de OS com checklist preenchido | OS executadas / OS com checklist anexado | 100% | Query OS x checklist | semanal |
| Taxa de colaboradores com ASO válido | Colaboradores ativos com ASO não vencido | 100% | Query colaborador x ASO.validade | mensal |
| Taxa de colaboradores com treinamento de segurança válido por função | Pra cada função, % com NR aplicável válida | 100% | Cross função x treinamento | mensal |
| EPIs vencidos em uso | EPIs entregues com CA vencido ou validade individual vencida | 0 | Query entregas ativas | semanal |
| Taxa de frequência de acidentes (TF) | (nº acidentes c/ afastamento × 1.000.000) / homens-hora trabalhadas | <5 | Acidentes + folha de horas | mensal |
| Taxa de gravidade (TG) | (dias perdidos × 1.000.000) / homens-hora | <100 | Acidentes + afastamentos | mensal |
| Tempo médio de resposta a quase-acidente | Da data do registro à data da ação corretiva concluída | ≤7 dias | Workflow ação corretiva | mensal |
| Acidentes evitados (proxy) | Quase-acidentes que geraram ação corretiva concluída | crescente | Registros quase-acidente | trimestral |
| Taxa de acidentes + quase-acidentes / 1000h (operacional) | Eventos totais (acidente + quase-acidente) por 1000 homens-hora trabalhadas. **Complementa TF/TG (que só conta acidentes com afastamento × 1Mh)** — esta métrica é mais sensível e captura tendência preventiva. **Fórmula:** `(count(Acidente) + count(QuaseAcidente)) × 1000 ÷ Σ homens-hora`. | < 2 eventos / 1000h | Registros acidente + quase-acidente + folha de horas | mensal |
| % técnicos com treinamento NR vigente (compliance) | Técnicos ativos com TODAS as NRs aplicáveis à sua função dentro da validade | 100% | Cross função × matriz NR × `Treinamento.validade` | mensal |
| % OSs bloqueadas por checklist SST faltante (controle) | OSs que tentaram avançar pra "executada" sem checklist anexado e foram bloqueadas pelo sistema. **Sinal duplo:** tendência decrescente = cultura SST melhorando; pico súbito = bug na exigência ou falha de UX. | < 5% das OSs/mês | Eventos `OS.BloqueadaPorChecklistSST` ÷ count(OS criadas) | semanal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do painel SST | 99.9% | 43min/mês |
| Latência p95 do painel de alertas | <2s | — |
| Disponibilidade de upload de evidência fotográfica | 99.5% | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001
- **Axiom (logs):** a definir

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| EPI vencendo em 30 dias | Daily job | Gerente SST | P3 |
| ASO vencendo em 30 dias | Daily job | Gerente SST | P3 |
| Treinamento de segurança vencendo em 30 dias | Daily job | Gerente SST + colaborador | P3 |
| Tentativa de alocar técnico sem NR válida | Em tempo real | Despachante + gerente | P2 |
| OS executada sem checklist (erro de bypass) | Em tempo real | Gerente SST + auditor | P1 |
| Acidente registrado | Em tempo real | Gerente SST + dono | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos / feature do módulo.
- Taxa de retrabalho em US de SST.
- Tempo médio de entrega de US-SST-*.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Mudança de target → ADR.
