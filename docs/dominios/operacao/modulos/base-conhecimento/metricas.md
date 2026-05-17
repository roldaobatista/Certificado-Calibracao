---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Métricas — Base de Conhecimento

> **Convenções canônicas** (ver `docs/comum/glossario-roldao.md`):
> - **TMR** (Tempo Médio de Resolução) = abertura → fechamento final. Escopo aqui: OS/Chamado que consumiu artigo da BC.
> - **Cobertura documental por equipamento** = dimensão "conhecimento" (vs. `qualidade_dados_inicial` no onboarding e `conformidade_formato_pdfa` em certificados).

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de exibição de sugestão | Sugestões mostradas ao usuário dentro de Chamado/OS. **Evento:** `SugestaoExibida` (artigo aparece no painel lateral). | tracking básico, sem target | contagem de eventos `SugestaoExibida` | semanal |
| Taxa de abertura de sugestão | % das sugestões exibidas que o usuário clicou pra ler. **Evento:** `SugestaoAberta` (clique no card). **Fórmula:** `count(SugestaoAberta) ÷ count(SugestaoExibida)`. | ≥ 35% | ratio de eventos | semanal |
| Taxa de aplicação de sugestão | % das sugestões abertas em que o artigo virou solução real do chamado/OS. **Evento:** `SugestaoAplicada` (artigo vinculado à resolução). **Fórmula:** `count(SugestaoAplicada) ÷ count(SugestaoAberta)`. | ≥ 50% | ratio de eventos + FK `chamado.artigo_solucao_id` | mensal |
| Cobertura documental por equipamento — canônico, dimensão: conhecimento (meta, não SLO) | % dos equipamentos top-50 com ≥ 1 artigo publicado. **Não é SLO** — meta de produto. `[baseline-em-construcao]` — medir mensal a partir do go-live; meta ≥ 80% até 6 meses pós-go-live. | meta 6m: ≥ 80% | join equipamentos × artigos | mensal |
| TMR com artigo vs. sem artigo — canônico, escopo: OS/Chamado | TMR (abertura → fechamento) de OS/Chamado quando consumiu artigo | < 70% do TMR sem artigo | comparar buckets | mensal |
| Artigos desatualizados | Nº de artigos sem revisão > 12 meses | < 10% do total | query date diff | mensal |
| Latência aprovação | Mediana de horas entre submissão e aprovação | < 48h | timestamps | semanal |
| Utilidade média | (% útil) / (% útil + % não útil) por artigo. **N-mínimo:** ≥ 10 votos pra entrar no cálculo (artigos com < 10 votos ficam fora do agregado). | ≥ 75% no top 20 (entre artigos com ≥ 10 votos) | agregado de votos com filtro `count_votos >= 10` | mensal |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade | 99.5% | 3h36min/mês |
| Latência busca p95 | < 800ms | — |
| Taxa de erro upload | < 0.5% | — |

---

## Dashboards canônicos

- Grafana: link a definir pós ADR-0001
- Axiom (logs): link

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Aprovação parada | artigo > 7 dias em revisão | aprovador + gerente | P2 |
| Sugestão zerada | nenhuma sugestão aceita em 7d consecutivos | dono produto | P3 |
| Upload falhando | > 5% erros em 1h | watchdog → Roldão | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos por feature
- Taxa de retrabalho por US
- Tempo médio de entrega
