---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Contratos API — Capacity Planning Operacional

## Convenções

- Versionamento via path `/v1/`.
- Auth: Bearer. Tenant: `X-Tenant-ID` ou token (INV-TENANT-001).
- Erros: RFC 7807.
- Idempotência via `Idempotency-Key`.

---

## Endpoints

### `POST /v1/cpo/recursos`
**Propósito:** cadastrar recurso (técnico/equipe/laboratório).
**Request:**
```json
{"tipo":"tecnico|equipe|laboratorio","referencia_id":"uuid","nome":"..."}
```
**Response 201:** `{"id":"uuid","ativo":true}`
**US:** US-CPO-001.

---

### `PUT /v1/cpo/recursos/{id}/capacidade-base`
**Request:**
```json
{"horas_semanais":40,"dias_uteis":["seg","ter","qua","qui","sex"],"vigencia_inicio":"2026-06-01"}
```
**Response 200.**
**US:** US-CPO-001, US-CPO-002.

---

### `POST /v1/cpo/recursos/{id}/ausencias`
**Request:**
```json
{"tipo":"ferias|atestado|treinamento|manutencao_lab","data_inicio":"...","data_fim":"...","horas_dia_afetadas":8}
```

---

### `GET /v1/cpo/painel`
**Query:** `tipo_recurso`, `equipe_id`, `laboratorio_id`, `tipo_servico_id`, `janela_semanas`, `inicio`.
**Response:**
```json
{"recursos":[{"id":"...","nome":"...","semanas":[{"semana":"2026-W22","capacidade_h":40,"ocupadas_h":32,"taxa":0.8,"status":"saudavel"}]}],"kpis":{"ocupacao_media":0.72,"gargalos":2}}
```
**US:** US-CPO-003, US-CPO-011.

---

### `GET /v1/cpo/disponibilidade`
**Query:** `tipo_servico_id`, `horas_necessarias`, `prazo_ate`, `recursos_preferidos?`.
**Response:**
```json
{"semaforo":"verde|amarelo|vermelho","proxima_data_verde":"2026-06-15","recursos_elegiveis":[...]}
```
**US:** US-CPO-004.

---

### `GET /v1/cpo/gargalos`
**Response:** lista de gargalos abertos.
**US:** US-CPO-005.
**Eventos:** —

---

### `POST /v1/cpo/simulacoes`
**Request:**
```json
{"nome":"...","descricao":"...","mudancas":[{"acao":"alocar","os_id":"...","recurso_id":"..."}]}
```
**Response 201:** simulação em rascunho com resultado calculado.
**US:** US-CPO-006.

---

### `POST /v1/cpo/simulacoes/{id}/aplicar`
**Pré:** simulação válida.
**Pós:** mudanças viram alocações reais.
**Eventos:** `CapacityPlanning.SimulacaoAplicada`.

---

### `GET /v1/cpo/sugestoes/distribuicao`
**Query:** `os_id`.
**Response:**
```json
{"sugestoes":[{"recurso_id":"...","score":0.87,"justificativa":["skill_match","ocupacao_baixa","proximidade"]}]}
```
**US:** US-CPO-007.
**Eventos:** `CapacityPlanning.DistribuicaoSugerida`.

---

### `POST /v1/cpo/alocacoes`
**Request:**
```json
{"recurso_id":"...","os_id":"...","data_inicio":"...","data_fim":"...","horas":4}
```
**Pré:** ocupação não excede capacidade.
**Response 201.**

---

### `GET /v1/cpo/tempo-medio`
**Query:** `tipo_servico_id?`.
**Response:** lista de tempos médios + overrides.
**US:** US-CPO-008.

---

### `PUT /v1/cpo/tempo-medio/{tipo_servico_id}/override`
**Request:** `{"minutos": 120}` ou `{"minutos": null}` pra remover override.

---

### `GET /v1/cpo/previsao`
**Query:** `tipo_servico_id`, `horizonte_semanas`.
**Response:** lista de horas previstas por semana.
**US:** US-CPO-009.

---

### `GET /v1/cpo/indicacoes-contratacao`
**Response:** lista de indicações abertas.
**US:** US-CPO-010.
**Eventos consumidos:** —

---

### `POST /v1/cpo/indicacoes-contratacao/{id}/encaminhar`
**Pós:** evento `CapacityPlanning.IndicacaoContratacao` (também consumido por RH).

---

## Eventos consumidos

`Agenda.*`, `OS.*`, `Colaboradores.AusenciaRegistrada`, `Colaboradores.EscalaAtualizada`. Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- Painel: 30 req/min/usuário (cache 60s server-side).
- Disponibilidade: 120 req/min/tenant.

## Versionamento

v1. Quebra exige ADR + 6 meses de janela.
