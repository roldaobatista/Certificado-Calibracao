---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: fornecedores
dominio: suporte-plataforma
---

# Contratos de API — Fornecedores

## Convenções

- `/v1/`. Bearer auth. `X-Tenant-ID`.
- Erros RFC 7807. `Idempotency-Key` em mutações.
- Endpoint público de resposta de cotação usa **token-only** (sem Bearer).

---

## Endpoints

### `POST /v1/fornecedores`
**Request:** `{ "cnpj", "razao_social", "nome_fantasia", "categorias", "condicao_pagamento_padrao", "dados_bancarios" }`
**Validação:** CNPJ algoritmo brasileiro + unicidade por tenant.
**Response 201:** fornecedor status=em_homologacao.
**Erros:** 409 (CNPJ duplicado), 422 (CNPJ inválido).
**US:** US-FOR-001.
**Eventos:** `Fornecedor.cadastrado`.

---

### `POST /v1/fornecedores/{id}/homologar`
**Pré:** docs obrigatórios presentes e válidos.
**Erros:** 422 (docs incompletos).
**Eventos:** `Fornecedor.homologado`.

---

### `POST /v1/fornecedores/{id}/contatos` / `PATCH .../{contato_id}` / `DELETE`
**LGPD:** registrar finalidade na criação.

---

### `POST /v1/fornecedores/{id}/documentos` (multipart)
**Request:** `file`, `tipo`, `validade (nullable)`.

---

### `POST /v1/cotacoes`
**Request:**
```json
{
  "linhas": [{"item_id": "uuid", "quantidade": 5, "observacao": ""}],
  "fornecedor_ids": ["uuid", "uuid", "uuid"],
  "prazo_resposta": "2026-06-01",
  "canal": ["email", "whatsapp"]
}
```
**Response 201:** cotação + tokens gerados.
**US:** US-FOR-002.
**Eventos:** `Cotacao.enviada`.

---

### `GET /v1/cotacoes/{id}/comparativo`
**Response:** matriz itens × fornecedores com preços, prazos, condições, melhor preço por linha.
**US:** US-FOR-003.

---

### `POST /v1/cotacoes/{id}/escolher`
**Request:** `{ "fornecedor_id", "justificativa": { "categoria": "qualidade|prazo|relacionamento|outro", "texto": "..." } }`
**Validação:** se `fornecedor_id` NÃO é o menor preço, `justificativa` é obrigatória.
**Eventos:** `Cotacao.fechada`.

---

### `GET /v1/cotacao-publica/{token}` (PÚBLICO, sem auth)
**Response 200:** formulário de resposta + dados do tenant.
**Response 410 Gone:** token expirado.
**Response 409:** já respondida.

### `POST /v1/cotacao-publica/{token}`
**Request:** respostas por item.
**Validação:** token válido e não expirado.
**Eventos:** —

---

### `POST /v1/pedidos-compra`
**Request:** `{ "cotacao_id": "uuid|null", "fornecedor_id": "uuid", "linhas": [...] }`
**Validação:** se valor total > `teto_cotacao_obrigatoria` do tenant E `cotacao_id IS NULL` → 422.
**US:** US-FOR-004.
**Eventos:** `PedidoCompra.enviado` (quando status muda pra enviado).

---

### `POST /v1/pedidos-compra/{id}/avaliacao`
**Request:** `{ "prazo": 8, "qualidade": 9, "preco": 7, "comentario": "..." }`
**Pré:** pedido recebido_total (vem do Estoque).
**US:** US-FOR-005.
**Eventos:** `AvaliacaoFornecedor.registrada`.

---

### `GET /v1/fornecedores/{id}/historico-preco?item_id=`
**Response:** séries temporais por item.
**US:** US-FOR-006.

---

## Rate limits

- `POST /v1/cotacao-publica/{token}`: 10 req/min/token.
- Default: a definir ADR-0001.

## Versionamento

v1, v2 coexistem 6 meses.

## Como evolui

- Endpoint novo → linkar US.
- Quebra → ADR + Sunset.
