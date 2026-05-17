---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: base-conhecimento
dominio: operacao
---

# Contratos API — Base de Conhecimento

## Convenções

- Versionamento via path `/v1/`.
- Auth: Bearer token. Tenant via `X-Tenant-ID` ou no token (INV-TENANT-001).
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key` em mutação.

---

## Endpoints

### `POST /v1/bcn/artigos`
**Propósito:** criar rascunho.
**Papel:** autor (técnico).
**Request:**
```json
{"titulo":"...","tipo":"solucao","corpo":"...","equipamento_id":"uuid","marca":"...","modelo":"...","tipo_servico":"...","normas":["ISO 17025"],"origem_os_id":"uuid?"}
```
**Response 201:**
```json
{"id":"uuid","status":"rascunho","versao":0}
```
**Códigos:** 201, 400, 401, 403, 422.
**INV:** INV-TENANT-001.
**US:** US-BCN-001.
**Eventos:** —

---

### `PUT /v1/bcn/artigos/{id}`
**Propósito:** editar rascunho.
**Pré:** status = rascunho ou rejeitado.

---

### `POST /v1/bcn/artigos/{id}/submeter`
**Propósito:** enviar pra revisão.
**Response 200:** `{"status":"em_revisao"}`.
**US:** US-BCN-002.

---

### `POST /v1/bcn/artigos/{id}/aprovar`
**Propósito:** aprovar e publicar.
**Papel:** aprovador técnico.
**Pré:** status = em_revisao; aprovador ≠ autor.
**Request:** `{"comentario":"..."}`
**Response 200:** `{"status":"publicado","versao":N}`.
**Eventos:** `BaseConhecimento.ArtigoPublicado`.
**US:** US-BCN-002.

---

### `POST /v1/bcn/artigos/{id}/rejeitar`
**Request:** `{"comentario":"obrigatório","modo":"rejeitar|ajustes"}`
**Response 200:** `{"status":"rascunho"}`.

---

### `POST /v1/bcn/artigos/{id}/arquivar`
**Pré:** publicado.
**Eventos:** `BaseConhecimento.ArtigoArquivado`.

---

### `GET /v1/bcn/artigos`
**Query:** `q`, `equipamento_id`, `marca`, `modelo`, `tipo`, `status`, `desatualizado`, `page`, `sort`.
**Response:** lista paginada com snippet, categoria, utilidade.
**US:** US-BCN-005.

---

### `GET /v1/bcn/artigos/{id}`
**Response:** artigo + versão corrente + metadados.

---

### `GET /v1/bcn/artigos/{id}/versoes`
**Response:** lista de versões com timestamps e aprovador.
**US:** US-BCN-006.

---

### `GET /v1/bcn/artigos/{id}/versoes/{n}`
**Response:** snapshot imutável.

---

### `POST /v1/bcn/artigos/{id}/voto`
**Request:** `{"util": true|false}`.
**Idempotente por usuário.**
**US:** US-BCN-008.

---

### `POST /v1/bcn/artigos/{id}/comentarios`
**Request:** `{"corpo":"...","tipo":"sugestao_melhoria|duvida|errata"}`.
**US:** US-BCN-007.

---

### `POST /v1/bcn/artigos/{id}/anexos`
**Multipart:** arquivo + descricao.
**Limite tamanho:** config tenant.

---

### `GET /v1/bcn/sugestoes`
**Query:** `origem_tipo=chamado|os&origem_id=uuid&top=5`.
**Response:** lista ordenada por score.
**US:** US-BCN-003, US-BCN-004.
**Eventos:** `BaseConhecimento.SugestaoExibida`.

---

### `POST /v1/bcn/sugestoes/{id}/aplicar`
**Marca sugestão como aplicada.**
**Eventos:** `BaseConhecimento.SugestaoAplicada`.

---

## Eventos consumidos

`Chamados.ChamadoAberto`, `OS.OSCriada`, `Treinamentos.TrilhaAtualizada`. Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- Busca: 60 req/min/usuário.
- Upload anexo: 10/min/usuário.

## Versionamento

v1 estável. Quebra exige ADR + 6 meses de janela.
