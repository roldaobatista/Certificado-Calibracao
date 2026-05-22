---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
modulo: os
dominio: operacao
---

# Contratos de API — Módulo OS

> REST por padrão (formato final em ADR-0001). Tenant obrigatório via header `X-Afere-Active-Tenant` ou token. RFC 7807 pra erros. `Idempotency-Key` **obrigatório** em todas mutações (IDEMP-001).
>
> **Revisado em 2026-05-23 (ADR-0023):** API reorientada por `AtividadeDaOS`. POST `/v1/os` **NÃO aceita mais `tipo` no payload da OS** — tipos vão nas atividades. Novos endpoints `/atividades/{aid}/iniciar` `/concluir` `/cancelar` substituem os endpoints OS-monolítico.

---

## Endpoints

### `POST /v1/os`
**Propósito:** abrir nova OS (estado RASCUNHO) com N atividades em PENDENTE (ADR-0023).
**Papéis autorizados:** P-OP-03 atendente, P-OP-04 gerente, sistema (handler `Orcamento.Aprovado`).
**Idempotency-Key:** obrigatório (IDEMP-001).
**Request:**
```json
{
  "cliente_id": "uuid",
  "equipamento_id": "uuid",
  "prazo_prometido": "2026-05-25",
  "itens": [
    {"descricao": "...", "quantidade": 1, "atividade_index": 0}
  ],
  "atividades": [
    {"tipo": "manutencao_corretiva", "sequencia": 1, "tecnico_executor_id": "uuid?"},
    {"tipo": "calibracao", "sequencia": 2, "tecnico_executor_id": "uuid?"}
  ],
  "correlation_id": "uuid?"
}
```
**Response 201:** `{"id": "uuid", "estado": "RASCUNHO", "atividades": [{"id": "uuid", "tipo": "...", "estado": "PENDENTE", "sequencia": 1}, ...]}`
**Erros:** 400 (input inválido / Idempotency-Key ausente), 403 (sem permissão), 422 (`OrcamentoCrossTenant`, `ClienteBloqueado`, `EquipamentoForaDoTenant`).
**Invariantes:** INV-026 (preço snapshot), INV-TENANT-001, INV-OS-ATIV-002/003, RAT-08, IDEMP-001.
**US:** US-OS-001. **Evento:** `OSAberta` com `atividades_planejadas` no payload.

---

### `POST /v1/os/{id}/atribuir`
**Propósito:** atribuir técnico geral → RASCUNHO → AGENDADA.
**Idempotency-Key:** obrigatório.
**Request:** `{"tecnico_id": "uuid", "agendada_para": "2026-05-20T08:00:00-03:00"}`
**Response 200:** OS com novo estado.
**Erros:** 409 (estado inválido pra transição), 422 (INV-020 violada — agenda UMC).
**Invariantes:** INV-027, INV-020, INV-AUTHZ-001.
**Evento:** `OSAtribuida`.

---

### `POST /v1/os/{id}/atividades`
**Propósito:** adicionar atividade a OS em andamento (US-OS-010 / ADR-0023).
**Idempotency-Key:** obrigatório.
**Request:** `{"tipo": "manutencao_corretiva", "sequencia": 3, "tecnico_executor_id": "uuid?"}`
**Response 201:** `{"id": "uuid", "tipo": "...", "estado": "PENDENTE", "sequencia": 3}` + publica `AtividadeAdicionada`.
**Erros:** 412 (`OSEmEstadoTerminal`), 403 (`PerfilSemCompetencia`), 400 (`TipoInvalido` — INV-OS-ATIV-003).
**Invariantes:** INV-OS-ATIV-001, INV-OS-ATIV-003.

---

### `POST /v1/os/{id}/atividades/{aid}/iniciar`
**Propósito:** PENDENTE → EM_EXECUCAO da atividade específica. OS migra pra EM_EXECUCAO se for a 1ª atividade iniciada.
**Idempotency-Key:** obrigatório (IDEMP-001 + sync mobile replay protection).
**Request:**
```json
{
  "client_event_id": "uuid",
  "client_timestamp": "2026-05-20T08:15:00-03:00",
  "geo": {"lat": -23.5, "long": -46.6, "precisao_m": 10}
}
```
**Response 200:** atividade atualizada.
**Erros:** 403 (`NaoEExecutor` — INV-OS-ATIV-005), 409 (estado inválido), 412 (`SequenciaPendente`).
**Invariantes:** INV-027, INV-OS-ATIV-005, INV-OS-GEO-001, IDEMP-001, RAT-07.
**Evento:** `AtividadeIniciada` (consumer `metrologia/calibracao` filtra `tipo=calibracao`).

---

### `POST /v1/os/{id}/atividades/{aid}/concluir`
**Propósito:** EM_EXECUCAO → CONCLUIDA da atividade. OS migra pra CONCLUIDA quando TODAS atividades terminais (INV-OS-ATIV-001).
**Idempotency-Key:** obrigatório.
**Request:**
```json
{
  "client_event_id": "uuid",
  "checklist": {"foto_inicial": "...", "padrao_usado_id": "uuid", "...": "..."},
  "aceite_atividade": {
    "versao_termo": "v1.0",
    "metodo_assinatura": "touch|A1|A3",
    "assinatura_base64_ou_a3_signature": "..."
  },
  "geo_conclusao": {"...": "..."}
}
```
**Response 200:** atividade CONCLUIDA + `os.estado` atualizado se aplicável.
**Erros:** 412 (`ChecklistIncompleto: [campo_X]`), 403 (`NaoEExecutor`), 409 (estado inválido), 400 (`TextoComPII` — INV-OS-TXT-001).
**Invariantes:** INV-027, INV-OS-ATIV-001/004/005, INV-CER-FRAUD-A3-001 (se método=A3), RAT-08.
**Eventos:** `AtividadeConcluida` + (se foi a última) `OSConcluida`.

---

### `POST /v1/os/{id}/atividades/{aid}/marcar-nc`
**Propósito:** EM_EXECUCAO → NAO_CONFORME. Aplica a atividade tipo=calibracao (US-OS-005).
**Idempotency-Key:** obrigatório.
**Request:** `{"razao_nao_conformidade": "..." (≥30 chars, anti-PII)}`
**Response 200:** atividade NAO_CONFORME.
**Erros:** 400 (`TextoComPII` ou `RazaoCurta`), 409 (estado inválido), 403 (sem permissão).
**Invariantes:** INV-012, INV-OS-TXT-001.
**Evento:** `AtividadeNaoConforme` (consumer `metrologia/certificados` bloqueia emissão).

---

### `POST /v1/os/{id}/atividades/{aid}/resolver-nc`
**Propósito:** NAO_CONFORME → EM_EXECUCAO após ciclo CAPA fechado (TEMA-B.2).
**Idempotency-Key:** obrigatório.
**Request:** `{"causa_raiz_id": "uuid", "acao_corretiva_id": "uuid", "eficacia_verificada_por": "uuid"}`
**Response 200:** atividade EM_EXECUCAO.
**Erros:** 412 (`CicloCAPANaoFechado`), 403 (`PerfilSemCompetenciaParaResolverNC`).
**Evento:** `AtividadeNCResolvida`.

---

### `POST /v1/os/{id}/atividades/{aid}/cancelar`
**Propósito:** cancelar UMA atividade sem cancelar a OS toda (US-OS-008).
**Idempotency-Key:** obrigatório.
**Request:** `{"razao_cancelamento": "..." (≥30 chars, anti-PII)}`
**Response 200:** atividade CANCELADA + `os.estado` recalculado (pode virar CONCLUIDA ou CANCELADA conforme INV-OS-ATIV-001).
**Evento:** `AtividadeCancelada`.

---

### `POST /v1/os/{id}/cancelar`
**Propósito:** cancelar OS inteira → cascateia atividades PENDENTE/EM_EXECUCAO pra CANCELADA. Atividades CONCLUIDA permanecem.
**Idempotency-Key:** obrigatório.
**Request:** `{"razao_cancelamento": "..." (≥30 chars, anti-PII)}`
**Response 200.**
**Erros:** 412 (`EstadoTerminalProibeCancelamento` — FATURADA/PAGA), 400 (`TextoComPII`).
**Evento:** `OSCancelada`.

---

### `POST /v1/os/{id}/reabrir`
**Propósito:** CONCLUIDA/FATURADA/PAGA → cria **nova OS** com `os_origem_id` (US-OS-006).
**Idempotency-Key:** obrigatório.
**Request:** `{"motivo": "...", "garantia_procedente": true, "chamado_origem_id": "uuid?", "atividades_a_clonar": ["uuid", "..."]}`
**Response 201:** nova OS em RASCUNHO. OS original permanece imutável (INV-027).
**Erros:** 422 (`ReaberturaCrossTenant` — INV-OS-ATIV-005), 412 (estado não-terminal).
**Evento:** `OS.Reaberta` com `correlation_id` herdado da OS-mãe + `causation_id`.

---

### `GET /v1/os/{id}`
Retorna OS + atividades (com estados + checklist + aceites) + itens + histórico de eventos. Filtro RBAC por tenant + papel + finalidade LGPD (INV-013 grava `AcessoDadosCliente` antes).

### `GET /v1/os`
Lista paginada. Query params: `estado`, `tecnico_id`, `tipo_predominante`, `cliente_id`, `prazo_de`, `prazo_ate`. Default ordenação: `criada_at desc`.

### `GET /v1/os/{id}/atividades/{aid}`
Retorna atividade individual + checklist + aceite + eventos da atividade.

### `POST /v1/os/sync` (mobile)
**Propósito:** batch de mudanças offline do app mobile. Cada operação carrega `client_event_id` próprio (anti-replay IDEMP-001). Ver ADR-0004 + ADR-0027 (sync mobile com merge por atividade — TEMA-F.4 a criar).
**Request:** lista de operações `[{op, atividade_id?, client_event_id, client_timestamp, payload}]`.
**Response:** `{aplicadas: [...], conflitos: [...]}`. Resolução por atividade (last-write-wins per atividade — ADR-0027).

---

## Eventos consumidos

- `Orcamento.Aprovado` (Comercial) → cria OS RASCUNHO + N atividades automáticas.
- `Colaborador.Desligado` (RH) → invalida sessões + bloqueia atividades pendentes do técnico (INV-INT-002).

## Eventos publicados (catálogo v10 — TEMA-E.1)

- `OSAberta`, `OSAtribuida`, `OSConcluida`, `OSCancelada`, `OS.Reaberta`
- `AtividadeAdicionada`, `AtividadeIniciada`, `AtividadeConcluida`, `AtividadeNaoConforme`, `AtividadeNCResolvida`, `AtividadeCancelada`

Todos os payloads carregam: `tenant_id`, `os_id`, `atividade_id` (quando aplicável), `correlation_id`, `causation_id`, hash HMAC-tenant para IDs sensíveis (INV-OS-AUD-001), `event_schema_version`.

## Rate limits

- `POST /os` — 60 req/min/tenant.
- `POST /os/.../iniciar`, `/concluir` — 120 req/min/tenant.
- `POST /os/sync` — 30 req/min/device.
- Endpoints públicos (portal-cliente) — 60 req/min/IP + lockout após 100 4xx/h (pattern SEC-QR-001).

## Versionamento

v1 e v2 coexistem 6 meses. Quebra de contrato → ADR + CHANGELOG "Removido/Modificado".

## Como evolui

Endpoint novo → linkar US-OS-NNN. Quebra → janela 6m + comunicar integradores.
