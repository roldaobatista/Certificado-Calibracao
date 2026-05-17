---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Configurações do Sistema

> Endpoints da central de configurações.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação: `Authorization: Bearer <token>`.
- Tenant: `X-Tenant-ID` obrigatório. `INV-TENANT-001` (ADR-0002).
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.
- Auditoria: toda mutação em config sensível dispara `Config.MudancaSensivelRegistrada` (SEC-005).

---

## Endpoints

### `GET /v1/config/empresa`

**Propósito:** ler dados da empresa do tenant.
**Response 200:** `{ id, razao_social, cnpj, ie, endereco, regime_tributario, logo_url }`.

---

### `PATCH /v1/config/empresa`

**Propósito:** atualizar dados.
**Request:** subset de campos.
**Response 200:** dados atualizados.
**Eventos:** `Config.EmpresaAtualizada`, `Config.MudancaSensivelRegistrada`.
**Invariantes:** `INV-036`.

---

### `GET /v1/config/filiais` / `POST` / `PATCH /{id}` / `DELETE /{id}`

**Propósito:** CRUD de filiais.
**Invariantes:** `INV-037` (exatamente 1 matriz).

---

### `GET /v1/config/series` / `POST` / `PATCH /{id}`

**Propósito:** CRUD de séries de documento.
**Invariantes:** `INV-028` (proximo_numero só cresce — `PATCH` que diminui retorna 422).
**US:** `US-CFG-002`.

---

### `GET /v1/config/impostos` / `POST` / `PATCH /{id}` (com vigência)

**Propósito:** gestão de alíquotas/CFOP/NCM padrão.
**Invariantes:** `INV-026` (imutabilidade pós-uso — `PATCH` que afetaria documento emitido retorna 409; versionamento de catálogo).
**US:** `US-CFG-003`.

---

### `GET /v1/config/papeis` / `POST` / `PATCH /{id}` / `DELETE /{id}`

**Propósito:** gestão de papéis (RBAC).
**Invariantes:** `INV-029`, `SEC-LEAST-PRIV-001`.
**US:** `US-CFG-004`.
**Eventos:** `Config.PapelAtualizado` (invalida cache RBAC).

---

### `GET /v1/config/papeis/{id}/permissoes` / `PUT`

**Propósito:** ler/sobrescrever matriz de permissões do papel.

---

### `GET /v1/config/workflows?entidade=os` / `POST` / `POST /{id}/versionar`

**Propósito:** gerir workflows por entidade. Mudança gera nova versão (não in-place).
**US:** `US-CFG-005`.
**Eventos:** `Config.WorkflowVersionado`.

---

### `GET /v1/config/status?entidade=chamado` / `POST` / `PATCH /{id}` / `POST /{id}/deprecar`

**Propósito:** gestão de status personalizados.
**Invariantes:** `INV-038` (não excluir se em uso; apenas deprecar).

---

### `GET /v1/config/campos-obrigatorios?entidade=os` / `PUT`

**Propósito:** definir campos obrigatórios por entidade.
**US:** `US-CFG-006`.

---

### `GET /v1/config/modelos-pdf` / `POST` / `PATCH /{id}` / `POST /{id}/ativar`

**Propósito:** gerir modelos de PDF.
**Invariantes:** `INV-001` (WORM — documentos antigos não regerados; template usado faz parte do snapshot).
**US:** `US-CFG-007`.

---

### `GET /v1/config/assinatura` / `PUT`

**Propósito:** config de assinatura A3 + posição.
**Invariantes:** ADR-0009, `SEC-A3-001`.
**US:** `US-CFG-008`.

---

### `GET /v1/config/integracoes` / `POST` / `PATCH /{id}` / `POST /{id}/testar` / `POST /{id}/ativar` / `POST /{id}/desativar`

**Propósito:** gestão de integrações.
**Detalhes:**
- Credenciais nunca expostas em GET (apenas referência KMS).
- `POST /{id}/testar` exige antes de ativar.
**Invariantes:** `SEC-KMS-001`, `SEC-005`.
**Eventos:** `Config.IntegracaoAtivada`, `Config.IntegracaoDesativada`.
**US:** `US-CFG-009`.

---

### `GET /v1/config/notificacoes` / `PUT`

**Propósito:** mapeamento evento → canal → destinatários.
**US:** `US-CFG-010`.

---

### `GET /v1/config/regras-comerciais` / `POST` / `PATCH /{id}`

**Propósito:** descontos máximos, alçadas.
**US:** `US-CFG-011`.

---

### `GET /v1/config/sla` / `POST` / `PATCH /{id}`

**Propósito:** SLAs por tipo de chamado/contrato/cliente.
**US:** `US-CFG-011`.

---

### `GET /v1/config/operacional/{dominio}` / `PUT` (dominio = estoque|financeiro|metrologia)

**Propósito:** parâmetros operacionais.
**US:** `US-CFG-012`.

---

### `GET /v1/config/backup` / `PUT` / `POST /forcar`

**Propósito:** config de backup + execução forçada.
**Invariantes:** `SEC-006`.
**US:** `US-CFG-013`.

---

### `GET /v1/config/retencao` / `PUT`

**Propósito:** retenção por entidade.
**Invariantes:** `INV-039` (não abaixo do mínimo legal).
**US:** `US-CFG-013`.
**Eventos:** `Config.RetencaoAjustada`.

---

### `GET /v1/config/features` / `PUT /{codigo}`

**Propósito:** ligar/desligar features liberadas pro plano.
**Invariantes:** `INV-030`, ADR-0006.
**US:** `US-CFG-014`.
**Eventos:** `Config.FeatureLigada`.

---

### `GET /v1/config/auditoria?entidade=...&desde=...`

**Propósito:** consultar histórico de mudanças.
**Response 200:** array de `AuditoriaConfig` ordenado por data desc.
**Invariantes:** `SEC-005`.

---

## Rate limits

- Mutações em config crítica (RBAC, fiscal, retenção, KMS): 30 req/min/tenant.
- Leitura: alta (cacheada).

## Versionamento

- v1, v2 coexistem 6 meses.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra de contrato → ADR + Sunset header.
