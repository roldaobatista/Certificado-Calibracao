---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: contas-receber
dominio: financeiro
---

# Contrato API — Contas a Receber

> REST + webhooks. Idempotência obrigatória. Auth tenant-scoped.

## Recursos

### `POST /v1/faturas`

Cria fatura (rascunho ou emitida).

Body: `{ cliente_id, origem, itens[], emitir_titulo: boolean, meio?, parcelas? }`

Resposta: `201 { fatura_id, titulos: [...] }`

Idempotência: header `Idempotency-Key` obrigatório.

### `POST /v1/titulos`

Cria título avulso (sem fatura formal — caso manual).

### `GET /v1/titulos`

Lista. Query: `?status=&cliente_id=&vencimento_de=&vencimento_ate=&page=`

### `GET /v1/titulos/{id}`

Detalhe + valor_atualizado calculado on-the-fly + histórico de pagamentos.

### `POST /v1/titulos/{id}/baixar`

Baixa manual.

Body: `{ valor, data, comprovante_url?, observacao? }`

Resposta: `200 { pagamento_id, status_novo }`

### `POST /v1/titulos/{id}/cancelar`

Body: `{ razao }`. Bloqueado se houver pagamento parcial.

### `POST /v1/titulos/{id}/segunda-via`

Reenvia linha digitável / QR.

## Webhooks de entrada (gateway → Aferê)

### `POST /v1/webhooks/gateway/{provider}`

Body: variável por provider; normalizado internamente.

- Verificação de assinatura HMAC obrigatória.
- Idempotência via `tx_id` do gateway.
- Resposta 2xx mesmo em duplicata (não rejeitar).
- Emite evento interno `Pago`.

## Webhooks de saída (Aferê → tenant)

- `titulo.emitido`
- `titulo.pago`
- `titulo.vencido`
- `titulo.cancelado`

Entrega com retry exponencial; assinado HMAC.

## Erros

| Código | Significado |
|---|---|
| `cliente_invalido` | CPF/CNPJ não bate |
| `gateway_indisponivel` | tentar novamente |
| `regra_juros_ausente` | tenant não configurou |
| `titulo_imutavel` | já tem pagamento parcial; cancelar bloqueado |

## Rate limiting

- Emissão: 60/min por tenant; 1000/h.
- Listagem: 600/min por tenant.

## Audit

Toda mutação registra `actor_id`, `tenant_id`, `action`, `entity`, `before`, `after`, `ts` — INV-008.

## Non-goals API

- GraphQL.
- Bulk import (Wave B).
- Webhook de read.

## Referências

- `docs/comum/integracoes-externas/pluggy-belvo.md`
- `docs/comum/integracoes-inter-modulos.md`
