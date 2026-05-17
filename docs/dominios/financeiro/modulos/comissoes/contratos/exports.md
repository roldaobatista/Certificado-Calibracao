---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: comissoes
dominio: financeiro
---

# Contrato Exports — Comissões

## Exports

| Export | Formato | Filtros | Audiência |
|---|---|---|---|
| Demonstrativo individual | PDF / XLSX | beneficiário + período | vendedor / técnico |
| Lote do mês — todas comissões | CSV / XLSX | período | financeiro |
| Resumo por beneficiário | CSV / PDF | período | dono / financeiro |
| Histórico de regras (auditoria) | CSV | beneficiário | financeiro / auditor |
| Contestações do período | CSV | período, status | financeiro / dono |

## Schema CSV — Demonstrativo individual

```
os_numero,cliente_nome,data_execucao,valor_os_bruto,percentual,
valor_comissao,data_pagamento_cliente,status,data_liberacao
```

Encoding UTF-8 BOM, `;`, `,` decimal, `DD/MM/YYYY`.

## Schema CSV — Lote do mês

```
beneficiario_nome,beneficiario_doc,os_numero,cliente,valor_os,
pct,valor_comissao,status,data_devida
```

## Schema CSV — Histórico de regras

```
beneficiario,tipo_formula,percentual,vigente_de,vigente_ate,
alterada_por,alterada_em
```

Pra evidenciar não-retroatividade em auditoria.

## PDF — Demonstrativo individual (layout)

- Cabeçalho: tenant + beneficiário + período + total devido
- Tabela: cada OS com cálculo transparente
- Rodapé: hash + QR de verificação (V2)
- Assinado por padrão (V2 — não precisa assinatura legal no MVP-1)

## Privacidade

- Demonstrativo só pra beneficiário + financeiro/dono. Vendedor nunca vê do colega.
- LGPD: dados pessoais do vendedor + dados financeiros sensíveis.
- Audit log de download obrigatório (RAT-08 análogo).

## Wave B / V2

- Export pra folha de pagamento (V2)
- Export pra contabilidade externa (V2)
- Relatório "ranking" de vendedores (Wave B — depende de discovery)

## Limites

- PDF/CSV individual: síncrono.
- Lote do mês inteiro: assíncrono se > 1000 linhas.

## Referências

- `docs/conformidade/comum/retencao-matriz.md`
- INV-008
