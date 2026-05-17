---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Calibração

> Endpoints REST/RPC (formato em ADR-0001).

---

## Convenções

- Path: `/v1/calibracao/`.
- Auth: Bearer.
- Tenant: `X-Tenant-ID` ou claim (INV-TENANT-001).
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `POST /v1/calibracao/recepcoes`
**Propósito:** registrar entrada do instrumento.
**RBAC:** recepcionista, RT.
**Request:**
```json
{
  "ordem_servico_id": "uuid",
  "cliente_id": "uuid",
  "instrumento_id": "uuid",
  "condicoes_recebidas": "texto",
  "fotos_recepcao_ids": ["uuid"]
}
```
**Response 201:** Calibracao RECEPCIONADA + etiqueta PDF URL.
**Eventos:** `Calibracao.Recepcionada`.

---

### `POST /v1/calibracao/{id}/configuracao`
**Request:**
```json
{
  "grandeza": "massa",
  "faixa_min": 0,
  "faixa_max": 50000,
  "unidade": "g",
  "metodo": "NIT-DICLA-XXX",
  "pontos_calibracao": [1000, 5000, 10000, 25000, 50000],
  "repeticoes_por_ponto": 3,
  "regra_decisao": "BANDA_GUARDA_30",
  "tipo_acreditacao": "RBC"
}
```
**Response 200:** ConfiguracaoCalibracao + Calibracao CONFIGURADA.
**Códigos:** 200, 400, 401, 403, 422 (fora do escopo CMC).
**Invariantes:** `INV-002`.
**Eventos:** `Calibracao.Configurada`.

---

### `POST /v1/calibracao/{id}/padroes`
**Request:** `{ "padroes_ids": ["uuid", ...] }`
**Response 201:** PadroesUsados criados com snapshots.
**Códigos:** 201, 422 (padrão com cert vencido).
**Invariantes:** `INV-003`.

---

### `POST /v1/calibracao/{id}/leituras`
**Request:**
```json
{
  "ponto_calibracao": 5000,
  "numero_repeticao": 1,
  "valor_lido": 5000.02,
  "unidade": "g",
  "origem": "MANUAL",
  "timestamp": "2026-05-17T14:00:00-03:00"
}
```
**Response 201.**
**Códigos:** 201, 400, 422 (ponto fora da config).

### `POST /v1/calibracao/{id}/leituras/lote`
**Request:** array de leituras (integração serial/USB).

---

### `POST /v1/calibracao/{id}/condicoes-ambientais`
**Request:** `{ "temperatura_c": 20.5, "umidade_relativa": 50, "pressao_hpa": 1013, "medido_em": "..." }`

---

### `POST /v1/calibracao/{id}/calcular-incerteza`
**Propósito:** dispara cálculo automático com versão atual do motor.
**Response 200:** OrcamentoIncerteza + versão motor.
**Códigos:** 200, 409 (sem leituras/padrões/condições).
**Invariantes:** `INV-004`, `INV-005`.

### `PATCH /v1/calibracao/{id}/orcamento-incerteza`
**Propósito:** RT/metrologista ajusta componente Tipo B (com justificativa).
**Request:** `{ "componente_idx": 2, "novo_valor": ..., "justificativa": "..." }`

---

### `POST /v1/calibracao/{id}/avaliacao-conformidade`
**Request:**
```json
{
  "especificacao_cliente": { "min": 4995, "max": 5005, "unidade": "g" }
}
```
**Response 200:** AvaliacaoConformidade (CONFORME / NAO_CONFORME / ZONA_INCERTEZA).
**Invariantes:** `INV-006`.

### `PATCH /v1/calibracao/{id}/avaliacao-conformidade/decidir-zona`
**Request:** `{ "decisao": "CONFORME_COM_RESERVA", "justificativa": "..." }`

---

### `POST /v1/calibracao/{id}/revisoes`
**Propósito:** RT executa revisão (1ª ou 2ª).
**Request:**
```json
{
  "etapa": "REVISAO_1",
  "resultado": "APROVADO",
  "nota": "..."
}
```
**Response 201:** RevisaoTecnica.
**Códigos:** 201, 422 (etapa fora de ordem).
**Invariantes:** `INV-007`, `INV-019`.
**Eventos:** `Calibracao.RevisadaPrimeira` ou `Calibracao.SegundaConferenciaAprovada`.

---

### `POST /v1/calibracao/{id}/cancelar`
**Request:** `{ "motivo": "..." }`
**Response 200:** Status CANCELADA.

---

### `GET /v1/calibracao`
**Query:** `status, cliente_id, instrumento_id, executor_id, revisor_id, page, page_size`.

### `GET /v1/calibracao/{id}`
**Response 200:** payload completo.

### `GET /v1/calibracao/instrumentos/{instrumento_id}/historico`
**Response 200:** timeline calibrações.
**US:** `US-CAL-009`.

---

### Padrões

### `POST /v1/calibracao/padroes`
**Request:** dados padrão.
**RBAC:** RT.

### `GET /v1/calibracao/padroes`
**Query:** `tipo, status, validade_ate`.

### `POST /v1/calibracao/padroes/{id}/certificados-externos`
**Propósito:** registrar novo cert externo após calibração no lab acreditado.
**Request:** `{ "numero_externo": "...", "lab_emissor": "...", "data_emissao": "...", "data_validade": "...", "valor_convencional": ..., "incerteza": ..., "anexo_pdf_id": "..." }`
**Eventos:** atualiza vigência.

### `POST /v1/calibracao/padroes/{id}/envio-calibracao-externa`
**Request:** `{ "lab_destino": "...", "data_envio": "...", "protocolo": "..." }`
**Response 200:** Padrao EM_CALIBRACAO_EXTERNA.

### `POST /v1/calibracao/padroes/{id}/verificacoes-intermediarias`
**Request:** `{ "data_executada": "...", "resultado": ..., "desvio_observado": ..., "criterio_aceitacao": ..., "executado_por": "uuid" }`
**Eventos:** se reprovado, `Padroes.VerificacaoIntermediariaReprovada`.

---

### Proficiência

### `POST /v1/calibracao/proficiencia`
**Request:** `{ "provedor": "...", "rodada": "...", "grandeza": "...", "faixa": ..., "data_participacao": "..." }`

### `PATCH /v1/calibracao/proficiencia/{id}/resultado`
**Request:** `{ "escore_z": ..., "status": "PASSED|QUESTIONABLE|UNACCEPTABLE", "relatorio_anexo_id": "..." }`
**Eventos:** `Proficiencia.EscoreInsatisfatorio` se \|z\|≥3.

---

### Escopo de Acreditação

### `POST /v1/calibracao/escopo`
**RBAC:** admin.
**Request:** `{ "documento_regulatorio_id": "uuid", "grandeza": "...", "faixa_min": ..., "faixa_max": ..., "unidade": "...", "cmc": ..., "metodo": "...", "vigente_a_partir": "..." }`

### `GET /v1/calibracao/escopo?vigente=true`

---

## Eventos consumidos

- `Licencas.BloqueioAtivado` (acreditação vencida) → bloqueia configuração RBC.
- `Licencas.DocumentoRenovado` → libera bloqueio.

## Rate limits

- POST leituras: 200/min/tenant (integração serial pode ser intensa).
- POST cálculo: 30/min/tenant.

## Versionamento

- v1/v2 coexistem 6 meses.
- Mudança no motor de cálculo → ADR + nova versão registrada por calibração.

## Como esta lista evolui

- Endpoint novo → US.
- Quebra → ADR.
- Deprecado → Sunset.
