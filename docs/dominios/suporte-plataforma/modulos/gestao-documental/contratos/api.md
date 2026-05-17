---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos API — Módulo Gestão Documental

---

## Convenções

- REST sobre HTTPS (formato final a confirmar pós ADR-0001).
- Autenticação: header `Authorization: Bearer <token>`.
- Tenant: dentro do token (`tenant_id` claim) + validado por middleware (INV-TENANT-001).
- Erros: RFC 7807 Problem Details.
- Idempotência: `Idempotency-Key` em uploads.
- Uploads grandes (>10MB) via multipart streaming.

---

## Endpoints

### `POST /v1/documentos`
**Propósito:** Criar documento + primeira versão (upload).
**Autorizado:** usuários com permissão `documento.criar`.
**Request (multipart/form-data):**
- `arquivo` (binário, até 50MB)
- `titulo`, `tipo_documento`, `entidade_tipo`, `entidade_id`, `requer_aprovacao` (bool), `data_validade` (opcional), `politica_retencao_id` (opcional), `tags` (array opcional)

**Response 201:**
```json
{
  "documento_id": "uuid",
  "versao_id": "uuid",
  "numero_versao": 1,
  "status": "vigente",
  "hash_sha256": "..."
}
```
**Códigos:** 201, 400 (validação), 401, 403, 413 (>50MB), 422.
**Invariantes:** `INV-001`, `INV-TENANT-001`.
**US:** `US-DOC-001`.
**Eventos:** `documento.criado`, `documento.versao_criada`.

---

### `GET /v1/documentos`
**Propósito:** Listar documentos do tenant com filtros.
**Query params:** `entidade_tipo`, `entidade_id`, `status`, `tipo_documento`, `tags`, `vencendo_em_dias`, `q` (busca full-text), `page`, `page_size`.
**Response 200:** array de documentos com paginação.
**Códigos:** 200, 401.

---

### `GET /v1/documentos/{id}`
**Propósito:** Detalhe + versões + metadados.
**Response 200:** objeto Documento + array de VersaoDocumento (resumo).

---

### `POST /v1/documentos/{id}/versoes`
**Propósito:** Substituir versão vigente (cria nova).
**Request:** mesmo formato de upload + `motivo_versao`.
**Response 201:** nova versão.
**Eventos:** `documento.versao_criada`.
**US:** `US-DOC-002`.

---

### `GET /v1/documentos/{id}/versoes/{versao_id}/download`
**Propósito:** Baixar binário da versão.
**Response 200:** binário (com headers de cache controlados).
**Auditoria:** registra acesso (`AcessoDocumento`).

---

### `POST /v1/documentos/{id}/versoes/{versao_id}/aprovar`
**Propósito:** Aprovar versão em_revisao.
**Autorizado:** usuários com `documento.aprovar`.
**Response 200:** status atualizado.
**Eventos:** `documento.aprovado`.
**US:** `US-DOC-003`.

---

### `POST /v1/documentos/{id}/links`
**Propósito:** Gerar link de compartilhamento.
**Request:**
```json
{"versao_id": "uuid", "expira_em": "2026-06-30T00:00:00Z", "senha": null, "max_acessos": null}
```
**Response 201:**
```json
{"link_id": "uuid", "url_publica": "https://...", "expira_em": "..."}
```
**US:** `US-DOC-010`.

---

### `DELETE /v1/documentos/{id}/links/{link_id}`
**Propósito:** Revogar link.
**Response 204.**

---

### `GET /v1/public/documentos/{token}`
**Propósito:** Acesso externo (sem auth) via token de compartilhamento.
**Response 200:** metadados públicos + URL temporária do binário.
**Códigos:** 200, 401 (senha), 410 (expirado), 429 (max_acessos).
**Auditoria:** registra IP, user-agent.

---

### `POST /v1/documentos/{id}/assinaturas`
**Propósito:** Solicitar assinatura.
**Request:**
```json
{"versao_id": "uuid", "tipo": "eletronica_simples", "assinantes": [{"identificador": "email@exemplo.com", "nome": "..."}]}
```
**Response 201:** array de convites com tokens.
**US:** `US-DOC-004`.

---

### `PUT /v1/documentos/{id}/acl`
**Propósito:** Atualizar lista de acesso.
**US:** `US-DOC-007`.
**Eventos:** auditoria.

---

### `GET /v1/documentos/{id}/acessos`
**Propósito:** Trilha de acessos.
**Response 200:** array de `AcessoDocumento`.
**Invariantes:** `INV-001`.

---

### `POST /v1/modelos-documento`
**Propósito:** Criar modelo reutilizável.
**US:** `US-DOC-006`.

---

### `POST /v1/modelos-documento/{id}/instanciar`
**Propósito:** Gerar documento a partir do modelo.

---

### `GET /v1/documentos/vencendo`
**Propósito:** Documentos vencendo em N dias.
**Query:** `dias` (default 30).
**US:** `US-DOC-005`.

---

## Eventos consumidos

Ver `../../../comum/integracoes-inter-modulos.md`. Principais:
- `cliente.deletado` (LGPD esquecimento) → marcar docs vinculados para revisão.
- `os.encerrada` → trigger de arquivamento.

## Rate limits

- Upload: 30 req/min/tenant.
- Busca full-text: 60 req/min/usuário.
- Link público: 100 req/min/token (anti-scraping).
- Default: 300 req/min/tenant.

## Versionamento

v1 atual. v2 com janela de 6 meses pra migração.

## Como esta lista evolui

Endpoint novo → linkar US. Quebra → ADR + janela. Descontinuação → `@deprecated` + Sunset header.
