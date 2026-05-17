---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
---

# Métricas do módulo Engenharia Técnica

> Como saber se o módulo está entregando valor.

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| % OS com projeto técnico vinculado | das OS que aplicam, quantas têm projeto | ≥ 80% | join OS x Projeto | mensal |
| Tempo médio de aprovação técnica | submissão → aprovação | ≤ 3 dias úteis | timestamps revisão | semanal |
| Reuso de componentes da biblioteca | componentes usados em ≥ 2 projetos / total | ≥ 60% | contagem cruzada | mensal |
| Redução de retrabalho por "desenho errado" | OS reclassificadas como retrabalho com motivo "desenho errado" | -50% em 6 meses | classificação manual em OS | trimestral |
| % projetos com BOM estruturado | BOM preenchido vs apenas anexo | ≥ 70% | atributo do projeto | mensal |
| Aprovações com assinatura digital ICP | das aprovações, quantas usaram ICP | ≥ 30% (apenas onde política exige) | atributo da aprovação | mensal |

---

## SLI/SLO técnico

Detalhe em `../../../operacao/observabilidade.md`. Resumo:

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do módulo | 99.5% | ~3,6h/mês |
| Latência busca em biblioteca p95 | < 500ms | — |
| Taxa de sucesso upload | > 99% | — |
| Tempo médio upload arquivo 100MB | < 60s | — |

---

## Dashboards canônicos

- **Grafana:** painel "Engenharia — uploads, aprovações, biblioteca" (link pós ADR-0001).
- **Axiom (logs):** query `module:engenharia` (link pós ADR-0001).

---

## Alertas configurados

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Falha persistente upload Backblaze | 3 falhas seguidas em janela 15min | Watchdog → operador | P1 |
| Aprovação técnica pendente > SLA | configurável por tenant | Watchdog → engenheiro responsável + gestor | P2 |
| Revisão "rascunho" sem atividade > 30 dias | batch noturno | notificação ao autor | P3 |
| Componente duplicado detectado (mesma fabricante+modelo) | no cadastro | sugestão de merge ao usuário | P3 |

---

## Métricas de saúde dos AGENTES neste módulo

(parte da Família 5 Governança IA)

- Tokens consumidos por feature.
- Taxa de retrabalho por US.
- Tempo médio de entrega de US-ENG-NNN.

---

## Como esta lista evolui

- Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
- Métrica obsoleta → `@deprecated`.
- Mudança de target → ADR.
