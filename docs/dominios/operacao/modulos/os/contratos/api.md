---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Contratos de API — Módulo OS

> REST por padrão (formato final em ADR-0001). Tenant obrigatório via header `X-Tenant-ID` ou token. RFC 7807 pra erros. `Idempotency-Key` em mutações.

---

## Endpoints

### `POST /v1/os`
**Propósito:** abrir nova OS (estado RASCUNHO).
**Papéis autorizados:** atendente, gerente, sistema (handler `OrcamentoAprovado`).
**Request:**
```json
{
  "tipo": "calibracao",
  "cliente_id": "uuid",
  "equipamento_id": "uuid",
  "prazo_prometido": "2026-05-25",
  "itens": [{"descricao": "...", "quantidade": 1}]
}
```
**Response 201:** `{"id": "uuid", "estado": "RASCUNHO", ...}`
**Erros:** 400 (input), 403 (sem permissão), 422 (cliente/equip inválido).
**Invariantes:** INV-026 (preço snapshot), RAT-08.
**US:** US-OS-001. **Evento:** `OSAberta`.

---

### `POST /v1/os/{id}/atribuir`
**Propósito:** atribuir técnico → RASCUNHO → AGENDADA.
**Request:** `{"tecnico_id": "uuid", "agendada_para": "2026-05-20T08:00:00-03:00"}`
**Response 200:** OS com novo estado.
**Erros:** 409 (estado inválido pra transição), 422 (INV-020 violada — agenda UMC).
**Invariantes:** INV-027, INV-020.
**Evento:** `OSAtribuida`.

---

### `POST /v1/os/{id}/iniciar`
**Propósito:** AGENDADA → EM_EXECUCAO.
**Request:** `{"geo": {"lat": -23.5, "long": -46.6, "precisao_m": 10}}` (opcional pra bancada).
**Response 200:** OS atualizada.
**Erros:** 409 (estado inválido), 403 (técnico ≠ atribuído).
**Invariantes:** INV-027, RAT-07 (geo opt-in).

---

### `POST /v1/os/{id}/concluir`
**Propósito:** EM_EXECUCAO → CONCLUIDA.
**Request:**
```json
{
  "checklist": [...],
  "nao_conformidade": false,
  "assinatura_cliente_base64": "...",
  "geo_conclusao": {...}
}
```
**Response 200:** OS CONCLUIDA.
**Erros:** 422 (checklist incompleto — retorna lista de itens faltantes), 409 (estado inválido).
**Invariantes:** INV-027, INV-012 (se `nao_conformidade=true` bloqueia certificado).
**Evento:** `OSConcluida`.

---

### `POST /v1/os/{id}/cancelar`
**Propósito:** qualquer estado ≠ FATURADA/PAGA → CANCELADA.
**Request:** `{"razao": "cliente desistiu"}`
**Response 200.** **Erros:** 422 (razão vazia), 409 (estado já final).
**Evento:** `OSCancelada`.

---

### `POST /v1/os/{id}/reabrir`
**Propósito:** CONCLUIDA/FATURADA/PAGA → cria **nova OS** com `os_origem_id`.
**Request:** `{"motivo": "cliente reclamou da medição"}`
**Response 201:** **nova OS** em RASCUNHO. **OS original permanece imutável** (INV-027).

---

### `GET /v1/os/{id}`
Retorna OS + checklist + itens + histórico de eventos. Filtro RBAC por tenant + papel.

### `GET /v1/os`
Lista paginada. Query params: `estado`, `tecnico_id`, `tipo`, `cliente_id`, `prazo_de`, `prazo_ate`. Default ordenação: `criada_at desc`.

### `POST /v1/os/sync` (mobile)
**Propósito:** batch de mudanças offline do app mobile. Ver ADR-0004.
**Request:** lista de operações com `client_timestamp` + `client_id`.
**Response:** `{aplicadas: [...], conflitos: [...]}`. Resolução de conflito por entidade (ADR-0004).

---

## Eventos consumidos

- `OrcamentoAprovado` (Comercial) → cria OS RASCUNHO automática.

## Rate limits

- `POST /os` — 60 req/min/tenant.
- `POST /os/sync` — 30 req/min/device.
- Default: a definir ADR-0001.

## Versionamento

v1 e v2 coexistem 6 meses. Quebra de contrato → ADR + CHANGELOG "Removido/Modificado".

## Como evolui

Endpoint novo → linkar US-OS-NNN. Quebra → janela 6m + comunicar integradores.
