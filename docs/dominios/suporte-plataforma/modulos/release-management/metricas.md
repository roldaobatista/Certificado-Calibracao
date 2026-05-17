---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
relacionados:
  - docs/adr/0006-feature-flags.md
---

# Métricas — Módulo Release Management

---

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Releases sem rollback | % releases publicadas que não precisaram rollback em 7 dias | > 95% | tracking de rollback | mensal |
| Cleanup de flags | % flags removidas em até 90 dias do criado | > 90% | data_criacao vs data_remocao | trimestral |
| Flags ativas no código | total de flags vivas em qualquer momento | < 50 simultâneas | contagem | semanal |
| Janela de breaking change | dias entre anúncio e quebra | >= 60 dias | comparação datas | por evento |
| Adesão ao beta | % tenants no programa | > 10% | tracking opt-in | mensal |
| Tempo médio entre releases | dias entre publicações | < 14 dias (cadência saudável) | tracking | mensal |
| % releases com release notes completas | adicionado/modificado/corrigido preenchidos | 100% | validação | por release |
| Migrações com rollback testado | % migrações destrutivas com plano validado | 100% | review pré-execução | por migração |
| Deployment frequency (DORA) | Quantidade de releases publicadas em produção por unidade de tempo. **Benchmark DORA:** Elite ≥ múltiplos/dia, High = 1/dia a 1/semana, Medium = 1/semana a 1/mês, Low > 1/mês. | Medium na Foundation; High após estabilização (alvo de longo prazo) | count(`Release.publicada_em_producao`) ÷ período | semanal/mensal |
| Lead time for changes (DORA) | Tempo entre commit aceito na branch principal e código rodando em produção. **Benchmark DORA:** Elite < 1h, High < 1 dia, Medium < 1 semana. | Medium na Foundation; High no estado estável | Diff `Commit.merged_em_main` → `Deploy.aplicado_em_producao` para o mesmo commit | semanal |
| Hotfix rate (DORA — proxy de Change Failure Rate) | % releases marcadas como `tipo=hotfix` ou que precisaram de patch corretivo em ≤48h após publicação. **Benchmark DORA CFR:** Elite ≤ 5%, High ≤ 10%, Medium ≤ 15%. | ≤ 10% | count(`Release.tipo=hotfix` OR `Release.patch_em_48h=true`) ÷ count(`Release.publicada`) | mensal |
| Cleanup de flags ≥ 90% (já no PRD) | Reforço aqui pra rastreabilidade: ver linha "Cleanup de flags" acima — métrica é a mesma. | ≥ 90% | data_criacao vs data_remocao | trimestral |

---

## SLI/SLO técnico

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade do serviço de flags | 99.95% | 22min/mês |
| Latência avaliação de flag p95 | < 10ms | — |
| Latência avaliação de flag p99 | < 50ms | — |
| Disponibilidade portal release notes | 99.9% | 43min/mês |
| Taxa de erro em migração orquestrada | < 0.5% | — |

---

## Dashboards canônicos

- **Grafana:** painel `release-management`.
- **Axiom:** filtro `module=release-management`.

---

## Alertas

| Alerta | Quando dispara | Quem é notificado | Severidade |
|---|---|---|---|
| Avaliação de flag > 50ms p95 por 5min | degradação | SRE + Roldão | P1 |
| Flag morta há > 90 dias sem cleanup | débito técnico | PM + Roldão | P3 |
| Migração falha em produção | incidente | SRE + Roldão | P0 |
| Breaking change anunciado < 60 dias | violação política | Roldão | P2 |
| Release sem notes publicadas | violação processo | PM + Roldão | P2 |
| Release sem aprovação dupla pra destrutiva | violação segurança | Roldão | P1 |

---

## Métricas de saúde dos agentes

- Tokens consumidos por release notes gerada.
- Acurácia de classificação automática (feature vs bug vs breaking change).
- Taxa de retrabalho em release notes (revisão humana muda muito?).

---

## Como evolui

Métrica nova → coleta + CHANGELOG. Target → ADR.
