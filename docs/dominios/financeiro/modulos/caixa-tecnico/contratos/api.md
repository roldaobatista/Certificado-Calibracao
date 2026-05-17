---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: caixa-tecnico
dominio: financeiro
---

# Contrato API — Caixa do Técnico

## Recursos

### `POST /v1/caixa/{tecnico_id}/adiantamento`

Solicitar adiantamento.

Body: `{ valor, motivo, os_id?, meio_preferido }`. Idempotência obrigatória.

### `POST /v1/adiantamentos/{id}/aprovar`

Body: `{ observacao? }`. Verifica alçada.

### `POST /v1/adiantamentos/{id}/entregar`

Body: `{ data, meio, comprovante_url }`. Marca entregue.

### `POST /v1/despesas`

Lançar despesa.

Body multipart:
- `valor`, `data`, `categoria`, `descricao`
- `os_id?`, `km?` (deslocamento)
- `gps_lat?`, `gps_lng?`
- `foto_comprovante` (file — **obrigatório**)

Bloqueio: requisição sem foto → 422.

Idempotência: `Idempotency-Key` (importante pro app offline retentar).

### `GET /v1/despesas`

Lista. Query: `?tecnico=&status=&periodo_de=&periodo_ate=&os_id=&page=`.

### `POST /v1/despesas/{id}/validar`

Body: `{ observacao? }`. Só financeiro/dono.

### `POST /v1/despesas/{id}/rejeitar`

Body: `{ motivo }`. Notifica técnico.

### `POST /v1/caixa/{tecnico_id}/prestar-contas`

Body: `{ periodo_de, periodo_ate }`. Cria PrestacaoContas imutável.

Resposta: `{ prestacao_id, saldo, direcao }`.

### `GET /v1/caixa/{tecnico_id}/saldo`

Saldo atual + prestação em aberto.

## Endpoint offline-sync

### `POST /v1/sync/despesas-lote`

Pra app reenviar batch offline.

Body: `[{ idempotency_key, ...campos despesa, foto_base64 }]`.

Resposta: array com `{ idempotency_key, status, despesa_id_remoto, erro? }`.

## Webhooks de saída

- `adiantamento.solicitado`
- `adiantamento.aprovado`
- `adiantamento.entregue`
- `despesa.lancada`
- `despesa.validada` → consumido por custeio OS (Wave B)
- `despesa.rejeitada`
- `prestacao.fechada`

## Erros

| Código | Significado |
|---|---|
| `foto_obrigatoria` | requisição sem foto — bloqueio inviolável |
| `foto_duplicada` | hash já existe — bloqueio |
| `limite_excedido` | acima do limite da política — bloqueio com justificativa |
| `os_invalida` | OS não pertence ao tenant ou não atribuída ao técnico |
| `prestacao_ja_aberta` | já existe prestação aberta no período |

## Audit

INV-008 obrigatório. Toda mudança em despesa/adiantamento/prestação registra `actor`, `before`, `after`, `ts`.

## Rate limiting

- Lançamento: 120/min/técnico (campo)
- Validação: 600/min/financeiro

## Non-goals API

- GraphQL
- OCR endpoint (V2)
- Streaming de fotos (V2)

## Referências

- OP3.2
- `docs/comum/integracoes-inter-modulos.md`
