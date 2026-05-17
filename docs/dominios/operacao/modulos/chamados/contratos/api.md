---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: chamados
dominio: operacao
---

# Contratos de API — Módulo Chamados

> REST por padrão. Tenant via header. `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/chamados`
**Propósito:** abrir chamado.
**Papéis:** atendente, gerente, sistema (handler webhook WhatsApp).
**Request:**
```json
{
  "canal_origem": "whatsapp",
  "cliente_id": "uuid",
  "equipamento_id": "uuid",
  "texto_inicial": "..."
}
```
**Response 201:** `{"id": "uuid", "estado": "ABERTO", "duplicados_sugeridos": [...]}`
**Erros:** 400, 422 (cliente inválido).
**Invariantes:** RAT-03 (mascarar telefone), RAT-08. **Evento:** `ChamadoAberto`.

---

### `POST /v1/chamados/{id}/triagem`
**Propósito:** ABERTO → TRIADO. SLA é calculado a partir de `SLAConfig` do tenant.
**Request:**
```json
{"tipo": "calibracao", "urgencia": "media", "equipamento_id": "uuid"}
```
**Response 200:** chamado com `sla_alvo_at` setado.
**Erros:** 409 (estado inválido), 422 (tipo desconhecido).
**Evento:** `ChamadoTriado`.

---

### `POST /v1/chamados/{id}/duplicados/check`
**Propósito:** consulta detecção de duplicados (também chamada em background ao abrir).
**Request:** `{"cliente_id": "...", "equipamento_id": "...", "janela_dias": 7}`
**Response 200:** `{"duplicados": [{"id": "...", "criado_at": "...", "score_similaridade": 0.85}]}`
**Nunca mescla sozinho — apenas sugere.**

---

### `POST /v1/chamados/{id}/duplicado-de`
**Propósito:** humano confirma duplicado.
**Request:** `{"original_id": "uuid"}`
**Response 200:** `duplicado_de_id` setado. **NÃO apaga** o novo chamado.

---

### `POST /v1/chamados/{id}/converter-em-os`
**Propósito:** TRIADO/EM_ANDAMENTO → FECHADO + cria OS RASCUNHO com `os_origem_chamado_id`.
**Request:** `{"tipo_os": "calibracao", "prazo_prometido": "2026-05-25"}`
**Response 201:** `{"chamado": {...FECHADO}, "os": {...RASCUNHO}}`.
**Evento:** `ChamadoConvertidoEmOS` + `OSAberta` (cascade).

---

### `POST /v1/chamados/{id}/fechar`
**Propósito:** fecha sem OS.
**Request:** `{"razao": "orientação por telefone resolveu"}`
**Erros:** 422 (razão vazia). **Evento:** `ChamadoFechado`.

---

### `POST /v1/chamados/{id}/atribuir`
**Request:** `{"atribuido_a": "uuid_atendente"}`. Limpa flags de escalonamento.

---

### `GET /v1/chamados/{id}` / `GET /v1/chamados`
Lista paginada. Filtros: `estado`, `canal`, `atribuido_a`, `urgencia`, `sla_consumido_min`. Ordenação default: `sla_alvo_at asc` (mais críticos primeiro).

---

### `POST /v1/chamados/webhook/whatsapp`
**Propósito:** receber mensagens do WhatsApp Business API.
**Auth:** secret HMAC.
**Comportamento:** identifica cliente pelo telefone; abre chamado novo OR adiciona mensagem ao chamado aberto desse cliente em 24h.

---

## Job de escalonamento SLA (interno)

Cron a cada 1 min: roda regra documentada em `../modelo-de-dominio.md` (75% notifica, 100% escala). **Não é endpoint público** — métrica de saúde em `metricas.md`.

## Eventos consumidos

- `ClienteCriado` (Comercial) → atualizar caches de busca.

## Rate limits

- `POST /chamados` — 120 req/min/tenant.
- Webhook WhatsApp — 600 req/min (limite de provedor).

## Versionamento

v1 e v2 coexistem 6 meses. ADR pra quebras.

## Como evolui

Endpoint novo → linkar US.
