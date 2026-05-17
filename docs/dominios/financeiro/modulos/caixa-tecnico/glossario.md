---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Glossário — Caixa do Técnico

| Termo | Definição |
|---|---|
| **Caixa do técnico** | Saldo + movimentações financeiras associadas a um técnico de campo (adiantamentos, despesas, reembolsos). |
| **Adiantamento** | Valor entregue ao técnico antes da execução pra cobrir despesas (peças, deslocamento, alimentação). |
| **Despesa** | Lançamento de gasto efetivo feito pelo técnico, com foto do recibo. |
| **Recibo / cupom fiscal** | Documento físico (foto) ou digital comprovando a despesa. |
| **Prestação de contas** | Ato de fechar um período: somar adiantamentos vs despesas, ajustar saldo. |
| **Saldo do caixa** | Adiantamentos − despesas prestadas. Positivo = técnico deve devolver; negativo = tenant deve reembolsar. |
| **Reembolso de km** | Despesa específica de deslocamento, calculada por km × tarifa configurada (JTBD-064). |
| **Despesa pendente** | Lançada pelo técnico mas ainda não validada pelo financeiro. |
| **Despesa validada** | Aprovada pelo financeiro → entra na prestação. |
| **Despesa rejeitada** | Recusada (recibo ilegível, fora de política) → técnico precisa ressubmeter. |
| **Política de despesa** | Conjunto de regras do tenant (limite por categoria, exige foto, alçada). |
| **Categoria de despesa** | Tipo (combustível, alimentação, pedágio, hospedagem, peça, deslocamento). |
| **Foto-comprovante** | Imagem anexada à despesa — INV-007 análogo (sem foto = não valida). |

## OS vinculada

Caixa do técnico é **vinculado a OS** sempre que possível — despesa "aluguel de equipamento" para OS X. Cria rastreabilidade para custeio (Wave B/MVP-2 — comissão sobre margem).

## Referências

- OP3.2 (caixa do técnico — Wave A robusto)
- BIG-08 (frota + UMC + caixa)
- JTBD-060 (solicitar adiantamento), JTBD-061 (lançar despesa), JTBD-062 (prestar contas em 5 min), JTBD-064 (reembolso km)
