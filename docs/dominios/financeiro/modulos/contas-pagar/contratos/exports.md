---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Contrato Exports — Contas a Pagar

> Wave C. Rascunho.

## Exports previstos

| Export | Formato | Filtros | Audiência |
|---|---|---|---|
| Lista de lançamentos do período | CSV / XLSX | data, status, centro custo | financeiro |
| Pagamentos efetuados | CSV / XLSX | data baixa, banco | financeiro / contador |
| Despesa por centro de custo | CSV / PDF | período | dono / gerente |
| Despesa por categoria (plano de contas) | CSV / PDF | período | dono / contador |
| Comprovante de pagamento | PDF | lançamento | tenant / fornecedor |

## Schema CSV — Lançamentos

```
numero,fornecedor_nome,fornecedor_doc,descricao,valor,emissao,
vencimento,pagamento,conta_analitica,centro_custo,status
```

Padrão BR: UTF-8 BOM, `;`, `,` decimal, `DD/MM/YYYY`.

## Schema CSV — Rateio

Export separado quando precisa visão analítica de rateio.

```
lancamento_numero,centro_custo,percentual,valor_rateado
```

## PDF — Comprovante de pagamento

- Cabeçalho tenant + fornecedor
- Valor pago + data + conta bancária
- Hash de autenticação
- Anexos (comprovante de banco) incorporados

## Wave C / V2

- Export SPED Contribuições (contador) — V2
- Export pra ERP contábil externo (Domínio, Alterdata, Contabilizei) — V2
- Relatório DRE — parte de OP12

## Privacidade

- Exports contêm CNPJ/CPF de fornecedores + valores — sensíveis (LGPD).
- Audit de download obrigatório.
- Acesso só com papel financeiro ou superior.

## Limites

- CSV ≤ 100k linhas síncrono; acima: assíncrono.

## Referências

- `docs/conformidade/comum/retencao-matriz.md`
- INV-008
