---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Contrato Exports — Contas a Receber

## Exports disponíveis (MVP-1)

| Export | Formato | Filtros | Audiência |
|---|---|---|---|
| Lista de cobranças do período | CSV / XLSX | data emissão, status, cliente | financeiro do tenant |
| Recebimentos (baixas) do período | CSV / XLSX | data baixa, meio | financeiro / contador |
| Inadimplentes > 30 dias | CSV / PDF | aging, valor mínimo | dono |
| 2ª via boleto / PIX | PDF / link | título individual | cliente final |

## Schema CSV — Lista de cobranças

```
numero,fatura,cliente_nome,cliente_doc,valor_original,valor_atualizado,
emissao,vencimento,meio,status,baixa_data,baixa_origem
```

- Encoding: UTF-8 com BOM (compatibilidade Excel BR)
- Separador: `;` (padrão BR)
- Decimal: `,`
- Data: `DD/MM/YYYY`

## Schema CSV — Recebimentos

```
titulo_numero,cliente_nome,cliente_doc,valor,data_baixa,
meio,gateway_tx_id,origem_baixa
```

## PDF — Boleto / 2ª via

- Layout FEBRABAN padrão (gerado pelo gateway).
- Aferê injeta logo do tenant + dados OS de origem na descrição.

## PDF — Comprovante de pagamento

- Cabeçalho: nome tenant, CNPJ, logo
- Corpo: descrição, valor, data, meio, autenticação (hash)
- QR de verificação (V2)

## Wave B / V2 (non-goals MVP-1)

- Export SPED (V2 — fiscal/contador)
- Export OFX reverso (relatório bancário sintético)
- Export para sistema externo do contador (Domínio, Alterdata) — V2
- Relatório DRE — parte de OP12 (painel do dono)

## Retenção e privacidade

- Exports contendo CPF/CNPJ + valor classificados como sensíveis (LGPD).
- Audit log de cada download (RAT-08).
- Link de 2ª via expira em 72h.

## Limites operacionais

- CSV até 100k linhas; acima: paginação ou job assíncrono (V2).
- PDF de 1 título: síncrono; lote: job assíncrono.

## Referências

- `docs/conformidade/comum/retencao-matriz.md`
- `docs/conformidade/comum/lgpd-rat.md` RAT-08
- INV-008 audit
