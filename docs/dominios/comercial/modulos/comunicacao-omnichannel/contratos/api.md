---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/comum/integracoes-externas/whatsapp.md
---

# Contratos de API — Módulo Comunicação Omnichannel

> Endpoints internos + webhooks de canais externos. Formato (REST / GraphQL / RPC) em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Auth via Bearer.
- Tenant via header `X-Tenant-ID` (ou token); `INV-TENANT-001`.
- Erros formato RFC 7807.
- Idempotência via `Idempotency-Key` em mutações (especialmente envio de mensagem).
- Webhooks externos têm endpoint sem auth de tenant — autenticados por assinatura HMAC do provedor.

---

## Endpoints

### `POST /v1/comunicacao/mensagens`
**Propósito:** enviar mensagem (saída).
**Persona/papel:** atendente, regra automação.
**Request:**
```json
{
  "thread_id": "uuid",
  "tipo": "texto",
  "conteudo": "Olá, segue o orçamento.",
  "template_id": null,
  "variaveis_template": null,
  "anexos": []
}
```
Ou com template:
```json
{
  "cliente_id": "uuid",
  "canal_id": "uuid",
  "tipo": "template",
  "template_id": "uuid",
  "variaveis_template": {"cliente.nome": "João", "os.numero": "12345"}
}
```
**Response (202):** `{"mensagem_id": "uuid", "status_inicial": "enviada"}`
**Códigos:** 202, 400, 403 (sem opt-in para promocional), 422 (template não aprovado), 429.
**Invariantes:** `INV-TENANT-001`; bloqueia se cliente em opt-out para canal+tipo.
**Eventos:** `Comunicacao.MensagemEnviada`.
**US:** `US-COM-001`, `US-COM-004`.

---

### `POST /v1/comunicacao/webhooks/{canal_tipo}`
**Propósito:** receber callback do canal externo (mensagem entrada, status, opt-out).
**Auth:** assinatura HMAC do provedor (não tenant header).
**Request:** payload do provedor (varia).
**Response:** 200 OK rápido (processamento assíncrono via fila `procrastinate`).
**Eventos:** `Comunicacao.MensagemRecebida`, `Comunicacao.StatusMensagemAtualizado`, `Comunicacao.OptOutAplicado` (detecção de palavra-chave).

---

### `GET /v1/comunicacao/conversas`
**Propósito:** listar conversas (caixa unificada).
**Query:** `?status=&canal=&atendente=&cliente_id=&q=&page=`
**Response:** paginada.

---

### `GET /v1/comunicacao/conversas/{id}`
**Propósito:** detalhe + mensagens.
**Response:**
```json
{
  "conversa": {...},
  "threads": [...],
  "mensagens": [...],
  "cliente": {...},
  "consentimentos": [...]
}
```

---

### `POST /v1/comunicacao/conversas/{id}/atribuir`
**Request:** `{"atendente_id": "uuid"}` ou `{"regra": "auto"}`
**Response:** `{"atendente_id": "uuid"}`
**US:** `US-COM-007`.

---

### `POST /v1/comunicacao/conversas/{id}/converter-em-chamado`
**Request:** `{"descricao": "...", "categoria_id": "..."}`
**Response (201):** `{"chamado_id": "uuid"}`
**Eventos:** `Comunicacao.ConvertidoEmChamado`.
**US:** `US-COM-008`.

---

### `POST /v1/comunicacao/conversas/{id}/converter-em-lead`
**Request:** `{"origem": "...", "responsavel_id": "..."}`
**Response (201):** `{"lead_id": "uuid"}`
**Eventos:** `Comunicacao.ConvertidoEmLead`.
**US:** `US-COM-009`.

---

### `POST /v1/comunicacao/conversas/{id}/resolver`
**Response (200):** `{"resolvida_em": "..."}`

---

### `POST /v1/comunicacao/templates`
**Request:**
```json
{
  "nome": "os-encerrada-v1",
  "canal_tipo": "whatsapp",
  "corpo": "Olá {{cliente.nome}}, sua OS {{os.numero}} foi encerrada.",
  "variaveis": ["cliente.nome", "os.numero"]
}
```
**Response (201):** `{"id": "uuid", "versao": 1, "status": "rascunho"}`
**US:** `US-COM-004`.

---

### `POST /v1/comunicacao/templates/{id}/submeter`
**Propósito:** enviar para aprovação no canal externo (ex: Meta).
**Response (200):** `{"status": "pendente", "external_id": "..."}`

---

### `POST /v1/comunicacao/consentimentos`
**Request:**
```json
{
  "cliente_id": "uuid",
  "canal_tipo": "whatsapp",
  "tipo": "opt_in",
  "base_legal": "consentimento",
  "texto_apresentado": "...",
  "texto_resposta_cliente": "ACEITO",
  "referencia_mensagem_id": "uuid"
}
```
**Response (201):** `{"id": "uuid"}`
**Invariantes:** WORM.
**Eventos:** `Comunicacao.ConsentimentoRegistrado`.
**US:** `US-COM-002`, `US-COM-003`.

---

### `GET /v1/comunicacao/consentimentos?cliente_id=...`
**Propósito:** auditar consentimentos.
**Response:** lista WORM.

---

### `POST /v1/comunicacao/regras-automacao`
**Request:**
```json
{
  "evento_gatilho": "OS.Encerrada",
  "condicao": {"tenant_id": "..."},
  "template_id": "uuid",
  "canal_preferido": "whatsapp",
  "fallback_canais": ["sms", "email"]
}
```
**Response (201):** `{"id": "uuid", "status": "ativo"}`
**US:** `US-COM-006`.

---

### `GET /v1/comunicacao/dashboards/atendimento`
**Query:** `?periodo_inicio=&periodo_fim=&canal=&atendente=`
**Response:** agregação.
**US:** `US-COM-011`.

---

## Eventos consumidos de outros módulos

Lista completa em `../modelo-de-dominio.md`. Resumo:
- `OS.*`, `Orcamento.*`, `Chamado.*`, `SLA.*`, `Calibracao.*` → potenciais gatilhos de regras de automação.
- Ver `../../../comum/integracoes-inter-modulos.md`.

---

## Rate limits

- `POST /v1/comunicacao/mensagens` — limite por tenant + limite imposto pelo canal externo (WhatsApp tem tier-rate-limit da Meta).
- Webhooks externos — sem limite (o sistema deve absorver).
- Disparo em massa via regra → fila `procrastinate` com backoff.

---

## Versionamento

- v1 e v2 coexistem por 6 meses.
- Quebra → ADR + Sunset header.

---

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR.
- Endpoint descontinuado → `@deprecated`.
