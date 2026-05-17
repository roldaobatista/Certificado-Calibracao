---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: dono
modulo: garantia
dominio: operacao
---

# Métricas — Módulo Garantia

## KPIs de negócio

| Métrica | Definição | Target | Como medir | Frequência |
|---|---|---|---|---|
| Custo total de garantia / mês | Soma de CUSTO_GARANTIA no período | ≤ 3% da receita do mês | Lançamentos da conta CUSTO_GARANTIA | mensal |
| % OS em garantia procedente | OS-filha procedentes ÷ OS-filha total | benchmark interno após 3 meses | Contagem por status de análise | mensal |
| Tempo médio de análise | Data análise − data abertura da OS-filha | ≤ 5 dias úteis | Diferença de timestamps | semanal |
| Reincidência por peça-modelo | Modelos de peça com ≥ 5 garantias procedentes em 6 meses | tendência decrescente | Agrupamento por peça-modelo | mensal |
| Reincidência por técnico | Técnicos com ≥ 4 garantias procedentes em 6 meses | tendência decrescente | Agrupamento por técnico | mensal |
| Reincidência por cliente | Clientes com ≥ 3 garantias em 6 meses (procedentes e improcedentes) | sinal de fraude / mau uso | Agrupamento por cliente | mensal |
| Ressarcimento de fornecedor | Valor recuperado ÷ valor enviado em peças-fornecedor | ≥ 70% | Soma de ressarcimentos ÷ NF de remessa | mensal |
| Cobrança bloqueada indevidamente | Casos de desbloqueio manual aprovado | ≤ 5% das OS em garantia | Audit log de desbloqueio | mensal |
| Aderência da apuração de custo de garantia | Diferença % entre custo apurado pelo sistema (lançamentos CUSTO_GARANTIA) e revisão manual amostral feita pelo Auditor 2 (Qualidade). **Fórmula:** `abs(custo_sistema - custo_revisao) ÷ custo_revisao por OS amostrada`. **N-mínimo:** 10 OS-filha amostradas/mês, **critério de amostra:** OS-filha com `custo_garantia ≥ R$ 500`. **Responsável:** Auditor 2 Qualidade. | divergência média < 5% | Amostragem mensal documentada em planilha de auditoria; resultado registrado em `garantia.auditoria.apuracao` | mensal | painel-do-dono + Auditor 2 |
| Turnaround time (entrada → parecer final) | Dias úteis entre abertura da OS-filha de garantia e parecer final assinado (procedente/improcedente) | mediana ≤ 7 dias úteis | Diff entre `OSFilha.criada_em` e `Garantia.PareceFinal.assinado_em` | semanal |
| Appeal rate (contestação do parecer) | % pareceres finais contestados pelo cliente (recurso/reanálise) ÷ total pareceres | ≤ 10% | Eventos `Garantia.ReanaliseSolicitada` ÷ `Garantia.PareceFinal.emitido` | mensal |

---

## SLI/SLO técnico

Ver `../../../operacao/observabilidade.md`.

| SLI | SLO | Erro orçamento (mensal) |
|---|---|---|
| Disponibilidade da tela de análise | 99.9% | 43min/mês |
| Latência p95 abertura OS-filha | < 500ms | — |
| Taxa de erro em bloqueio de cobrança | 0% (crítico) | — |

---

## Dashboards canônicos

- Grafana: a definir pós ADR-0001
- Painel "Reincidência" — top 10 peça-modelo, técnico, cliente

---

## Alertas

| Alerta | Quando dispara | Quem notifica | Severidade |
|---|---|---|---|
| Desbloqueio manual de cobrança | toda vez que ocorre | Gerente operacional + audit | P2 |
| Peça-modelo virou REINCIDENTE | passou de N garantias em 6m | Comprador + Gerente | P2 |
| Prazo de retorno do fornecedor vencido | cron diário | Comprador | P3 |
| Custo de garantia > 5% da receita do mês | fechamento mensal | Gerente + Dono | P1 |

---

## Métricas de saúde dos agentes

- Tokens / feature do módulo
- Taxa de retrabalho / feature
- Tempo médio de entrega de US

---

## Como evolui

Métrica nova → adicionar + configurar coleta + bump CHANGELOG.
