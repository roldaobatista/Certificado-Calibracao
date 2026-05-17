---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Certificados

> Endpoints REST/RPC (formato em ADR-0001).

---

## Convenções

- Path: `/v1/certificados/`.
- Auth: Bearer.
- Tenant: header `X-Tenant-ID` ou claim.
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.
- Página pública verificadora: `/v/{qr_token}` (sem auth).

---

## Endpoints

### `POST /v1/certificados`
**Propósito:** gerar certificado (status RASCUNHO ou PENDENTE_ASSINATURA).
**RBAC:** RT, admin.
**Request:**
```json
{
  "tipo": "CERT_CALIBRACAO_RBC",
  "calibracao_id": "uuid",
  "template_id": "uuid",
  "data_validade_recalibracao": "2027-05-17"
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "numero_sequencial": 1234,
  "ano": 2026,
  "versao": 1,
  "status": "PENDENTE_ASSINATURA",
  "pdf_url": "/v1/certificados/uuid/pdf",
  "hash_pdf_sha256": "abc..."
}
```
**Códigos:** 201, 400, 401, 403, 409 (calibração não aprovada), 422 (acreditação vencida).
**Invariantes:** `INV-012`, `INV-013`, `INV-014`, `INV-019`.
**US:** `US-CER-001`.
**Eventos:** `Certificados.Emitido`.

---

### `GET /v1/certificados`
**Query:** `tipo, status, cliente_id, instrumento_id, data_inicio, data_fim, page, page_size`.
**Response 200:** página de certificados.

---

### `GET /v1/certificados/{id}`
**Response 200:** payload completo (sem snapshot expandido — link separado).

---

### `GET /v1/certificados/{id}/pdf`
**Response 200:** stream PDF (Content-Type: application/pdf). Headers `Content-Disposition: attachment`.
**Eventos:** `Certificados.Baixado` (se via portal cliente).

---

### `GET /v1/certificados/{id}/snapshot`
**Response 200:** snapshot JSON completo (imutável).

---

### `POST /v1/certificados/{id}/assinatura/iniciar`
**Propósito:** servidor gera nonce + signing_time pro fluxo Web PKI Lacuna.
**RBAC:** RT.
**Response 200:**
```json
{
  "nonce": "base64",
  "signing_time": "2026-05-17T14:23:45-03:00",
  "hash_pdf_sha256": "abc...",
  "session_id": "uuid"
}
```

### `POST /v1/certificados/{id}/assinatura/finalizar`
**Request:**
```json
{
  "session_id": "uuid",
  "pkcs7": "base64"
}
```
**Response 200:** AssinaturaDigital + status atualizado.
**Códigos:** 200, 400, 401, 403, 409 (nonce reusado/expirado), 422 (cadeia ICP inválida, ART/RRT vencida).
**Invariantes:** `INV-019`, ADR-0009. Nonce one-shot.
**Eventos:** `Certificados.Assinado`.

---

### `POST /v1/certificados/{id}/reemissao`
**Request:**
```json
{
  "motivo": "texto >= 50 chars descrevendo o que muda e por quê",
  "ajustes_snapshot": { /* deltas */ }
}
```
**Response 201:** novo certificado versao+1.
**Invariantes:** `INV-014` (anterior preservada → SUBSTITUIDA).
**Eventos:** `Certificados.Reemitido`.

---

### `POST /v1/certificados/{id}/cancelamento`
**Request:** `{ "motivo": "...", "assinatura_admin_id": "..." }`
**Response 200:** status CANCELADO.
**Invariantes:** `INV-013` (número não reusa).
**Eventos:** `Certificados.Cancelado`.

---

### `POST /v1/certificados/{id}/etiquetas`
**Request:** `{ "tamanho": "50x30" }`
**Response 201:** `{ "etiqueta_id": "...", "pdf_url": "...", "qr_token": "opaco", "url_publica": "/v/{token}" }`.

---

### `POST /v1/certificados/{id}/envios`
**Request:** `{ "destinatario_email": "...", "canal": "EMAIL" }`
**Response 202:** envio agendado.
**Eventos:** `Certificados.Enviado` quando entregue.

---

### `POST /v1/certificados/{id}/envios/{envio_id}/retry`
**RBAC:** RT, admin.

---

### `POST /v1/templates`
**Request:** template completo (HTML + CSS + logo_id + cor + cabecalho + rodape + tipo_aplicavel).
**Response 201:** template inativo.

### `POST /v1/templates/{id}/ativar`
**Response 200:** template ativo; anterior desativada.

### `GET /v1/templates?tipo=...&ativo=...`
**Response 200:** lista.

---

### `POST /v1/nao-conformidades`
**Request:**
```json
{
  "origem": "CALIBRACAO",
  "referencia_id": "uuid",
  "descricao": "...",
  "acao_imediata": "...",
  "acao_corretiva_planejada": "...",
  "responsavel_id": "uuid",
  "prazo_fechamento": "2026-06-17"
}
```
**Response 201.**
**Eventos:** `Certificados.NCAberta`.

### `PATCH /v1/nao-conformidades/{id}/fechar`
**Request:** `{ "justificativa": "..." }`.

---

### Página pública verificadora

### `GET /v/{qr_token}`
**Auth:** NENHUMA.
**Response 200 (HTML):** página com status + dados mínimos não-PII.
**Rate limit:** 60 req/min/IP.
**Invariantes:** sem PII além do mínimo; IP hash + UA truncado registrados (LGPD).
**Eventos:** `Certificados.VerificacaoPublica`.

---

## Eventos consumidos

- `Calibracao.Aprovada` → habilita criação de certificado.
- `Licencas.BloqueioAtivado` (acreditação vencida) → bloqueia emissão RBC.
- `Licencas.DocumentoRenovado` (ART/RRT do RT) → reativa assinatura.

## Rate limits

- POST certificados: 30/min/tenant.
- POST assinatura: 20/min/tenant.
- GET /v/{token}: 60/min/IP.

## Versionamento

- v1/v2 coexistem 6 meses.
- Quebra → ADR.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR.
- Deprecado → header Sunset.
