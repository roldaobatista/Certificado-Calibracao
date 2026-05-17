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
>
> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall**. KPI de uso da biblioteca (reuso, BOM, retrabalho de desenho) → **painel-do-dono / gestor de engenharia**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — disponibilidade **99.5%**, latência p99 < 1s. Upload em Backblaze (storage WORM) é caminho crítico para preservação de arquivos.

| SLI | SLO | Erro orçamento (mensal) | Origem |
|---|---|---|---|
| Disponibilidade do módulo | 99.5% | ~3,6h/mês | OTel |
| Latência busca em biblioteca p95 | < 500ms | — | OTel |
| Taxa de sucesso upload | > 99% | — | OTel + Backblaze |
| Tempo médio upload arquivo 100MB | < 60s | — | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + Slack `#oncall`.

| Alerta operacional | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Falha persistente upload Backblaze | 3 falhas seguidas em 15min | page oncall + Watchdog | P1 |
| Latência busca > 2s por 10min | degradação | page oncall | P2 |
| 5xx > 0.5% em 5min | falha API | page oncall | P1 |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono mensal** + gestor de engenharia. **NÃO acionam pager.**

| Métrica | Definição | Target | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| % OS com projeto técnico vinculado (cobertura) | OS aplicáveis com projeto | ≥ 80% | join OS x Projeto | mensal | painel-do-dono |
| Tempo médio aprovação técnica (operação) | Submissão → aprovação | ≤ 3 dias úteis | timestamps revisão | semanal | painel-do-dono |
| Reuso de componentes da biblioteca (asset library) | Componentes usados em ≥2 projetos / total | ≥ 60% | contagem cruzada | mensal | painel-do-dono |
| Redução de retrabalho por "desenho errado" (qualidade) | OS reclassificadas retrabalho motivo "desenho errado" | -50% em 6 meses | classificação manual | trimestral | relatório trimestral |
| % projetos com BOM estruturado (qualidade dado) | BOM preenchido vs apenas anexo | ≥ 70% | atributo do projeto | mensal | painel-do-dono |
| Aprovações com assinatura digital ICP (compliance) | Aprovações com ICP / aprovações onde política exige | ≥ 30% | atributo da aprovação | mensal | painel-do-dono + auditoria |

**Política de alerta KPI:** variação anômala → **e-mail gestor / dashboard** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| Aprovação técnica pendente > SLA | configurável por tenant | e-mail engenheiro + gestor (não-page) |
| Revisão "rascunho" sem atividade > 30 dias | batch noturno | notificação ao autor (não-page) |
| Componente duplicado detectado | mesma fabricante+modelo no cadastro | sugestão merge ao usuário (não-page) |
| Reuso de componentes < 40% por 2 meses | degradação asset library | e-mail Roldão (não-page) |

---

## Dashboards canônicos

- **Grafana SLI/SLO:** painel "Engenharia — uploads, latência" pós ADR-0001 — destino oncall
- **Painel-do-dono KPIs:** "Engenharia — aprovações, biblioteca, BOM" pós ADR-0001 — destino Roldão/gestor
- **Axiom (logs):** query `module:engenharia` pós ADR-0001

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
