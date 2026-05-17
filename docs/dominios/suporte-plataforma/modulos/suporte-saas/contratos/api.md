---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos API — Módulo Suporte SaaS

---

## Convenções

- REST sobre HTTPS.
- Autenticação: Bearer token com `tenant_id` claim.
- Tenant: middleware injeta + valida (`INV-TENANT-001`).
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key` em criação.

---

## Endpoints — Tickets

### `POST /v1/suporte/tickets`
**Propósito:** Abrir ticket.
**Request:**
```json
{
  "categoria": "bug",
  "titulo": "Botão Salvar não funciona",
  "descricao": "...",
  "prioridade_sugerida": "P3",
  "anexos": [{"storage_key": "...", "tipo": "screenshot"}]
}
```
**Response 201:**
```json
{"ticket_id":"uuid","numero_protocolo":"SUP-2026-001234","sla_deadline":"2026-05-17T18:00:00Z"}
```
**Códigos:** 201, 400, 401, 422.
**Eventos:** `ticket.aberto`.
**US:** `US-SUP-001`.

---

### `GET /v1/suporte/tickets`
**Propósito:** Listar tickets do tenant.
**Query:** `status`, `categoria`, `prioridade`, `aberto_por_usuario_id`, `page`.
**Códigos:** 200, 401.

---

### `GET /v1/suporte/tickets/{id}`
**Propósito:** Detalhe + mensagens.

---

### `POST /v1/suporte/tickets/{id}/mensagens`
**Propósito:** Responder no ticket.
**Request:**
```json
{"conteudo": "Tente F5 e me diga.", "anexos": [], "interna": false}
```
**Eventos:** `ticket.respondido`.

---

### `PATCH /v1/suporte/tickets/{id}/status`
**Propósito:** Mudar status.
**Request:** `{"status": "resolvido"}`
**Eventos:** `ticket.resolvido` (se aplicável).

---

### `POST /v1/suporte/tickets/{id}/csat`
**Propósito:** Avaliação pós-resolução.
**Request:** `{"nota": 5, "comentario": "Rápido"}`
**Eventos:** `ticket.csat_recebido`.

---

## Endpoints — Base de Conhecimento

### `GET /v1/suporte/bc/artigos`
**Propósito:** Listar/buscar artigos.
**Query:** `q`, `categoria`, `tags`, `page`.
**Auth:** opcional (usuário anônimo pode ler — artigo é global).

---

### `GET /v1/suporte/bc/artigos/{id}`
**Propósito:** Conteúdo do artigo.

---

### `POST /v1/suporte/bc/artigos/{id}/avaliar`
**Propósito:** "Resolveu?"
**Request:** `{"util": true, "comentario": "..."}`
**Métricas:** alimenta deflexão.

---

## Endpoints — Chat

### `POST /v1/suporte/chat/sessoes`
**Propósito:** Iniciar conversa.
**Response:** `{"sessao_id":"...","modo":"ia"}`

---

### `POST /v1/suporte/chat/sessoes/{id}/mensagens`
**Propósito:** Enviar mensagem.
**Response:** resposta (IA ou enfileirado humano).

---

### `POST /v1/suporte/chat/sessoes/{id}/handoff`
**Propósito:** Pedir humano.
**Eventos:** notifica fila atendentes.

---

## Endpoints — Acesso Remoto

### `POST /v1/suporte/acesso-remoto/sessoes`
**Propósito:** Atendente solicita acesso.
**Request:**
```json
{"tenant_id":"...","ticket_id":"...","motivo":"...","ttl_minutos":120}
```
**Response 201:** sessão em status "pendente_autorizacao".
**Eventos:** `sessao_remota.solicitada`.
**US:** `US-SUP-007`.

---

### `POST /v1/suporte/acesso-remoto/sessoes/{id}/autorizar`
**Propósito:** Tenant admin autoriza.
**Auth:** apenas tenant admin do tenant alvo.
**Eventos:** `sessao_remota.iniciada`.

---

### `DELETE /v1/suporte/acesso-remoto/sessoes/{id}`
**Propósito:** Revogar.
**Auth:** tenant admin ou auto-expiração.
**Eventos:** `sessao_remota.encerrada`.

---

### `GET /v1/suporte/acesso-remoto/sessoes/{id}/logs`
**Propósito:** Auditoria de ações da sessão.
**Invariantes:** `INV-001`.

---

## Endpoints — Sugestões e Roadmap

### `POST /v1/suporte/sugestoes`
**Propósito:** Nova sugestão.
**US:** `US-SUP-009`.

### `GET /v1/suporte/sugestoes`
**Propósito:** Listar sugestões visíveis ao tenant.

### `POST /v1/suporte/sugestoes/{id}/votos`
**Propósito:** Votar.
**Idempotente:** segundo voto do mesmo usuário retorna 409.

### `POST /v1/suporte/sugestoes/{id}/aprovar`
**Auth:** apenas PM Aferê.
**Eventos:** `sugestao.aprovada`.

### `GET /v1/suporte/roadmap`
**Propósito:** Itens roadmap visíveis ao tenant (público + privados do tenant).
**US:** `US-SUP-010`.

---

## Endpoints — Manutenção e Status

### `POST /v1/suporte/manutencoes`
**Propósito:** Agendar.
**Auth:** equipe Aferê.
**Validação:** janela planejada exige T-24h.
**Eventos:** `manutencao.agendada`.
**US:** `US-SUP-011`.

### `GET /v1/suporte/manutencoes`
**Propósito:** Listar pra tenant.

### `GET /v1/public/status`
**Propósito:** Página pública de status.
**Auth:** nenhuma.

---

## Rate limits

- Abertura de ticket: 10/min/usuário (anti-spam).
- Chat: 30 msgs/min/usuário.
- Voto: 60/min/usuário.
- Default: 300/min/tenant.

## Versionamento

v1 ativa. v2 com 6 meses de janela.

## Como evolui

Endpoint novo → US. Quebra → ADR + janela + comunicação a integradores.
