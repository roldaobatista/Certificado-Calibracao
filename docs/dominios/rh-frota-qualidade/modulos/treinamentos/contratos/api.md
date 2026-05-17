---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
modulo: treinamentos
---

# Contratos de API — Módulo Treinamentos e Certificações Internas

> Endpoints REST presumidos (ADR-0001 candidata).

---

## Convenções

- Path: `/v1/treinamentos/`.
- Auth: `Authorization: Bearer <token>`.
- Tenant: `X-Tenant-ID` (`INV-TENANT-001`).
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/treinamentos/catalogo`
**Propósito:** cadastrar treinamento.
**Request:**
```json
{ "nome": "NR-35 — Trabalho em Altura", "categoria": "seguranca", "sub_categoria": "NR-35", "carga_horaria": 8, "validade_padrao_meses": 24 }
```
**Response (201):** `{ "id": "uuid", ... }`
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-001`, `INV-TENANT-001`.
**US:** `US-TRE-001`.

---

### `GET /v1/treinamentos/catalogo?categoria=seguranca`
**Resposta:** lista paginada.

---

### `POST /v1/treinamentos/eventos`
**Propósito:** programar evento.
**Request:**
```json
{ "treinamento_catalogo_id": "uuid", "data_inicio": "2026-06-01T08:00", "data_fim": "2026-06-01T17:00", "local": "Sala A", "facilitador_id": "uuid", "participantes": ["col-uuid-1","col-uuid-2"] }
```
**Códigos:** 201, 422.
**Invariantes:** `INV-001`.
**US:** `US-TRE-002`.

---

### `POST /v1/treinamentos/eventos/{id}/participacoes`
**Propósito:** registrar presença / nota.
**Request:**
```json
{ "colaborador_id": "uuid", "presenca_percentual": 100, "nota": 9.0, "aprovado": true }
```
**Códigos:** 201, 422.
**US:** `US-TRE-003`.

---

### `POST /v1/treinamentos/eventos/{id}/concluir`
**Propósito:** marcar evento como concluído (libera emissão).
**US:** `US-TRE-003`.

---

### `POST /v1/treinamentos/certificados`
**Propósito:** emitir certificado.
**Request:** `{ "participacao_id": "uuid" }`
**Response (201):** `{ "id", "pdf_url", "hash", "validade": "2028-06-01" }`
**Códigos:** 201, 409 (não aprovado), 422.
**Invariantes:** `INV-001` (imutável após emissão).
**Eventos:** `Treinamentos.CertificadoEmitido`.
**US:** `US-TRE-004`.

---

### `POST /v1/treinamentos/trilhas`
**Propósito:** criar / versionar trilha.
**Request:**
```json
{ "escopo": "equipamento_modelo", "referencia_escopo": "uuid-modelo", "itens": [ { "treinamento_catalogo_id": "uuid", "obrigatorio": true, "ordem": 1 } ] }
```
**Códigos:** 201, 422.
**Invariantes:** `INV-001`; versionada.
**US:** `US-TRE-005`.

---

### `GET /v1/treinamentos/matriz-competencia?funcao=tecnico-calibrador`
**Propósito:** matriz consolidada.
**Response:**
```json
{ "colaboradores": [...], "habilidades": [...], "celulas": [ {"col":"uuid","hab":"uuid","status":"valido","validade":"2027-01-01"} ] }
```
**US:** `US-TRE-006`.

---

### `GET /v1/treinamentos/colaboradores/{id}/habilitacao?escopo=equipamento_modelo&referencia=uuid`
**Propósito:** consulta crítica usada por `operacao` e `calibracao` antes de alocar técnico / emitir certificado.
**Response:**
```json
{ "apto": false, "motivo": "trilha incompleta", "lacunas": ["NR-10 vencida em 2026-03-10","Treinamento Balanca Mecanica não realizado"] }
```
**SLO:** p95 < 200ms (caminho crítico).
**Invariantes:** suporta `INV-002`, `INV-003` na emissão de certificado de calibração.
**US:** `US-TRE-007`.

---

### `POST /v1/treinamentos/bypass`
**Propósito:** liberação excepcional.
**Request:**
```json
{ "colaborador_id": "uuid", "escopo": "norma", "referencia_escopo": "ISO-17025", "justificativa": "...", "expira_em": "2026-06-30" }
```
**Pré-condição:** chamador tem papel "aprovador-qualidade".
**Códigos:** 201, 403, 422.
**Invariantes:** `INV-001`; expira automaticamente.
**Eventos:** `Treinamentos.BypassExecutado`.
**US:** `US-TRE-007` AC-3.

---

### `GET /v1/treinamentos/alertas?dias=30`
**Propósito:** vencimentos próximos.
**US:** `US-TRE-008`.

---

### `GET /v1/treinamentos/colaboradores/{id}/historico`
**Propósito:** linha do tempo.
**US:** `US-TRE-009`.

---

### `POST /v1/treinamentos/eventos/reciclagem`
**Propósito:** programar reciclagem a partir de certificados a vencer.
**Request:** `{ "certificados_ids": [...] }` (auto-gera evento herdando turma).
**US:** `US-TRE-010`.

---

## Eventos consumidos

- `Colaboradores.ColaboradorDesligado` → marca habilitações como históricas.
- `Operacao.OSCriada` (de risco/calibração) → consulta `consultarHabilitacao` antes de alocar.
- `Calibracao.SolicitacaoEmissaoCertificado` → consulta antes de gerar PDF (`INV-002`, `INV-003`).

Detalhes em `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `GET /habilitacao` — alto throughput; default 600/min/tenant.
- Default: a definir ADR-0001.

## Versionamento

- v1 → v2 coexistem 6 meses.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela de migração.
