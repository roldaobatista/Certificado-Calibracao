---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: garantia
dominio: operacao
---

# Contratos de API — Módulo Garantia

> Endpoints / IPC. Formato REST candidato (ADR-0001 confirma).

## Convenções

- Versionamento via path `/v1/`.
- Auth: header `Authorization: Bearer ...`.
- Tenant: `X-Tenant-ID` obrigatório (`INV-TENANT-001`).
- Erros: RFC 7807.
- Mutação aceita `Idempotency-Key`.

---

## Endpoints

### `POST /v1/garantia/prazos`
**Propósito:** cadastrar nova versão de prazo de garantia.
**Papel:** GERENTE_OPERACIONAL.
**Request:**
```json
{ "tipo": "PECA", "prazo_dias": 90 }
```
**Response 201:**
```json
{ "id": "uuid", "tipo": "PECA", "prazo_dias": 90, "vigente_de": "2026-05-17T00:00:00Z" }
```
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-001`, `INV-026` análogo.
**US:** `US-GAR-001`.

---

### `GET /v1/garantia/prazos?tipo=PECA`
**Propósito:** lista prazos vigentes e históricos.
**Response 200:** array de prazos com `vigente_de` / `vigente_ate`.

---

### `POST /v1/garantias`
**Propósito:** abrir garantia + OS-filha em garantia.
**Papel:** ATENDENTE, GERENTE.
**Request:**
```json
{
  "os_mae_id": "uuid",
  "tipo": "SERVICO",
  "motivo": "cliente relata que balança voltou a descalibrar em 10 dias",
  "forcar_fora_prazo": false,
  "aprovador_id": null
}
```
**Response 201:**
```json
{
  "garantia_id": "uuid",
  "os_filha_id": "uuid",
  "status": "ABERTA",
  "data_limite": "2026-06-17T00:00:00Z"
}
```
**Códigos:** 201, 400 (fora de prazo sem `forcar_fora_prazo`+`aprovador_id`), 403, 409 (já existe garantia aberta), 422.
**Eventos:** `Garantia.Aberta`.
**US:** `US-GAR-002`.

---

### `POST /v1/garantias/{id}/iniciar-analise`
**Propósito:** muda status para EM_ANALISE.
**Papel:** TECNICO, METROLOGISTA.
**Response 200:** `{ "status": "EM_ANALISE" }`.

---

### `POST /v1/garantias/{id}/laudo`
**Propósito:** registrar laudo + decisão (imutável após).
**Request:**
```json
{
  "decisao": "PROCEDENTE",
  "parcela_cobravel_pct": 0,
  "causa_raiz_codigo": "DEFEITO_PECA",
  "texto": "...",
  "anexos": ["s3://..."],
  "assinatura": "..."
}
```
**Response 201:**
```json
{ "laudo_id": "uuid", "hash": "sha256:...", "imutavel": true }
```
**Códigos:** 201, 403, 409 (já tem laudo assinado), 422.
**Eventos:** `Garantia.Analisada` + (`Procedente` | `Improcedente` | `Parcial`).
**Invariantes:** `INV-001`, `INV-013`.
**US:** `US-GAR-003`.

---

### `GET /v1/garantias/{id}`
**Propósito:** detalhe + laudo + eventos.
**Response 200:** entidade completa.

---

### `POST /v1/garantias/{id}/desbloquear-cobranca`
**Propósito:** gerente libera cobrança manualmente.
**Papel:** GERENTE_OPERACIONAL.
**Request:** `{ "motivo": "..." }`
**Response 200:** `{ "desbloqueado_em": "...", "desbloqueado_por": "uuid" }`
**Eventos:** audit log gravado (`INV-001`).
**US:** `US-GAR-005`.

---

### `POST /v1/garantia-fornecedor`
**Propósito:** abrir ciclo de garantia com fornecedor.
**Papel:** COMPRADOR.
**Request:**
```json
{
  "garantia_id": "uuid",
  "fornecedor_id": "uuid",
  "peca_id": "uuid",
  "nota_remessa": "NFe-...",
  "data_envio": "2026-05-17",
  "prazo_retorno": "2026-06-17",
  "valor_enviado": 1200.00
}
```
**Response 201:** id criado.
**Eventos:** `GarantiaFornecedor.Aberta`.
**US:** `US-GAR-006`.

---

### `POST /v1/garantia-fornecedor/{id}/retorno`
**Propósito:** registrar retorno do fornecedor.
**Request:** `{ "valor_ressarcido": 1200.00, "observacao": "..." }`
**Response 200:** status RETORNADA.
**Eventos:** `GarantiaFornecedor.Retornada`.

---

### `GET /v1/garantias/reincidencia?escopo=PECA_MODELO&janela=6m`
**Propósito:** dashboard de reincidência.
**Response 200:** array ordenado por `qtd_procedentes_6m` desc.
**US:** `US-GAR-007`.

---

## Eventos consumidos

- `OS.Concluida` (do módulo OS) → atualiza data-limite-garantia.
- `OS.Reaberta` (do módulo OS) → checa se cabe abrir garantia automaticamente.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- `POST /v1/garantias`: 60 req/min/tenant.
- `GET /v1/garantias/reincidencia`: 30 req/min/tenant (consulta cara).

## Versionamento

v1, v2 coexistem 6 meses. Quebra de contrato → ADR + CHANGELOG.
