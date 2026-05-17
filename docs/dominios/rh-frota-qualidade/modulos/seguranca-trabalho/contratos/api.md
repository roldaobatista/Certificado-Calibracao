---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: seguranca-trabalho
---

# Contratos de API — Módulo Segurança do Trabalho

> Endpoints. Formato REST presumido (ADR-0001 candidata).

---

## Convenções

- Versionamento via path `/v1/sst/`.
- Auth via `Authorization: Bearer <token>`.
- Tenant via header `X-Tenant-ID` (`INV-TENANT-001` exige no WHERE).
- Erros: RFC 7807 Problem Details.
- Mutação aceita `Idempotency-Key`.

---

## Endpoints

### `POST /v1/sst/epis`
**Propósito:** cadastrar EPI.
**Persona:** Gerente SST.
**Request body:**
```json
{ "nome": "Capacete classe B", "numero_ca": "12345", "validade_ca": "2027-12-31", "fornecedor": "X", "categoria": "cabeca" }
```
**Response (201):** `{ "id": "uuid", ... }`
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-001`, `INV-TENANT-001`.
**US:** `US-SST-001`.

---

### `POST /v1/sst/epis/{id}/entregas`
**Propósito:** entregar EPI a colaborador com assinatura.
**Request:**
```json
{ "colaborador_id": "uuid", "quantidade": 1, "validade_individual": "2026-11-17", "assinatura_payload": "<base64 ou code>" }
```
**Response (201):** `{ "id": "uuid", "termo_pdf_url": "...", "hash": "sha256:..." }`
**Códigos:** 201, 400, 409 (CA vencido), 422.
**Invariantes:** `INV-001`, `INV-017` (assinatura), `INV-TENANT-001`.
**Eventos:** `SST.EPIEntregue`.
**US:** `US-SST-002`.

---

### `GET /v1/sst/alertas?dias=30`
**Propósito:** listar alertas (EPIs / ASOs / treinamentos a vencer).
**Response:** `{ "vencidos": [...], "ate_30d": [...], "ate_60d": [...], "ate_90d": [...] }`.
**US:** `US-SST-003`.

---

### `POST /v1/sst/aso`
**Propósito:** registrar ASO.
**Request:** `{ "colaborador_id", "tipo", "data_emissao", "validade", "medico", "crm", "resultado", "restricoes", "pdf_base64" }`
**Códigos:** 201, 400, 422.
**Invariantes:** `INV-001`; LGPD sensível (saúde).
**US:** `US-SST-003`.

---

### `POST /v1/sst/permissao-trabalho`
**Propósito:** emitir PT.
**Request:** `{ "os_id", "tipo", "executante_id", "validade_ate", "descricao_servico", "medidas_controle" }`
**Response (201):** `{ "id", "qr_code_url" }`
**Invariantes:** `INV-001`.
**US:** `US-SST-006`.

---

### `POST /v1/sst/apr`
**Propósito:** preencher APR.
**Request:** `{ "os_id", "template_id", "campos_preenchidos": {...}, "assinatura_payload" }`
**Invariantes:** `INV-001`.
**US:** `US-SST-007`.

---

### `POST /v1/sst/checklists`
**Propósito:** preencher checklist pré-OS.
**Request:** `{ "os_id", "template_id", "respostas": {...} }`
**Response (201) + liberação para iniciar OS.**
**Erros 422 com lista de itens obrigatórios faltando.**
**Invariantes:** `INV-001`.
**US:** `US-SST-005`.

---

### `GET /v1/sst/tecnicos/{id}/aptidao?tipo_os=NR-35`
**Propósito:** validar se técnico tem NR válida para tipo de OS.
**Response:** `{ "apto": false, "motivo": "NR-35 vencida em 2026-03-10" }`
**US:** `US-SST-004`.

---

### `POST /v1/sst/acidentes`
**Propósito:** registrar acidente / quase-acidente.
**Request:** `{ "tipo", "data_hora", "local", "descricao", "colaboradores_envolvidos": [...], "evidencias": [...], "gravidade", "houve_afastamento", "dias_afastamento", "acao_corretiva": {...}, "os_id"? }`
**Response (201):** `{ "id" }`.
**Invariantes:** `INV-001` (imutável após confirmação).
**Eventos:** `SST.AcidenteRegistrado`.
**US:** `US-SST-008`.

---

### `GET /v1/sst/relatorio?periodo=2026-Q1`
**Propósito:** relatório consolidado.
**Response:** payload com TF, TG, contagens, exportáveis.
**US:** `US-SST-009`.

---

## Eventos consumidos

- `Colaboradores.ColaboradorDesligado` → revoga EPIs ativos + flagga ASOs / treinamentos como históricos.
- `Treinamentos.CertificadoEmitido` (NR-*) → cria/atualiza `TreinamentoSegurancaAplicado`.
- `Operacao.OSCriada` → se OS de risco, exige PT + APR + checklist.

Detalhes em `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /sst/checklists` — 60/min/técnico.
- Default: a definir ADR-0001.

## Versionamento

- v1, v2 coexistem por 6 meses.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela de migração.
