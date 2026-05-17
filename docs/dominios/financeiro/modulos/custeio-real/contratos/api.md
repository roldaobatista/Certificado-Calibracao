---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Custeio Real

> Endpoints REST. Formato final pós ADR-0001.

---

## Convenções

- `/v1/` path versioning.
- Autenticação Bearer; tenant em `X-Tenant-ID` (`INV-TENANT-001`).
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key` em mutação.
- RBAC: rankings por técnico/vendedor/cliente → papéis restritos (gestor, dono).

---

## Endpoints

### `GET /v1/custeio/os/{os_id}/custo-real`
**Propósito:** retorna apuração da OS (versão mais recente).
**Response:**
```json
{
  "os_id": "uuid",
  "versao": 2,
  "apurado_em": "2026-05-17T10:00:00Z",
  "receita_os": 1500.00,
  "custo_total": 1800.00,
  "margem_real": -300.00,
  "margem_pct": -20.0,
  "eh_deficitaria": true,
  "linhas": [
    {"categoria":"mao_obra","previsto":600,"realizado":900,"variacao_pct":50.0},
    {"categoria":"pecas","previsto":700,"realizado":700,"variacao_pct":0},
    ...
  ]
}
```
**Códigos:** 200, 404 (OS não apurada), 403.
**US:** `US-CUS-001`, `US-CUS-002`.

---

### `GET /v1/custeio/os/{os_id}/custo-real/versoes`
**Propósito:** lista histórico de apurações.
**Response:** lista `[{versao, apurado_em, custo_total, margem_real}]`.

---

### `POST /v1/custeio/os/{os_id}/reapurar`
**Propósito:** força reapuração (papel autorizado).
**Request:** `{motivo}`.
**Response:** `202 {job_id}` (assíncrono).
**Códigos:** 202, 403, 404, 409 (já em apuração).
**Eventos:** `CusteioReal.CustoReapurado` ao concluir.

---

### `GET /v1/custeio/margem/agregado`
**Propósito:** dashboard "Minha Margem".
**Query:** `?periodo_inicio=&periodo_fim=`.
**Response:** `{receita, custo_total, margem_real, margem_pct, count_os, count_deficitarias, serie_mensal:[...]}`.
**US:** `US-CUS-003`.

---

### `GET /v1/custeio/margem/ranking`
**Propósito:** ranking por dimensão.
**Query:** `?dimensao=cliente|vendedor|tecnico|servico&periodo_inicio=&periodo_fim=&order=margem_pct_asc&limit=`.
**Response:** lista paginada `[{dimensao_id, dimensao_nome, receita, custo, margem, margem_pct, count_os, eh_deficitaria}]`.
**RBAC:** rankings por técnico/vendedor exigem papel `gestor_operacional` ou `dono`.

---

### `GET /v1/custeio/alertas-deficitarios`
**Propósito:** fila de OSs deficitárias.
**Query:** `?status=&periodo=&tecnico_id=&cliente_id=&page=`.
**Response:** lista paginada.
**US:** `US-CUS-004`.

---

### `PATCH /v1/custeio/alertas-deficitarios/{id}`
**Propósito:** atualizar status do alerta.
**Request:** `{status:"em_revisao"|"tratado"|"ignorado", nota?}`.
**Response:** `200`.
**Códigos:** 200, 400, 403, 404, 409 (transição inválida).

---

### `GET /v1/custeio/parametros`
**Propósito:** lista parâmetros vigentes.
**Query:** `?escopo_tipo=&data=` (data permite consultar parâmetros vigentes em data passada).
**Response:** lista.
**US:** `US-CUS-007`.

---

### `POST /v1/custeio/parametros`
**Propósito:** cria nova versão de parâmetro.
**Request:** `{chave, valor, vigente_desde, escopo_tipo?, escopo_id?}`.
**Response:** `201`.
**Códigos:** 201, 400, 403.
**Trilha:** registrada em log de auditoria (quem/quando/de→para).

---

## Eventos consumidos (internos)

| Evento | Origem | Tratamento |
|---|---|---|
| `Operacao.OSEncerrada` | OS | enfileira apuração |
| `Operacao.OSReaberta` | OS | invalida apuração vigente |
| `Estoque.SaidaPeca` | Estoque | recalcula linha `pecas` se OS vinculada |
| `CaixaTecnico.DespesaAprovada` | Caixa Técnico | recalcula linha de despesa correspondente |
| `Comissoes.ComissaoCalculada` | Comissões | recalcula linha `comissao` |

---

## Eventos publicados

(ver `../modelo-de-dominio.md` para schema completo)

- `CusteioReal.CustoApurado`
- `CusteioReal.AlertaDeficitarioCriado`
- `CusteioReal.CustoReapurado`

---

## Rate limits

- `POST /v1/custeio/os/{id}/reapurar` — 5 req/min/tenant.
- Demais GET: limite padrão do tenant.

---

## Versionamento

- v1 estável; v2 coexiste 6 meses em quebra de contrato.
- Mudança em payload de evento: comunicar consumidores + ADR.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Dimensão de agregação nova → adicionar enum em `?dimensao=`.
