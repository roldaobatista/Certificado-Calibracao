---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Modelo de Domínio — Contas a Receber

## Agregados

### `Fatura` (raiz de agregado)

Documento que agrupa itens cobráveis (OSs, contratos) em um único cliente.

Atributos:
- `id`, `tenant_id`, `cliente_id`, `numero_sequencial_tenant`
- `data_emissao`, `valor_bruto`, `valor_liquido` (após descontos)
- `origem`: `os` | `contrato-recorrente` | `manual`
- `status`: `rascunho` | `emitida` | `parcialmente-paga` | `paga` | `cancelada`
- `itens[]`: referência a OS ou linha de contrato

### `Titulo` (raiz separada)

Cobrança individual emitida a partir da fatura.

Atributos:
- `id`, `fatura_id`, `tenant_id`, `cliente_id`
- `valor_original`, `valor_atualizado` (com juros/multa)
- `data_emissao`, `data_vencimento`, `data_baixa`
- `meio`: `boleto` | `pix` | `cartao`
- `gateway_externo_id` (nullable até gateway responder)
- `linha_digitavel` / `qr_code` / `tx_id`
- `status`: `aberto` | `pago` | `parcialmente-pago` | `vencido` | `cancelado` | `em-disputa`
- `regra_juros_id`, `regra_multa_id`, `regra_desconto_id`

### `Parcela` (subentidade do Título)

Quando título é parcelado. Cada parcela tem `valor`, `vencimento`, `status` próprios.

### `Pagamento` (entidade de evento)

Registro imutável de baixa. Atributos: `titulo_id`, `valor`, `data`, `origem` (`webhook-gateway`, `ofx`, `manual`, `pix-direto`), `comprovante_url`, `audit`.

## Regras de negócio

- **Juros/multa/desconto** aplicados na leitura (`valor_atualizado` calculado on-the-fly conforme data atual) — nunca persistir valor inflado, persiste regra.
- **Idempotência**: webhook gateway com mesmo `tx_id` aplicado 2× = 1 pagamento.
- **Cancelamento** só permitido se `status = aberto` E sem pagamento parcial.
- **Baixa parcial**: divide saldo restante em novo título sucessor (configurável).
- **INV-026**: alterar tabela de preço não recalcula títulos já emitidos.

## Eventos emitidos

- `TituloEmitido(titulo_id, valor, cliente_id, vencimento)`
- `BoletoGerado(titulo_id, linha_digitavel)`
- `Pago(titulo_id, valor, data, origem)` → consumido por Comercial (timeline 360°) e Comissões (gatilho OP4)
- `TituloVencido(titulo_id, dias_atraso)` → consumido por régua de cobrança (Wave B)
- `TituloCancelado(titulo_id, razao)`

## Eventos consumidos

- `OSConcluida` (Operação) → gera fatura + título
- `ContratoRenovado` (Comercial) → gera título recorrente
- Webhook gateway → emite `Pago`

## Non-goals do modelo

- Não modela antecipação/factoring (Wave B/V2).
- Não modela conta corrente do cliente (saldo agregado) — Wave B/V2.
- Não modela protesto/cartório.

## Invariantes

- INV-026 (preço não-retroativo), INV-008 (audit log).

## Referências

- `docs/comum/integracoes-inter-modulos.md` (eventos)
- OP-FIN, OP11
