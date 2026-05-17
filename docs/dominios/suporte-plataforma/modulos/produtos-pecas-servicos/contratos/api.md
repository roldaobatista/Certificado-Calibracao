---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: produtos-pecas-servicos
dominio: suporte-plataforma
---

# Contratos de API — Catálogo

## Convenções

- `/v1/` path. Bearer auth. `X-Tenant-ID`.
- Erros RFC 7807. `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/catalogo/itens`
**Request:**
```json
{
  "tipo": "peca",
  "codigo": "PEC-001",
  "nome": "Bateria 9V",
  "descricao": "...",
  "unidade_medida": "un",
  "categoria": "consumiveis",
  "controla_estoque": true,
  "preco": 12.50
}
```
**Response 201:** item + versão 1.
**Erros:** 409 (código duplicado), 422 (campo inválido).
**Invariantes:** `INV-026`, `INV-TENANT-001`.
**US:** US-CAT-001.
**Eventos:** `Catalogo.item_cadastrado`.

---

### `GET /v1/catalogo/itens?busca=&tipo=&status=&categoria=`
**Response:** lista paginada.

---

### `GET /v1/catalogo/itens/{id}?data_referencia=YYYY-MM-DD`
**Propósito:** ficha do item.
**Comportamento:** sem `data_referencia`, retorna versão vigente hoje. Com `data_referencia`, retorna versão vigente naquela data (INV-026).

---

### `PATCH /v1/catalogo/itens/{id}`
**Comportamento:**
- Atualização de atributo versionável → cria nova `ItemCatalogoVersao` com `vigente_de = body.vigente_de || hoje`.
- Atualização de `codigo_interno` → 422 (imutável).

**Erros:** 422, 404, 403.
**Invariantes:** `INV-026`.
**US:** US-CAT-002.
**Eventos:** `Catalogo.preco_alterado` se preço mudou.

---

### `POST /v1/catalogo/itens/{id}/inativar`
**Eventos:** `Catalogo.item_inativado`.

---

### `POST /v1/catalogo/kits`
**Request:** `{ "codigo": "KIT-001", "nome": "...", "composicao": [{"item_id": "uuid", "quantidade": 2}] }`
**Erros:** 422 (kit-dentro-de-kit, item inativo).
**US:** US-CAT-003.

---

### `POST /v1/catalogo/importacao`
**Request:** multipart `file=...` + mapeamento de colunas.
**Response:** `{ "job_id": "uuid" }` (assíncrono).
**US:** US-CAT-004.

### `GET /v1/catalogo/importacao/{job_id}`
**Response:** status + linhas processadas + erros por linha.

---

### `GET /v1/catalogo/itens/{id}/historico`
**Response:** lista de `ItemCatalogoVersao`.

---

## Rate limits

- `POST /catalogo/importacao`: 1 simultâneo/tenant.
- Default: a definir.

## Versionamento

v1, v2 coexistem por 6 meses.

## Como evolui

- Endpoint novo → linkar US.
- Quebra de contrato → ADR + Sunset.
