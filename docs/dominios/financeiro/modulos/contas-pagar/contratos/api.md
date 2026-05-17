---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-pagar
dominio: financeiro
---

# Contrato API — Contas a Pagar

> Wave C. Rascunho.

## Recursos

### `POST /v1/lancamentos`

Cria lançamento.

Body: `{ fornecedor_id, descricao, valor, vencimento, conta_analitica_id, centro_custo_id, anexos[], rateio[]? }`

Idempotência: `Idempotency-Key`.

### `GET /v1/lancamentos`

Lista. Query: `?status=&fornecedor=&centro_custo=&vencimento_de=&vencimento_ate=&page=`.

### `GET /v1/lancamentos/{id}`

Detalhe + histórico de aprovações + pagamentos.

### `POST /v1/lancamentos/{id}/aprovar`

Body: `{ observacao? }`. Verifica alçada do `actor`.

### `POST /v1/lancamentos/{id}/rejeitar`

Body: `{ razao }`.

### `POST /v1/lancamentos/{id}/pagar`

Body: `{ valor, data, conta_bancaria_id, comprovante_url? }`. Marca baixa.

### `POST /v1/lancamentos/{id}/cancelar`

Body: `{ razao }`. Só permitido se nunca pago.

### `GET/POST /v1/plano-contas`

CRUD do plano (com guarda anti-deleção; usa desativação).

### `GET/POST /v1/centros-custo`

CRUD.

### `POST /v1/conciliacao/ofx` (V2)

Upload OFX → retorna sugestões de match.

## Webhooks de saída

- `lancamento.criado`
- `lancamento.aprovado`
- `lancamento.pago`
- `lancamento.cancelado`

## Webhooks de entrada (V2)

- Pluggy/Belvo: pagamento efetuado dispara baixa automática.

## Erros

| Código | Significado |
|---|---|
| `alcada_insuficiente` | actor não tem permissão pro valor |
| `rateio_invalido` | soma ≠ 100% |
| `conta_inativa` | conta do plano desativada |
| `duplicata_provavel` | warning, não bloqueia |

## Rate limiting

A definir pós-discovery (estimar volume).

## Audit

INV-008. Toda mudança em lançamento + plano + alçada registra `actor`, `before`, `after`.

## Non-goals API

- GraphQL.
- Webhook DDA.
- API pública pro contador (V2+).

## Referências

- `docs/comum/integracoes-externas/pluggy-belvo.md`
