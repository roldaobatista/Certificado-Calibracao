---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Contratos de API — Módulo Agenda

> REST por padrão. Tenant via header. `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/agenda/eventos`
**Propósito:** criar EventoAgenda.
**Request:**
```json
{
  "tecnico_id": "uuid",
  "tipo": "os",
  "inicia_at": "2026-05-20T08:00:00-03:00",
  "termina_at": "2026-05-20T10:00:00-03:00",
  "os_id": "uuid"
}
```
**Response 201:** evento criado.
**Erros:**
- 422 + `{"violacao": "INV-020", "detalhe": "técnico não terá 11h ininterruptas", "sugestao_proximo_slot": "..."}` (jornada UMC)
- 409 + `{"conflito_com_evento_id": "..."}` (overlap)
- 422 (feriado sem confirmação)
**Invariantes:** INV-020, unique-overlap, RAT-08.
**Evento:** `AgendaSlotAlocado` (se tipo=os).

---

### `PATCH /v1/agenda/eventos/{id}`
**Propósito:** mover evento (mesma estrutura de criação). Valida INV-020 + conflito **antes** de salvar.
**Response 200:** evento atualizado. **Evento:** `AgendaReagendada` (se tipo=os).
**Audit:** grava `de` e `para` em EventoAuditoria.

---

### `POST /v1/agenda/eventos/{id}/cancelar`
**Request:** `{"motivo": "..."}`. Não apaga — marca cancelado + audit.

---

### `POST /v1/agenda/validar`
**Propósito:** dry-run de validação (drag & drop pré-save). Retorna ok/violação **sem persistir**.
**Request:** mesma estrutura de POST eventos.
**Response 200:** `{"ok": true}` OR `{"ok": false, "violacao": "INV-020|CONFLITO|FERIADO|CAPACIDADE", "detalhes": {...}}`.
**Performance:** < 200ms p95 (NFR pra drag fluido).

---

### `GET /v1/agenda/semana`
**Query:** `inicio=YYYY-MM-DD&tecnicos=uuid,uuid,...`
**Response:** matriz `{tecnico_id: [eventos]}` + capacidade por dia + feriados aplicáveis.

---

### `GET /v1/agenda/sugestoes`
**Propósito:** sugerir 3 slots livres pra agendar OS (US-AG-006).
**Query:** `tecnico_id`, `duracao_min`, `prazo_max`, `competencia_requerida?`.
**Response:** lista ordenada por proximidade temporal + custo de deslocamento estimado.

---

### `POST /v1/agenda/bloqueios`
**Propósito:** criar bloqueio (férias, treinamento).
**Request:** `{"tecnico_id": "...", "inicia_at": "...", "termina_at": "...", "motivo": "ferias"}`
**Papel:** gerente + RH.

---

### `POST /v1/agenda/recorrencia`
**Propósito:** criar regra (ex: manutenção semanal).
**Request:** `{"tecnico_id": "...", "regra_rrule": "FREQ=WEEKLY;BYDAY=MO", "template_evento": {...}, "inicia_em": "...", "termina_em": "..."}`
**Response 201:** regra + job materializa 90 dias.

---

### `POST /v1/agenda/eventos/{id}/aprovar-cliente`
**Propósito:** cliente aprova janela proposta (via portal).
**Auth:** token público com escopo limitado (RFC 8693).
**Request:** `{"aprovado": true}`.

---

### `GET /v1/agenda/feriados`
**Query:** `tenant_id?`, `ano`. Retorna feriados nacionais + estaduais + municipais + custom.

---

## Eventos consumidos

- `OSAtribuida` (módulo OS) → cria EventoAgenda tipo=os automático se ainda não existe slot.
- `OSCancelada` → libera slot (remove EventoAgenda associado, mantendo audit).
- `ChamadoConvertidoEmOS` → não cria slot direto; gera sugestão pro atendente.

## Rate limits

- `POST /agenda/validar` — 1200 req/min/tenant (chamado durante drag).
- `POST /agenda/eventos` — 120 req/min/tenant.

## Versionamento

v1 e v2 coexistem 6 meses.

## Como evolui

Endpoint novo → linkar US. Mudança em validação INV-020 → ADR.
