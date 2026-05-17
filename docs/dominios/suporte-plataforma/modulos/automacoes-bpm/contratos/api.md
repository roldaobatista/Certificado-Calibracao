---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Automações & BPM

> Endpoints do módulo. Formato (REST / GraphQL / RPC) consolidado em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`) ou header (ADR-0001).
- Autenticação: header `Authorization: Bearer ...`.
- Tenant: `X-Tenant-ID` ou claim no token. `INV-TENANT-001` exige presença.
- Erros: RFC 7807 Problem Details.
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints — Fluxos

### `POST /v1/bpm/fluxos`
**Propósito:** criar fluxo (rascunho).
**Persona:** Configurador (RBAC `bpm.fluxo.criar`).
**Request:**
```json
{ "nome": "Aprovação Orçamento Desconto Alto", "descricao": "...", "categoria": "comercial" }
```
**Response 201:** `{ "id": "uuid", "status": "rascunho", "versao_corrente": null }`
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-TENANT-001`.
**US:** `US-BPM-001`.

### `PUT /v1/bpm/fluxos/{id}/definicao`
**Propósito:** salvar definição do desenho (rascunho).
**Request:** `{ "definicao": {...} }` (JSON do desenho).
**Response 200:** fluxo atualizado.

### `POST /v1/bpm/fluxos/{id}/publicar`
**Propósito:** publicar versão (cria `VersaoFluxo`).
**Request:** `{ "modo": "shadow" }` ou `{ "modo": "ativo" }`.
**Response 201:** `{ "versao_id": "uuid", "numero_versao": 3 }`.
**Códigos:** 201, 400, 409 (definição inválida), 422.
**Eventos:** `BPM.FluxoPublicado`.

### `GET /v1/bpm/fluxos` / `GET /v1/bpm/fluxos/{id}` / `GET /v1/bpm/fluxos/{id}/versoes`

---

## Endpoints — Instâncias e Pendências

### `POST /v1/bpm/instancias` (interno — engine)
**Propósito:** iniciar instância em resposta a evento.
**Request:** `{ "fluxo_id", "entidade_origem_tipo", "entidade_origem_id", "payload": {...} }`.
**Response 201:** instância criada.
**Eventos:** `BPM.InstanciaIniciada`.

### `GET /v1/bpm/pendencias?aprovador=me`
**Propósito:** listar pendências do aprovador logado.
**Query:** `status`, `risco_sla`, `fluxo_id`.
**Response 200:** lista paginada com SLA restante calculado.
**US:** `US-BPM-005`.

### `POST /v1/bpm/pendencias/{id}/decidir`
**Propósito:** aprovar ou rejeitar.
**Request:** `{ "decisao": "aprovada"|"rejeitada", "comentario": "..." }`.
**Response 200:** pendência decidida.
**Códigos:** 200, 403 (aprovador errado), 409 (já decidida), 410 (expirada).
**Eventos:** `BPM.AprovacaoConcedida` ou `BPM.AprovacaoRejeitada`.

### `POST /v1/bpm/pendencias/decidir-lote`
**Request:** `{ "pendencias": [{"id","decisao","comentario"}] }`.

---

## Endpoints — Regras

### `POST /v1/bpm/regras` / `PUT /v1/bpm/regras/{id}` / `POST /v1/bpm/regras/{id}/publicar`
Mesmo padrão dos fluxos.

### `GET /v1/bpm/regras/{id}/execucoes`
**Query:** `status`, `data_de`, `data_ate`.
**Response 200:** lista paginada.
**US:** `US-BPM-004`.

### `POST /v1/bpm/execucoes/{id}/reprocessar`
**Response 202:** nova `ExecucaoRegra` com link à original.
**US:** `US-BPM-004`.

### `POST /v1/bpm/execucoes/reprocessar-lote`
**Request:** `{ "execucoes": ["uuid","uuid"] }`.

---

## Endpoints — Catálogo

### `GET /v1/bpm/catalogo/eventos?modulo=calibracao`
### `GET /v1/bpm/catalogo/condicoes`
### `GET /v1/bpm/catalogo/acoes`
**US:** `US-BPM-007`.

---

## Endpoints — Delegação

### `POST /v1/bpm/delegacoes`
**Request:** `{ "substituto_id", "valido_de", "valido_ate", "motivo" }`.
**Códigos:** 201, 422 (overlap com outra delegação).
**US:** `US-BPM-003`.

### `GET /v1/bpm/delegacoes?titular=me`

---

## Endpoints — Alertas

### `POST /v1/bpm/alertas`
**Request:** `{ "tipo", "criterio", "canal", "destinatario" }`.

### `GET /v1/bpm/alertas`

---

## Eventos consumidos

O motor (ADR-0005) consome eventos de **todos os módulos de negócio** (CRM, Financeiro, Orçamentos, Chamados, OS, Calibração, Contratos, Estoque, Fiscal, Frota) via barramento. Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `decidir`: 100 req/min/usuário.
- `reprocessar-lote`: 10 req/min/tenant.
- Listagens: 60 req/min/usuário.

## Versionamento

- v1, v2 coexistem por 6 meses.
- Quebra exige ADR + bump CHANGELOG.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela.
- Descontinuação → `@deprecated` + headers Sunset (RFC 8594).
