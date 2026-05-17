---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0004-sync-offline-first.md
---

# Contratos de API — Módulo App do Técnico

> Endpoints REST consumidos pelo app Flutter. Sync é orientado a delta + idempotência.

---

## Convenções

- Versionamento via path (`/v1/`).
- Auth: header `Authorization: Bearer <token>`; refresh token persistido no Keychain/Keystore.
- Tenant: dentro do token (`tenant_id` claim). `INV-TENANT-001` exige presença em toda query no backend.
- Erros: RFC 7807 Problem Details.
- Idempotência: TODA mutação aceita `Idempotency-Key` header (UUID gerado no app).
- Sync usa timestamp de servidor (`If-Modified-Since`) + `client_op_id` pra dedup.

---

## Endpoints

### `GET /v1/app/agenda?data=YYYY-MM-DD`
**Propósito:** retorna agenda do dia do técnico autenticado.
**Persona/papel:** Técnico (RBAC).
**Response (sucesso 200):**
```json
{
  "data": "2026-05-17",
  "itens": [
    {"id": "uuid", "horario": "08:00", "tipo": "OS", "cliente": "...", "endereco": "...", "os_id": "uuid"}
  ],
  "snapshot_servidor_em": "2026-05-17T07:42:11Z"
}
```
**US:** `US-APP-001`.
**Invariantes:** `INV-TENANT-001`.

---

### `POST /v1/app/checkin`
**Propósito:** registra chegada.
**Request:**
```json
{
  "client_op_id": "uuid",
  "os_id": "uuid",
  "timestamp": "2026-05-17T09:12:33Z",
  "gps": {"lat": -23.55, "lng": -46.63, "precisao_m": 8},
  "foto_url": null,
  "justificativa_manual": null
}
```
**Response:** 201 com `{id, distancia_endereco_m}`.
**Códigos:** 201, 400, 401, 403, 409 (já existe checkin com mesmo client_op_id — devolve o existente).
**Eventos:** `AppTecnico.CheckInRealizado`.
**US:** `US-APP-003`.

---

### `POST /v1/app/deslocamento`
**Propósito:** registra início/pausa/retomada/fim.
**Request:**
```json
{
  "client_op_id": "uuid",
  "os_id": "uuid",
  "evento": "iniciar|pausar|retomar|chegar",
  "timestamp": "...",
  "gps": {...}
}
```
**Response:** 200 com deslocamento atualizado.
**US:** `US-APP-002`.

---

### `POST /v1/app/servico-executado`
**Propósito:** marca serviço feito.
**US:** `US-APP-004`.

---

### `POST /v1/app/consumo-peca`
**Propósito:** baixa de peça do veículo.
**Request:**
```json
{
  "client_op_id": "uuid",
  "os_id": "uuid",
  "peca_id": "uuid",
  "quantidade": 2,
  "veiculo_origem_id": "uuid",
  "timestamp": "..."
}
```
**Códigos:** 201, 409 (saldo insuficiente — devolve saldo atual servidor).
**Eventos:** `AppTecnico.PecaConsumida`.

---

### `POST /v1/app/solicitacao-peca`
**Propósito:** pede peça à base.
**Eventos:** `AppTecnico.PecaSolicitada`.
**US:** `US-APP-005`.

---

### `POST /v1/app/transferencia-estoque/{id}/aceitar`
**Propósito:** técnico destino aceita transferência.
**US:** `US-APP-005`.

---

### `POST /v1/app/foto`
**Propósito:** upload foto (multipart).
**Request (multipart):** `arquivo`, `os_id`, `categoria`, `gps`, `timestamp`.
**Response:** 201 com URL Backblaze B2.
**Invariantes:** imutável após upload.
**US:** `US-APP-006`.

---

### `POST /v1/app/checklist`
**Propósito:** envia execução de checklist.
**US:** `US-APP-006`.

---

### `POST /v1/app/assinatura-aceite`
**Propósito:** envia assinatura + PDF gerado.
**Request multipart:** `imagem_assinatura`, `pdf_aceite`, `os_id`, `nome_cliente`, `cpf_cliente`.
**Non-goal:** NÃO é A3 — ver ADR-0009.
**US:** `US-APP-007`.

---

### `POST /v1/app/despesa`
**Propósito:** lança despesa.
**Eventos:** `AppTecnico.DespesaLancada`.
**US:** `US-APP-008`.

---

### `POST /v1/app/adiantamento`
**Propósito:** solicita adiantamento.
**Eventos:** `AppTecnico.AdiantamentoSolicitado`.
**US:** `US-APP-009`.

---

### `POST /v1/app/prestacao-contas`
**Propósito:** fecha viagem.
**US:** `US-APP-009`.

---

### `GET /v1/app/chat/threads`
**Propósito:** lista threads do técnico.
**US:** `US-APP-010`.

### `POST /v1/app/chat/threads/{id}/mensagem`
**Propósito:** envia mensagem.
**US:** `US-APP-010`.

---

### `POST /v1/app/sync/lote`
**Propósito:** envia lote de operações offline em batch.
**Request:**
```json
{
  "operacoes": [
    {"tipo": "checkin", "client_op_id": "uuid", "payload": {...}},
    {"tipo": "consumo_peca", "client_op_id": "uuid", "payload": {...}}
  ]
}
```
**Response:**
```json
{
  "resultados": [
    {"client_op_id": "uuid", "status": "ok", "id_servidor": "uuid"},
    {"client_op_id": "uuid", "status": "conflito", "diff": {...}}
  ]
}
```
**Códigos:** 200 (com resultados parciais), 207 Multi-Status preferido.
**Invariantes:** idempotência por `client_op_id`.
**US:** `US-APP-012`, `US-APP-013`.

---

### `POST /v1/app/sync/conflito/{client_op_id}/resolver`
**Propósito:** resolve conflito (decisão do técnico/coordenador).
**Request:** `{decisao: "manter_local"|"aceitar_servidor"|"merge_customizado", payload?: {...}}`.
**US:** `US-APP-013`.

---

## Eventos consumidos de outros módulos

- `OS.AtribuidaTecnico` → app atualiza agenda.
- `Estoque.SaldoVeiculoAtualizado` → app refresca saldo local pós-sync.
Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /v1/app/sync/lote` — 60 req/min/dispositivo.
- `POST /v1/app/foto` — 30 req/min/dispositivo.
- Demais: default a definir em ADR-0001.

## Versionamento

- v1, v2 coexistem 6 meses.
- Quebra de contrato → ADR + bump CHANGELOG + comunicação aos apps em produção (app força atualização).

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra de contrato → ADR + janela de migração.
- Endpoint `@deprecated` → headers Sunset (RFC 8594).
