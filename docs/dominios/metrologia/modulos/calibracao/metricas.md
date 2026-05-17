---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Calibração

> Como saber se este módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Lead time entrada→aprovação | Dias úteis entre recepção do instrumento e aprovação 2ª conferência | mediana ≤ 3 dias | Diff timestamps | semanal |
| Taxa de rejeição em 1ª revisão | % calibrações que voltaram do RT pro metrologista | ≤ 10% | Contagem | semanal |
| Taxa de rejeição em 2ª conferência | % calibrações que voltaram da 2ª pro 1ª revisão | ≤ 5% | Contagem | semanal |
| Calibrações RBC emitidas fora do escopo | Quantidade de calibrações RBC executadas fora do escopo CMC | 0 | Auditoria diária | diária |
| Padrões usados fora de vigência | Quantidade de seleções de padrão com cert externo vencido | 0 | Bloqueio em runtime + auditoria | diária |
| Escore médio em ensaios de proficiência | Média do \|z\| das últimas rodadas | \|z\| ≤ 1 | Registros EP | trimestral |
| Cobertura de ensaios complementares | % calibrações com linearidade/repetibilidade quando aplicável | ≥ 95% | Auditoria por método | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.9% | 43min |
| Latência cálculo incerteza (≤100 pontos) p95 | < 1s | — |
| Latência registro leitura p95 | < 200ms | — |
| Taxa de erro no motor de cálculo | 0% (qualquer divergência = incidente P0) | — |

---

## Dashboards canônicos

- **Grafana:** a definir pós ADR-0001.
- **Axiom (logs):** a definir.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Calibração RBC tentada fora de escopo | Validação bloqueou | RT + admin + watchdog | P1 |
| Padrão vencido tentado em seleção | Validação bloqueou | RT + admin | P2 |
| Verificação intermediária reprovada | Padrão fora de critério de aceitação | RT + qualidade | P0 |
| Ensaio de proficiência \|z\|≥3 | Desempenho insatisfatório | RT + qualidade + admin | P0 |
| Versão do motor de cálculo mudou sem ADR | CI detecta | Watchdog | P0 |
| Calibração parada > 5 dias em revisão | Atraso anômalo | RT + admin | P2 |

---

## Métricas de saúde dos AGENTES

- Tokens por feature deste módulo.
- Taxa de retrabalho em US-CAL-NNN.
- Tempo médio entrega de US.

---

## Como esta lista evolui

- Métrica nova → adicionar + coleta + CHANGELOG.
- Obsoleta → `@deprecated`.
- Mudança de target → ADR.
