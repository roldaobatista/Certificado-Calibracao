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

## KPIs de negócio

| Métrica | Definição | Target MVP-1 | Como medir | Frequência |
|---|---|---|---|---|
| Taxa de duplicidade | % de cadastros idênticos (mesmo CPF/CNPJ) sobre total | < 1% | Job noturno que conta CPF/CNPJ repetidos por tenant | Semanal |
| Tempo médio de cadastro PF | Mediana segundos entre abrir form e salvar com sucesso | < 60s | Telemetria front-end | Semanal |
| Taxa de uso da visão 360° | % de clientes ativos que tiveram tela 360° aberta ao menos 1x/semana | > 40% | Log de acesso à rota `/clientes/{id}` | Semanal |
| Taxa de cadastro com LGPD aceito | % de clientes criados com aceite LGPD registrado (RAT-03) | 100% (obrigatório) | Query `WHERE lgpd_aceite_em IS NULL` | Diária |
| Tempo de importação 1-clique | Mediana segundos para importar planilha de 100 linhas | < 30s | Telemetria do job de import | Mensal |
| Acurácia de dedup automático | % de dedups automáticos que NÃO foram revertidos manualmente em 30d | > 95% | Reversões / dedups totais | Mensal |

## SLI/SLO técnico

| SLI | SLO | Erro orçamento mensal |
|---|---|---|
| Disponibilidade `/clientes/*` | 99.9% | ~43 min/mês |
| Latência p95 GET `/clientes/{id}` | < 1.5s | — |
| Latência p95 POST `/clientes` | < 800ms | — |
| Taxa de erro 5xx | < 0.1% | — |

## Dashboards canônicos

- Grafana — painel "Clientes" (link pós-ADR-0001)
- Axiom — saved query "clientes-erros-7d"

## Alertas

| Alerta | Quando dispara | Severidade |
|---|---|---|
| `clientes-sem-tenant-id` | Linter SQL detecta query sem `tenant_id` | P0 (vazamento cross-tenant) |
| `dedup-revertida-massa` | > 10 dedups revertidas em < 24h | P1 (algoritmo errado) |
| `import-falha-massiva` | > 30% das linhas de um import rejeitadas | P2 (mapeamento ruim ou planilha mal-formada) |
| `lgpd-cadastro-sem-aceite` | Qualquer cadastro criado sem `lgpd_aceite_em` | P0 (violação LGPD) |

## Métricas de saúde dos agentes

- Tokens consumidos por US deste módulo.
- Taxa de retrabalho (rebases por US).
- Tempo médio entrega US-CLI-NNN.

## Como evolui

Métrica nova → adicionar + configurar coleta. Mudança de target → ADR.
