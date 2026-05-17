---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Glossário — Contas a Receber

| Termo | Definição |
|---|---|
| **Fatura** | Documento interno do tenant que agrupa uma ou mais OSs/contratos cobráveis; gera 1+ títulos. |
| **Título** | Linha individual de cobrança (boleto, PIX, cartão); pertence a uma fatura. |
| **Parcela** | Subdivisão de um título quando o tenant negocia parcelamento. |
| **Boleto** | Título com linha digitável + código de barras; emitido via gateway bancário. |
| **PIX cobrança** | Título com QR estático ou dinâmico; conciliação automática via webhook. |
| **Juros** | Acréscimo proporcional ao tempo de atraso (% ao mês ou ao dia). |
| **Multa** | Acréscimo fixo aplicado uma vez quando título vence sem pagamento. |
| **Desconto pontualidade** | Abatimento concedido se pago antes do vencimento. |
| **Aging** | Faixas etárias da inadimplência (0-30, 31-60, 61-90, > 90 dias). |
| **Régua de cobrança** | Sequência de comunicações automáticas escaladas (lembrete → aviso → corte). |
| **Inadimplência** | Estado do título depois do vencimento sem baixa. |
| **Baixa** | Marcação de "pago" no título; pode ser manual, por conciliação OFX ou webhook gateway. |
| **Conciliação** | Casamento entre extrato bancário e títulos abertos. |
| **OFX** | Formato padrão de extrato bancário exportado pelo banco. |
| **Recorrência** | Cobrança automática repetida (mensal, anual) — base de contrato. |
| **Status do título** | `aberto`, `pago`, `parcial`, `vencido`, `cancelado`, `em-disputa`. |
| **Cliente devedor** | Pessoa/empresa que tem 1+ títulos vencidos. |
| **Antecipação** | Operação onde tenant troca título a vencer por dinheiro hoje (com deságio) — non-goal MVP-1. |

## Referências

- OP-FIN (Wave A) — módulo financeiro mínimo
- OP11 (Wave B) — cobrança + inadimplência
- BIG-04 — multi-canal financeiro
- `docs/dominios/financeiro/README.md`
