---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/conformidade-iso-17025.md
---

# Contratos de API — Módulo Auditoria Externa

> Endpoints REST. Cliente principal: web + mobile (registro de apontamento).

---

## Convenções

- Versionamento via path (`/v1/`).
- Auth: `Authorization: Bearer <token>`.
- Tenant: dentro do token. `INV-TENANT-001` exige presença em toda query no backend.
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `GET /v1/auditorias`
**Propósito:** lista auditorias do tenant.
**Querystring:** `status`, `norma_id`, `ano`, `pagina`, `tamanho`.
**Response 200:** lista paginada.
**US:** `US-AUD-008`.

---

### `POST /v1/auditorias`
**Propósito:** cria auditoria + carrega checklist da norma.
**Request:**
```json
{
  "norma_id": "uuid",
  "organismo": "CGCRE",
  "nome_organismo": "INMETRO",
  "data_inicio": "2026-11-15",
  "data_fim": "2026-11-17",
  "escopo": "Calibração de balanças classe III",
  "responsavel_geral_id": "uuid"
}
```
**Response 201:** auditoria + checklist gerado.
**Eventos:** `AuditoriaExterna.AuditoriaPlanejada`.
**US:** `US-AUD-001`, `US-AUD-002`.
**Invariantes:** `INV-TENANT-001`.

---

### `GET /v1/auditorias/{id}`
**Propósito:** detalhe completo.
**US:** todas.

---

### `PATCH /v1/auditorias/{id}/status`
**Propósito:** transição planejada→em_andamento→concluida.
**Request:** `{status: "em_andamento"|"concluida"|"cancelada"}`.
**Invariantes:** concluída é imutável depois.
**US:** `US-AUD-001`.

---

### `GET /v1/auditorias/{id}/checklist`
**Propósito:** itens do checklist com filtros.
**Querystring:** `status`, `responsavel_id`, `criticidade`.
**US:** `US-AUD-002`, `US-AUD-005`.

---

### `PATCH /v1/checklist-item/{id}`
**Propósito:** atribuir responsável, prazo, status.
**Request:** `{responsavel_id?, prazo?, status?}`.
**US:** `US-AUD-003`.

---

### `POST /v1/checklist-item/{id}/evidencia`
**Propósito:** anexar evidência (multipart) ou referência.
**Request multipart:** `arquivo` OU `doc_controlado_id` OU `referencia_sistema`.
**Response 201:** evidência criada.
**US:** `US-AUD-004`.
**Invariantes:** imutável após auditoria concluída.

---

### `POST /v1/auditorias/{id}/apontamento`
**Propósito:** registra apontamento durante auditoria.
**Request:**
```json
{
  "tipo": "nc_maior|nc_menor|observacao|oportunidade",
  "requisito_norma_id": "uuid",
  "descricao": "...",
  "evidencia_apresentada_id": "uuid",
  "foto_url": null
}
```
**Response 201:** apontamento criado.
**Eventos:** `AuditoriaExterna.NCMaiorRegistrada` (se NC maior).
**US:** `US-AUD-006`.

---

### `POST /v1/apontamento/{id}/plano-acao`
**Propósito:** cria plano de ação para uma NC.
**Request:**
```json
{
  "causa_raiz": "...",
  "metodo_causa_raiz": "5_porques",
  "porques": ["por1", "por2", "por3", "por4", "por5"],
  "acao_corretiva": "...",
  "responsavel_id": "uuid",
  "prazo": "2026-12-15",
  "acao_preventiva": null
}
```
**Códigos:** 201, 422 (se NC maior sem 5-porquês completo).
**Invariantes:** NC maior exige 5-porquês.
**US:** `US-AUD-007`.

---

### `POST /v1/plano-acao/{id}/evidencia-fechamento`
**Propósito:** anexa evidência de fechamento.
**Request multipart:** `arquivo`, `descricao`.
**US:** `US-AUD-007`.

---

### `POST /v1/plano-acao/{id}/aprovar-fechamento`
**Propósito:** RQ aprova fechamento da NC.
**Códigos:** 200, 403 (só RQ aprova).
**Eventos:** `AuditoriaExterna.NCFechada`.
**US:** `US-AUD-007`.

---

### `GET /v1/normas/{id}/matriz-conformidade`
**Propósito:** matriz cláusula × status em tempo real.
**Response 200:**
```json
{
  "norma": {...},
  "linhas": [
    {"clausula": "7.5.3", "status": "atendido", "ultima_evidencia": {...}, "responsavel": {...}}
  ],
  "percentual_conformidade": 96.3
}
```
**US:** `US-AUD-010`.

---

### `GET /v1/normas/{id}/documentos-exigidos`
**Propósito:** lista docs exigidos + status.
**US:** `US-AUD-011`.

---

### `POST /v1/auditorias/{id}/drill`
**Propósito:** cria simulação.
**Request:** `{auditor_simulado_id: "uuid" | "agente:familia5-qualidade"}`.
**Eventos:** `AuditoriaExterna.DrillConcluido` quando finalizado.
**US:** `US-AUD-012`.

---

### `GET /v1/drill/{id}/gap-report`
**Propósito:** retorna gap report do drill.
**US:** `US-AUD-012`.

---

### `GET /v1/painel-prontidao`
**Propósito:** semáforo por norma ativa.
**Response 200:**
```json
{
  "normas": [
    {"norma_id": "uuid", "codigo": "ISO/IEC 17025:2017", "semaforo": "verde", "percentual": 96.3, "nc_abertas": 1, "proxima_auditoria": "2026-11-15", "top3_acoes": []}
  ]
}
```
**Eventos:** consumido por `AuditoriaExterna.SemaforoMudou` (push opcional via SSE/websocket — a definir em ADR).
**US:** `US-AUD-013`.

---

### `POST /v1/auditorias/{id}/relatorio-final`
**Propósito:** gera PDF final.
**Response 201:** URL do PDF (Backblaze B2).
**US:** `US-AUD-009`.

---

## Eventos consumidos de outros módulos

- `Qualidade.DocControladoAtualizado` → marca evidências apontando pra versão anterior como "desatualizada".
- `Calibracao.LaudoEmitido` → pode ser referenciado como evidência em auditoria ISO 17025.
- `Governanca.AuditorFamilia5DrillSolicitado` → cria drill com agente.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /v1/auditorias/{id}/apontamento` — 60 req/min (auditoria intensa).
- Demais: default ADR-0001.

## Versionamento

- v1, v2 coexistem 6 meses.
- Quebra de contrato → ADR + bump CHANGELOG.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela migração.
- `@deprecated` → Sunset header (RFC 8594).
