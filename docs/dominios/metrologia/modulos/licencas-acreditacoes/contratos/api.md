---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Licenças e Acreditações

> Endpoints REST/RPC (formato final definido em ADR-0001).

---

## Convenções

- Path versionado: `/v1/licencas/`.
- Auth: header `Authorization: Bearer <token>`.
- Tenant: `X-Tenant-ID` ou claim do token (INV-TENANT-001).
- Erros: RFC 7807 Problem Details.
- Idempotência: mutações aceitam `Idempotency-Key`.
- Upload de anexos: `multipart/form-data` em endpoint dedicado retornando `anexo_id`.

---

## Endpoints

### `POST /v1/licencas/documentos`
**Propósito:** cadastrar novo documento regulatório.
**RBAC:** admin tenant.
**Request:**
```json
{
  "tipo": "ACREDITACAO_CGCRE",
  "numero": "CRL-0123",
  "orgao_emissor": "INMETRO/CGCRE",
  "data_emissao": "2026-01-15",
  "data_validade": "2030-01-14",
  "escopo": "Massa: 1mg-50kg; classes E2 a M3",
  "responsavel_id": "uuid-user",
  "bloqueante": true,
  "anexo_id": "uuid-anexo"
}
```
**Response 201:**
```json
{
  "id": "uuid-doc",
  "status": "VIGENTE",
  "revisao_atual_id": "uuid-rev",
  "alertas_agendados": [{"data": "2029-10-16", "janela_dias": 90}, ...]
}
```
**Códigos:** 201, 400 (input), 401, 403, 422 (validação — escopo obrigatório, anexo missing).
**Invariantes:** `INV-046`, `INV-001`, `INV-TENANT-001`, `INV-032`.
**US:** `US-LIC-001`.
**Eventos:** `Licencas.DocumentoCadastrado`.

---

### `GET /v1/licencas/documentos`
**Propósito:** listar documentos com filtros.
**RBAC:** admin, responsável conformidade, auditor (leitura).
**Query params:** `tipo`, `status`, `bloqueante`, `responsavel_id`, `vence_em_dias`, `page`, `page_size`.
**Response 200:**
```json
{
  "items": [{"id": "uuid", "tipo": "...", "status": "VIGENTE", "data_validade": "2030-01-14", ...}],
  "total": 42,
  "page": 1
}
```

---

### `GET /v1/licencas/documentos/{id}`
**Propósito:** detalhe do documento + revisões + alertas + bloqueios.
**Response 200:** payload completo com sub-recursos embed (resumidos) e links pra coleções completas.

---

### `POST /v1/licencas/documentos/{id}/revisoes`
**Propósito:** registrar renovação.
**RBAC:** admin.
**Request:**
```json
{
  "data_emissao": "2030-01-10",
  "data_validade": "2034-01-09",
  "anexo_id": "uuid-novo-anexo",
  "motivo": "RENOVACAO",
  "observacao": "renovação ciclo 4 anos"
}
```
**Response 201:** revisão criada (imutável).
**Códigos:** 201, 400, 401, 403, 409 (revisão duplicada por idempotência).
**Invariantes:** `INV-001` (imutabilidade WORM).
**Eventos:** `Licencas.DocumentoRenovado`, possivelmente `Licencas.BloqueioResolvido`.

---

### `PATCH /v1/licencas/documentos/{id}`
**Propósito:** editar metadados não-imutáveis (`responsavel_id`, `bloqueante`, `observacao`).
**RBAC:** admin.
**Códigos:** 200, 400, 403, 422.
**Invariantes:** campos imutáveis bloqueados (`numero`, `data_emissao`, `data_validade` — esses só via revisão).

---

### `GET /v1/licencas/documentos/{id}/revisoes`
**Propósito:** histórico completo de renovações.
**RBAC:** admin, auditor.

---

### `GET /v1/licencas/alertas`
**Propósito:** lista de alertas (filtrar por status/destinatario).
**RBAC:** próprio destinatário + admin.

---

### `POST /v1/licencas/alertas/{id}/marcar-lido`
**Propósito:** marcar alerta como visualizado pelo destinatário.

---

### `POST /v1/licencas/bloqueios/{id}/modo-emergencial`
**Propósito:** liberar operação com documento bloqueante vencido.
**RBAC:** admin tenant (privilégio elevado).
**Request:**
```json
{
  "operacao_a_liberar": "emissao_certificado_rbc",
  "justificativa": "texto >= 50 chars",
  "janela_horas": 72,
  "assinatura_a3_id": "uuid-assinatura"
}
```
**Response 201:** evento criado + janela ativa.
**Códigos:** 201, 400, 403, 422 (assinatura A3 inválida/expirada).
**Invariantes:** `INV-001`, `INV-033` (modo emergencial: justificativa + A3 + WORM), exige A3 (ADR-0009).
**Eventos:** `Licencas.ModoEmergencialAcionado`.

---

### `POST /v1/licencas/relatorios/auditoria`
**Propósito:** gerar PDF consolidado.
**RBAC:** admin, auditor.
**Request:**
```json
{
  "data_corte": "2026-05-17",
  "tipos": ["ACREDITACAO_CGCRE", "ART", "CERT_DIGITAL_A3"],
  "incluir_historico_meses": 24
}
```
**Response 202:** job assíncrono; `Location: /v1/licencas/relatorios/{job_id}`.
**Response final 200:** `{pdf_url, sha256, gerado_em}`.

---

## Eventos consumidos de outros módulos

- `RT.HabilitacaoSuspensa` → marca ART/RRT vinculada como suspensa.
- Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- POST relatórios: 5/hora/tenant.
- Default: definido em ADR-0001.

## Versionamento

- v1 e v2 coexistem por 6 meses.
- Quebra contratual → ADR + CHANGELOG.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR.
- Deprecado → header Sunset.
