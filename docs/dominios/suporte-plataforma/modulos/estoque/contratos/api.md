---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: estoque
dominio: suporte-plataforma
---

# Contratos de API — Estoque

## Convenções

- `/v1/`. Bearer auth. `X-Tenant-ID`.
- Erros RFC 7807. `Idempotency-Key` obrigatório em movimentações.
- Foto da transferência: multipart upload.

---

## Endpoints

### `GET /v1/estoque/saldos?item=&local=&abaixo_minimo=&lote_vencendo=`
**Response:** lista paginada de saldos.
**US:** US-EST-001.

---

### `POST /v1/estoque/movimentos/entrada`
**Request:**
```json
{
  "item_id": "uuid",
  "local_id": "uuid",
  "quantidade": 10,
  "lote": "L123",
  "validade": "2027-01-01",
  "numero_serie": null,
  "origem_descricao": "NF 12345"
}
```
**Response 201:** movimento criado + saldo atualizado.
**Erros:** 422 (validade no passado, item inativo), 403.
**Invariantes:** `INV-TENANT-001`.
**US:** US-EST-002.
**Eventos:** `Estoque.movimento_registrado`.

---

### `POST /v1/estoque/transferencias`
**Propósito:** etapa 1 (emissão).
**Request:** `{ "item_id", "local_origem_id", "local_destino_id", "quantidade", "lote", "numero_serie" }`
**Response 201:** transferência em_transito.
**Erros:** 409 (saldo insuficiente), 422.
**Eventos:** `Estoque.transferencia_emitida`.

---

### `POST /v1/estoque/transferencias/{id}/aceitar`
**Propósito:** etapa 2 com foto.
**Request:** multipart com `foto` (binary, ≤ 5MB) + `observacao` (opcional).
**Comportamento:**
- Valida `foto` presente → senão 422 "foto do lacre obrigatória" (BIG-12).
- Salva foto em storage; cria movimento aceite.

**Erros:** 422 (foto ausente, foto inválida), 404, 403.
**US:** US-EST-003.
**Eventos:** `Estoque.transferencia_aceita`.

---

### `POST /v1/estoque/transferencias/{id}/recusar`
**Request:** `{ "categoria": "peca_errada|quantidade_errada|lacre_violado|outro", "motivo": "..." }`
**Erros:** 422 (motivo vazio).
**Eventos:** `Estoque.transferencia_recusada`.

---

### `GET /v1/estoque/transferencias?status=&local_origem=&local_destino=`
**Response:** lista de transferências.

---

### `POST /v1/estoque/consumo`
**Propósito:** consumir para OS.
**Request:** `{ "item_id", "local_id", "quantidade", "lote", "os_id" }`
**Comportamento:**
- Valida lote não vencido → senão 422 PT "lote L123 vencido em DD/MM/AAAA".
- Reduz saldo (ou reserva).

**Erros:** 422 (vencido, saldo insuficiente).
**Eventos:** `Estoque.movimento_registrado`.

---

### `POST /v1/estoque/reservas` / `DELETE /v1/estoque/reservas/{id}`
**US:** US-EST-005.

---

### `GET /v1/estoque/kardex?item_id=&local_id=&desde=&ate=`
**Response:** linha do tempo de movimentos.

---

### `POST /v1/estoque/inventario` / `PATCH /v1/estoque/inventario/{id}/linha` / `POST /v1/estoque/inventario/{id}/finalizar`
**US:** US-EST-004.

---

### `POST /v1/estoque/minimos` / `PATCH /v1/estoque/minimos/{id}`
**US:** US-EST-006.

---

## Rate limits

- Upload foto: 30 req/min/usuário.
- Default: a definir ADR-0001.

## Versionamento

v1, v2 coexistem 6 meses.

## Como evolui

- Endpoint novo → linkar US.
- Quebra → ADR + Sunset.
