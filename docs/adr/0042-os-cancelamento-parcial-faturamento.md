---
adr: 0042
titulo: Cancelamento parcial de atividade × Faturamento da OS
status: proposta
data: 2026-05-23
proposto-por: agente (Onda 6 saneamento pré-Marco 3 — auditor 5)
revisado-por: tech-lead-saas-regulado (pendente) + advogado-saas-regulado (pendente fiscal)
bloqueia-fase: Wave A Marco 3 (`os`) + integração Financeiro
depende-de: ADR-0023 (OS com Atividades)
---

# ADR-0042 — Cancelamento parcial × Faturamento

## Contexto

PRD §6 US-OS-008 (cancelarAtividade) permite cancelar UMA atividade da
OS sem cancelar a OS toda. Caso real: cliente desistiu da manutenção,
mantém calibração. Cenário cria pergunta não respondida no PRD anterior:
**como o valor da OS é recalculado** quando uma atividade vira CANCELADA
após orçamento aprovado?

Possíveis caminhos:

A. OS fatura sempre o escopo original (atividade cancelada cobrada
   integralmente). Rejeitado — viola CDC art. 39 (prática abusiva).
B. OS fatura escopo final pós-cancelamentos (atividade CANCELADA não
   compõe `ContasReceber`). Aceito — alinha com expectativa do cliente
   + permite NF-e correta.
C. Emite NF-e original + nota de devolução proporcional. Complexidade
   fiscal alta para MVP-1; vai pra Wave B (módulo fiscal).

## Decisão

Caminho B: **OS atômica MVP-1 fatura escopo final pós-cancelamentos**.

Regra:

1. `ContasReceber` é criada/atualizada a partir de
   `sum(atividades_não_canceladas.valor_unitario_snapshot)` na transição
   `OS → CONCLUIDA` (todas atividades em estado terminal).
2. `valor_unitario_snapshot` foi congelado por atividade na abertura
   (preço da tabela vigente — INV-026 + ADR-0023).
3. Quando `cancelarAtividade` executa, OS publica `OS.EscopoAlterado`
   com payload `{tenant_id, os_id, atividade_id_cancelada, valor_removido,
   valor_total_atualizado, motivo, correlation_id}`.
4. Consumer `financeiro/contas-receber` atualiza `ContasReceber.valor`
   se OS ainda não foi `FATURADA`; se já foi, abre NC fiscal manual
   (gate Wave B — `ajuste-pos-faturamento`).
5. Atividade CANCELADA permanece visível no histórico da OS (não some
   da timeline — auditoria ISO 17025 cl. 7.4).

## Invariante

`INV-OS-FAT-001` — "faturamento de OS = `sum(atividades.valor_unitario_snapshot)
WHERE atividade.estado != CANCELADA`. Não inclui itens de OS vinculados
a atividade cancelada (`os_item.atividade_id`). Recálculo trigger por
`OS.EscopoAlterado`".

## AC novo (em US-OS-008 do PRD)

GIVEN atividade cancelada com sucesso, WHEN servidor processa, THEN
publica `OS.EscopoAlterado` + Financeiro consumer recalcula
`ContasReceber.valor` (se ainda RASCUNHO) OR emite alerta NC fiscal
(se já FATURADA).

## Consequências

- **Positivas:** cliente paga o que recebeu; LGPD/CDC alinhados;
  rastreabilidade preservada (histórico mostra atividade cancelada).
- **Negativas:** Financeiro precisa consumir evento — débito Wave A
  acompanhado de gate `GATE-FIN-CR-ESCOPO-ALTERADO`.
- **Wave B:** ajuste pós-faturamento (cancelamento após NF-e) sai do
  MVP-1; alerta operacional manual nesse caso.

## Como evolui

Decisão de incluir cancelamento pós-faturamento automático exige novo
ADR + integração nota de devolução / cancelamento NF-e.
