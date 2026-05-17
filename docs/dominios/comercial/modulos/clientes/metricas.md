---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
audiencia: dono
---

# Métricas — Módulo Clientes

> **Regra de ouro (auditor 7):** SLI/SLO violado → **page oncall** (PagerDuty/WhatsApp). KPI de negócio violado → **painel-do-dono + e-mail Roldão semanal**, NUNCA page.

---

## SLI / SLO Operacional (observabilidade técnica)

SLO de referência: domínio **CRM** em `docs/operacao/observabilidade.md` — disponibilidade **99.5%**, latência p99 < 1s, erro 5xx < 0.5%. Targets abaixo são refinamentos do módulo.

| SLI | SLO | Erro orçamento mensal | Origem |
|---|---|---|---|
| Disponibilidade `/clientes/*` | 99.9% (acima do CRM por ser caminho crítico) | ~43 min/mês | OTel / Grafana |
| Latência p95 GET `/clientes/{id}` | < 1.5s | — | OTel |
| Latência p95 POST `/clientes` | < 800ms | — | OTel |
| Taxa de erro 5xx | < 0.1% | — | OTel |

**Política de alerta SLI/SLO:** viola → **page oncall** + canal Slack `#oncall`.

| Alerta operacional | Quando dispara | Severidade | Ação |
|---|---|---|---|
| `clientes-sem-tenant-id` | Linter SQL detecta query sem `tenant_id` | P0 (vazamento cross-tenant) | page + suspende sistema |
| `clientes-5xx-spike` | Erro 5xx > 0.5% em 5min | P1 | page oncall |
| `clientes-latencia-spike` | p95 GET > 3s por 10min | P2 | page oncall |
| `lgpd-cadastro-sem-aceite` | Cadastro criado sem `lgpd_aceite_em` | P0 (violação LGPD) | page + bloqueio fluxo |

---

## KPIs de Negócio / Produto

Destino: **painel-do-dono semanal** + relatório executivo Roldão. **NÃO acionam pager.**

| Métrica | Definição | Target MVP-1 | Como medir | Frequência | Destino |
|---|---|---|---|---|---|
| Taxa de duplicidade | % de cadastros idênticos (mesmo CPF/CNPJ) sobre total | < 1% | Job noturno que conta CPF/CNPJ repetidos por tenant | Semanal | painel-do-dono |
| Tempo médio de cadastro PF | Mediana segundos entre abrir form e salvar com sucesso | < 60s | Telemetria front-end | Semanal | painel-do-dono |
| Taxa de uso da visão 360° (engajamento) | % de clientes ativos que tiveram tela 360° aberta ao menos 1x/semana | > 40% | Log de acesso à rota `/clientes/{id}` | Semanal | painel-do-dono |
| Taxa de cadastro com LGPD aceito | % de clientes criados com aceite LGPD registrado (RAT-03) | 100% (obrigatório) | Query `WHERE lgpd_aceite_em IS NULL` | Diária | painel-do-dono + auditoria |
| Tempo de importação 1-clique | Mediana segundos para importar planilha de 100 linhas | < 30s | Telemetria do job de import | Mensal | painel-do-dono |
| Acurácia de dedup automático | % de dedups automáticos NÃO revertidos em 30d | > 95% | Reversões / dedups totais | Mensal | painel-do-dono |

**Política de alerta KPI:** variação anômala → **e-mail Roldão semanal** (NUNCA page).

| Alerta KPI | Quando dispara | Destino |
|---|---|---|
| Queda engajamento 360° | Variação > -20% semana sobre semana | e-mail Roldão semanal |
| Acurácia dedup degradada | < 90% em 30d | e-mail Roldão semanal |
| Tempo cadastro subindo | Mediana > 90s por 2 semanas | painel-do-dono (sinalização) |

---

## Dashboards canônicos

- Grafana — painel "Clientes" SLI/SLO (link pós-ADR-0001) — destino oncall
- Painel-do-dono — KPIs negócio (link pós-ADR-0001) — destino Roldão
- Axiom — saved query "clientes-erros-7d"

## Métricas de saúde dos agentes

- Tokens consumidos por US deste módulo.
- Taxa de retrabalho (rebases por US).
- Tempo médio entrega US-CLI-NNN.

## Como evolui

Métrica nova → adicionar + configurar coleta. Mudança de target → ADR.
