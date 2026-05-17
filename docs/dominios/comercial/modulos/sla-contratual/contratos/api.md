---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo SLA Contratual

> Endpoints. Formato final (REST / GraphQL / RPC) em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Auth via Bearer.
- Tenant via header `X-Tenant-ID` (ou token); `INV-TENANT-001` exige presença.
- Erros formato RFC 7807.
- Idempotência via header `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/sla/perfis`
**Propósito:** criar perfil de SLA.
**Persona/papel:** comercial.
**Request:**
```json
{
  "nome": "Ouro 24/7",
  "tempo_resposta_min": 120,
  "tempo_solucao_min": 480,
  "calendario_id": "uuid",
  "regra_penalidade": {"tipo": "percentual_hora", "valor": 2.0, "teto_pct": 20},
  "regra_bonificacao": {"tipo": "percentual_mensal", "valor": 1.0, "condicao": "cumprimento_100"},
  "motivos_pausa_permitidos": ["AGUARDANDO_CLIENTE", "PECA_TRANSITO"]
}
```
**Response (201):**
```json
{"id": "uuid", "versao": 1, "status": "rascunho"}
```
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-TENANT-001`.
**US:** `US-SLA-001`.

---

### `POST /v1/sla/perfis/{id}/ativar`
**Propósito:** ativar perfil em rascunho.
**Response (200):** `{"id": "uuid", "status": "ativo", "versao": 1}`
**Códigos:** 200, 409 (já ativo), 422 (campos faltando).
**US:** `US-SLA-001`.

---

### `POST /v1/sla/perfis/{id}/nova-versao`
**Propósito:** criar nova versão de perfil ativo.
**Request:** mesmos campos do POST inicial (delta).
**Response (201):** `{"id": "uuid", "versao": 2, "status": "rascunho"}`
**US:** `US-SLA-001` (AC-001-2).

---

### `POST /v1/sla/vinculos`
**Propósito:** vincular perfil a contrato.
**Request:**
```json
{
  "contrato_id": "uuid",
  "perfil_sla_id": "uuid",
  "vigencia_inicio": "2026-06-01",
  "vigencia_fim": null,
  "overrides": null
}
```
**Response (201):** `{"id": "uuid", "perfil_sla_versao": 1}`
**Códigos:** 201, 409 (já existe vínculo sobreposto), 422.

---

### `POST /v1/sla/cronometros`
**Propósito:** iniciar cronômetro (chamado pelo módulo Chamados/OS).
**Request:**
```json
{
  "vinculo_id": "uuid",
  "referencia_tipo": "chamado",
  "referencia_id": "uuid",
  "aberto_em": "2026-05-17T10:30:00-03:00"
}
```
**Response (201):**
```json
{
  "evento_id": "uuid",
  "deadline_TR": "2026-05-17T12:30:00-03:00",
  "deadline_TS": "2026-05-17T18:30:00-03:00"
}
```
**Eventos disparados:** `SLA.Cronometrando`.

---

### `POST /v1/sla/cronometros/{id}/pausar`
**Propósito:** pausar SLA com motivo.
**Request:**
```json
{
  "motivo_codigo": "AGUARDANDO_CLIENTE",
  "motivo_descricao": "Cliente fora até 15h",
  "anexos": ["url-b2"]
}
```
**Response (200):** `{"pausa_id": "uuid", "iniciado_em": "..."}`
**Códigos:** 200, 422 (motivo não permitido pelo perfil), 409 (já pausado).
**Eventos:** `SLA.Pausado`.
**US:** `US-SLA-003`.

---

### `POST /v1/sla/cronometros/{id}/despausar`
**Propósito:** retomar SLA.
**Response (200):** `{"encerrado_em": "..."}`
**Eventos:** `SLA.Despausado`.
**US:** `US-SLA-003`.

---

### `POST /v1/sla/cronometros/{id}/cumprir`
**Propósito:** marcar cumprimento (chamado pelo módulo Chamados/OS na resolução).
**Request:** `{"resolvido_em": "...", "evidencias": [{"tipo": "foto", "url": "..."}]}`
**Response (200):** `{"TR_real_min": 90, "TS_real_min": 420, "status": "cumprido"}`
**Eventos:** `SLA.Cumprido`.

---

### `GET /v1/sla/cronometros?status=em_risco`
**Propósito:** listar SLAs em risco (≥ 80%).
**Response:** lista paginada.
**Persona:** Gerente.

---

### `POST /v1/sla/relatorios`
**Propósito:** gerar relatório SLA do cliente no período.
**Request:**
```json
{
  "cliente_id": "uuid",
  "periodo_inicio": "2026-05-01",
  "periodo_fim": "2026-05-31"
}
```
**Response (201):**
```json
{
  "relatorio_id": "uuid",
  "url_pdf": "url-b2",
  "hash": "sha256:...",
  "emitido_em": "..."
}
```
**Invariantes:** WORM após emissão.
**Eventos:** `SLA.RelatorioEmitido`.
**US:** `US-SLA-007`.

---

### `POST /v1/sla/relatorios/{id}/enviar`
**Propósito:** enviar relatório via Comunicação Omnichannel.
**Request:** `{"canal": "email", "destinatario": "cliente@..."}`
**Response (202):** `{"envio_id": "uuid", "status": "enfileirado"}`
**US:** `US-SLA-007` (AC-007-2).

---

### `GET /v1/sla/dashboards/cumprimento`
**Propósito:** dados agregados do dashboard.
**Query:** `?periodo_inicio=...&periodo_fim=...&cliente_id=...&equipe_id=...`
**Response:** estrutura agregada (totais, %).

---

## Eventos consumidos de outros módulos

- `Chamado.Aberto`, `OS.Aberta` → dispara `iniciarCronometroSLA`.
- `Chamado.Resolvido`, `OS.Encerrada` → dispara `cumprir`.
- Detalhes em `../../../comum/integracoes-inter-modulos.md`.

---

## Rate limits

- `POST /v1/sla/relatorios` — 10 req/min/tenant.
- `POST /v1/sla/cronometros/*` — sem limite estrito (operacional crítico); circuit breaker em caso de surto.
- Default: a definir em ADR-0001.

---

## Versionamento

- v1 e v2 coexistem por 6 meses.
- Quebra de contrato → ADR + CHANGELOG seção "Modificado/Removido".

---

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US.
- Quebra → ADR + Sunset header (RFC 8594).
- Endpoint descontinuado → `@deprecated`.
