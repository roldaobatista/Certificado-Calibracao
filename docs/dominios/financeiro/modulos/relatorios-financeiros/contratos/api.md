---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Relatórios Financeiros

> Endpoints majoritariamente **GET** (read-model). Mutações: salvar visão, agendar, importar conciliação.

---

## Convenções

- Versionamento por path (`/v1/`).
- `Authorization: Bearer <token>`.
- Tenant via header `X-Tenant-ID` (validado por `INV-TENANT-001`).
- Erros: RFC 7807.
- Cache HTTP (`ETag`/`Cache-Control: private, max-age=N`) habilitado para GETs de relatório.

---

## Endpoints

### `GET /v1/relatorios/dre`
**Query:** `?periodo_ini=&periodo_fim=&comparar_com=periodo_anterior|null&granularidade=mes|trimestre|ano`.
**Response 200:**
```json
{
  "periodo": {"ini": "2026-05-01", "fim": "2026-05-31"},
  "linhas": [
    {"chave": "receita_bruta", "valor": 120000.00, "drill_url": "/v1/relatorios/dre/drill?linha=receita_bruta&..."},
    {"chave": "deducoes", "valor": -15000.00},
    {"chave": "lucro_liquido", "valor": 38000.00}
  ],
  "comparativo": null
}
```
**Códigos:** 200, 400, 401, 403.
**US:** `US-RFN-001`. **Invariantes:** `INV-RFN-001`.

---

### `GET /v1/relatorios/dre/drill`
**Query:** `?linha=&categoria=&periodo_ini=&periodo_fim=`.
**Response 200:** lista paginada de lançamentos.
**US:** `US-RFN-001`.

---

### `GET /v1/relatorios/fluxo-caixa/realizado`
**Query:** `?periodo_ini=&periodo_fim=&granularidade=dia|semana|mes`.
**Response 200:** série temporal com entradas, saídas, saldo acumulado.
**US:** `US-RFN-002`.

---

### `GET /v1/relatorios/fluxo-caixa/projetado`
**Query:** `?janela_dias=30|60|90&incluir_recorrencias=true|false&data_base=YYYY-MM-DD`.
**Response 200:**
```json
{
  "data_base": "2026-05-17",
  "dias": [
    {"data": "2026-05-18", "entradas_previstas": 0, "saidas_previstas": 2400.00, "saldo_projetado": -2400.00, "alerta": "saldo_negativo"},
    ...
  ]
}
```
**US:** `US-RFN-003`.

---

### `GET /v1/relatorios/aging`
**Query:** `?tipo=receber|pagar|ambos&data_base=`.
**Response 200:** array de faixas com qtd, valor, % do total.
**US:** `US-RFN-004`.

---

### `GET /v1/relatorios/centro-custo`
**Query:** `?periodo_ini=&periodo_fim=&comparar_com=periodo_anterior`.
**Response 200:** array por centro com total, %, variação.
**US:** `US-RFN-005`.

---

### `GET /v1/relatorios/receitas-despesas`
**Query:** `?periodo_a_ini=&periodo_a_fim=&periodo_b_ini=&periodo_b_fim=`.
**Response 200:** tabela comparativa.
**US:** `US-RFN-007`.

---

### `GET /v1/relatorios/resultado-dimensao`
**Query:** `?dimensao=cliente|tecnico|vendedor|servico&periodo_ini=&periodo_fim=&ordem=margem_asc|margem_desc`.
**Response 200:** array com receita, custo, margem, margem %.
**US:** `US-RFN-008`.

---

### `POST /v1/conciliacao/extratos`
**Propósito:** upload de OFX/CSV.
**Request:** multipart `arquivo` + `conta_bancaria_id`.
**Response 201:** `{ "conciliacao_id": "uuid", "linhas_count": 142, "status": "em_andamento" }`.
**Códigos:** 201, 400 (formato inválido), 401, 403, 413.
**US:** `US-RFN-006`. **Invariantes:** `INV-WORM-001`.

---

### `GET /v1/conciliacao/{id}`
**Response 200:** conciliação + linhas.
**US:** `US-RFN-006`.

---

### `POST /v1/conciliacao/{id}/linhas/{linha_id}/confirmar`
**Request:** `{ "lancamento_id_match": "uuid", "comentario": "opcional" }`.
**Response 200:** linha vira `conciliada`.
**US:** `US-RFN-006`. **Invariantes:** `INV-RFN-002`.

---

### `POST /v1/relatorios/visoes`
**Propósito:** salvar visão (filtros nomeados).
**Request:** `{ "tipo": "dre", "filtros": {...}, "nome": "DRE 2026" }`.
**Response 201:** `{ "relatorio_id": "uuid" }`.
**US:** `US-RFN-001`+.

---

### `POST /v1/relatorios/visoes/{id}/agendar`
**Request:** `{ "cron_expr": "0 9 1 * *", "destinatarios_emails": ["..."], "formato": "pdf" }`.
**Response 201:** `{ "agendamento_id": "uuid" }`.

---

### `GET /v1/relatorios/exportar/{tipo}`
**Query:** filtros do relatório + `formato=pdf|xlsx|csv`.
**Response 200:** binário com `Content-Disposition: attachment`.
**Códigos:** 200, 400, 401, 403.
**US:** `US-RFN-009`. **Segurança:** anonimização conforme RBAC do solicitante (`SEC-LGPD-005`).

---

## Eventos consumidos

Ver `../modelo-de-dominio.md` — este módulo consome eventos de praticamente todo o domínio financeiro para manter views agregadas.

## Rate limits

- Exports — 30 req/h/usuário.
- GETs de relatório — 120 req/min/usuário (cacheáveis).
- Default: a definir em ADR-0001.

## Versionamento

- v1, v2 coexistem 6 meses.
- Quebra → ADR + bump CHANGELOG.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela de migração.
- `@deprecated` → headers Sunset (RFC 8594).
