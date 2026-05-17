---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Onboarding

> Endpoints do módulo de implantação. Formato (REST) a confirmar em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação: `Authorization: Bearer <token>`.
- Tenant: header `X-Tenant-ID` (ou subdomain). `INV-TENANT-001` exige presença em toda query.
- Erros: RFC 7807 Problem Details.
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `POST /v1/onboarding/implantacoes`

**Propósito:** criar nova implantação pra tenant existente.
**Autorizado:** responsável interno, gestor.
**Request:**
```json
{
  "tenant_id": "uuid",
  "responsavel_interno_id": "uuid",
  "checklist_template_id": "uuid",
  "data_go_live_prevista": "2026-06-30"
}
```
**Response 201:**
```json
{
  "id": "uuid",
  "status": "nao_iniciada",
  "etapas": [ { "id": "uuid", "ordem": 1, "nome": "Cadastro empresa", "status": "nao_iniciada" } ]
}
```
**Erros:** 400, 401, 403, 409 (já existe implantação ativa para o tenant).
**Invariantes:** `INV-TENANT-001`, `INV-040` (status só avança em ordem definida).
**US:** `US-ONB-001`, `US-ONB-003`, `US-ONB-004`.
**Eventos:** `Onboarding.ImplantacaoCriada`.

---

### `GET /v1/onboarding/implantacoes`

**Propósito:** listar implantações com filtros.
**Query params:** `status`, `responsavel_id`, `inicio_data`, `fim_data`, `parada_ha_dias`.
**Response 200:** array paginado.

---

### `GET /v1/onboarding/implantacoes/{id}`

**Propósito:** detalhe completo (etapas, imports, inconsistências, treinamentos, validações, termo).

---

### `PATCH /v1/onboarding/implantacoes/{id}/etapas/{etapa_id}`

**Propósito:** mudar status de etapa.
**Request:**
```json
{ "status": "concluida", "observacoes": "..." }
```
**Response 200:** etapa atualizada.
**Invariantes:** `INV-041` (justificativa se "pulada").
**Eventos:** `Onboarding.EtapaConcluida`.

---

### `POST /v1/onboarding/implantacoes/{id}/importacoes`

**Propósito:** registrar nova importação (passo 1: validação).
**Request (multipart):** `tipo` (clientes/produtos/serviços/equipamentos/estoque), `arquivo` (CSV/XLSX).
**Response 201:** `{ id, status: "validando", hash_arquivo }`.
**Idempotência:** `Idempotency-Key` recomendado; `hash_arquivo` impede reprocessar mesma planilha duas vezes.
**Invariantes:** `INV-006`, `INV-TENANT-001`.

---

### `POST /v1/onboarding/importacoes/{id}/executar`

**Propósito:** executar import após validação OK.
**Response 200:** `{ resumo: { criados, duplicados, ignorados }, inconsistencias_geradas: N }`.
**Eventos:** `Onboarding.ImportacaoConcluida`.

---

### `GET /v1/onboarding/importacoes/{id}/inconsistencias`

**Propósito:** listar inconsistências de uma importação.
**Query params:** `severidade`, `status`.

---

### `PATCH /v1/onboarding/inconsistencias/{id}`

**Propósito:** resolver ou aceitar inconsistência.
**Request:**
```json
{ "status": "resolvida", "justificativa": "..." }
```
**Invariantes:** `INV-042` (justificativa obrigatória).

---

### `POST /v1/onboarding/implantacoes/{id}/treinamentos`

**Propósito:** registrar treinamento.
**Request:**
```json
{
  "data": "2026-06-10",
  "duracao_minutos": 90,
  "modulos_cobertos": ["chamados", "ordens-servico"],
  "participantes": [ { "nome": "...", "email": "..." } ],
  "anexos_urls": []
}
```
**US:** `US-ONB-006`.

---

### `POST /v1/onboarding/implantacoes/{id}/validacoes`

**Propósito:** rodar validação automática do ambiente.
**Response 200:**
```json
{
  "resultado": "passou",
  "checks": [
    { "nome": "rls_ativo", "resultado": "passou" },
    { "nome": "kms_configurado", "resultado": "passou" }
  ]
}
```
**Invariantes:** `SEC-001`, `SEC-KMS-*`.
**Eventos (se falhou):** `Onboarding.ValidacaoFalhou`.

---

### `POST /v1/onboarding/implantacoes/{id}/termo`

**Propósito:** gerar termo de aceite (PDF).
**Response 201:** `{ id_termo, pdf_url, hash_pdf }`. PDF salvo em Backblaze B2 WORM.

---

### `POST /v1/onboarding/termos/{id}/assinar`

**Propósito:** registrar assinatura do cliente.
**Request:**
```json
{ "assinante_nome": "...", "assinante_documento": "CPF", "assinatura_blob": "base64" }
```
**Response 200:** termo selado, implantação muda pra "concluída".
**Invariantes:** `INV-043` (imutável após assinar), `INV-001` (WORM).
**Eventos:** `Onboarding.TermoAssinado`.

---

### `POST /v1/onboarding/sandbox/{tenant_id}/promover`

**Propósito:** promover sandbox pra produção.
**Pré-condições:** termo assinado + última validação passou.
**Response 200:** `{ snapshot_id, data_promocao }`.
**Eventos:** `Onboarding.SandboxPromovido`.

---

## Rate limits

- Upload de import: 5 req/min/tenant.
- Validação ambiente: 10 req/hora/tenant.
- Default: a definir em ADR.

## Versionamento

- v1, v2 coexistem 6 meses.

## Como esta lista evolui

- Endpoint novo → linkar US + atualizar eventos.
- Quebra de contrato → ADR + janela migração + headers Sunset.
