---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Despesas

> Endpoints. Formato (REST recomendado) a confirmar em ADR-0001.

---

## Convenções

- Versionamento por path (`/v1/`).
- `Authorization: Bearer <token>`.
- Tenant via header `X-Tenant-ID` (validado por `INV-TENANT-001`).
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `POST /v1/despesas`
**Propósito:** criar despesa em rascunho ou já enviar para aprovação.
**Papel:** colaborador autenticado.
**Request:**
```json
{
  "data": "2026-05-17",
  "valor": 125.40,
  "moeda": "BRL",
  "categoria_id": "uuid",
  "descricao": "Combustível ida cliente X",
  "comprovante_id": "uuid",
  "os_id": "uuid|null",
  "viagem_id": "uuid|null",
  "tecnico_id": "uuid|null",
  "centro_custo_id": "uuid|null",
  "adiantamento_id": "uuid|null",
  "acao": "enviar_aprovacao | salvar_rascunho"
}
```
**Response 201:**
```json
{ "id": "uuid", "status": "pendente_aprovacao | rascunho" }
```
**Códigos:** 201, 400, 401, 403, 422 (sem comprovante quando `acao=enviar_aprovacao`).
**Invariantes:** `INV-DSP-001`, `INV-MULTI-TENANT-001`.
**US:** `US-DSP-001`, `US-DSP-004`.
**Eventos:** `Despesa.Criada` quando `acao=enviar_aprovacao`.

---

### `POST /v1/despesas/{id}/comprovantes`
**Propósito:** upload do arquivo de comprovante (multipart).
**Request:** `multipart/form-data` campo `arquivo`.
**Response 201:**
```json
{ "comprovante_id": "uuid", "hash_sha256": "...", "tipo": "image/jpeg" }
```
**Códigos:** 201, 400 (tipo não suportado), 413 (arquivo > 10 MB), 401, 403.
**US:** `US-DSP-001`.
**Invariantes:** `INV-WORM-001`.

---

### `GET /v1/despesas`
**Propósito:** listar com filtros.
**Query:** `?status=&periodo_ini=&periodo_fim=&categoria_id=&colaborador_id=&os_id=&centro_custo_id=&page=&page_size=`.
**Response 200:** página com colunas conforme `ui.md`.
**Códigos:** 200, 400, 401, 403.
**US:** `US-DSP-005`.

---

### `GET /v1/despesas/{id}`
**Propósito:** detalhe da despesa + histórico de aprovação.
**Response 200:** corpo da despesa + array `aprovacoes`.
**Códigos:** 200, 401, 403, 404.

---

### `POST /v1/despesas/{id}/aprovar`
**Propósito:** aprovador decide.
**Papel:** aprovador com alçada suficiente.
**Request:** `{ "comentario": "opcional" }`.
**Response 200:** novo status + próximo aprovador se houver.
**Códigos:** 200, 401, 403 (sem alçada), 409 (já decidida).
**Invariantes:** `INV-AUDIT-001`.
**US:** `US-DSP-002`.
**Eventos:** `Despesa.Aprovada` (se foi a última alçada).

---

### `POST /v1/despesas/{id}/rejeitar`
**Papel:** aprovador.
**Request:** `{ "motivo": "obrigatório, min 10 chars" }`.
**Response 200:** status `rejeitada`.
**Códigos:** 200, 400, 401, 403, 409, 422 (motivo curto).
**US:** `US-DSP-002`.
**Eventos:** `Despesa.Rejeitada`.

---

### `POST /v1/despesas/{id}/reembolsar`
**Papel:** financeiro.
**Pré-condição:** despesa aprovada e sem adiantamento vinculado (ou diferença positiva).
**Request:** `{ "conta_bancaria_colaborador_id": "uuid" }`.
**Response 200:** `{ "contas_pagar_id": "uuid" }`.
**Códigos:** 200, 401, 403, 409.
**US:** `US-DSP-003`.
**Eventos:** `Despesa.Reembolsada` (após liquidação).

---

### `POST /v1/despesas/{id}/compensar`
**Papel:** financeiro.
**Pré-condição:** despesa aprovada com `adiantamento_id` válido e saldo positivo.
**Response 200:** `{ "saldo_adiantamento_pos": 0.00, "diferenca_para_reembolso": 0.00 }`.
**Eventos:** `Despesa.Compensada`.
**US:** `US-DSP-003`.

---

## Eventos consumidos

- `Adiantamento.Aberto` de `caixa-tecnico/` (para popular `adiantamento_id` disponível).
- `ContasPagar.Liquidado` (para fechar despesa em `reembolsada`).

Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /v1/despesas` — 20 req/min/usuário.
- `POST /v1/despesas/{id}/comprovantes` — 10 req/min/usuário.
- Default: a definir em ADR-0001.

## Versionamento

- v1, v2 coexistem 6 meses.
- Quebra → ADR + bump CHANGELOG.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela de migração.
- `@deprecated` → headers Sunset (RFC 8594).
