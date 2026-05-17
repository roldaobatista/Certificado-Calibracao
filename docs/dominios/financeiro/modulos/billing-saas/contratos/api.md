---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Billing SaaS

> Endpoints REST. Formato final pós ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação: Bearer token.
- Tenant: `X-Tenant-ID` header (`INV-TENANT-001`).
- Erros: RFC 7807 Problem Details.
- Idempotência: mutação aceita `Idempotency-Key`.
- Webhooks de gateway: HMAC signature verificada (`SEC-PCI-001`).

---

## Endpoints (tenant-facing)

### `GET /v1/billing/planos`
**Propósito:** lista planos ativos do catálogo.
**Autorização:** pública (sem login) OU autenticada (filtra por elegibilidade).
**Response:** `[{id, codigo, nome, preco_mensal, preco_anual, limites:{...}, modulos_liberados:[...], trial_dias}]`.

---

### `POST /v1/billing/assinaturas`
**Propósito:** contratar plano.
**Request:**
```json
{
  "plano_id": "uuid",
  "ciclo": "mensal",
  "cupom": "OPCIONAL",
  "metodo_pagamento": {"gateway_token": "tok_xxx"}
}
```
**Response:** `201 {assinatura_id, status, trial_termina_em}`.
**Códigos:** 201, 400 (input), 401, 403, 409 (já tem assinatura ativa), 422 (cupom inválido).
**Invariantes:** constraint `UNIQUE (tenant_id) WHERE status='ativa'` (1 assinatura ativa por tenant), `INV-TENANT-001`.
**US:** `US-BIL-001`.
**Eventos:** `BillingSaas.AssinaturaCriada`.

---

### `GET /v1/billing/assinaturas/minha`
**Propósito:** estado da assinatura do tenant atual.
**Response:** `{id, plano, status, proximo_vencimento, uso:{usuarios:X/Y, modulos:[...], ...}, cupons_ativos:[...]}`.
**US:** `US-BIL-007`.

---

### `PATCH /v1/billing/assinaturas/minha/plano`
**Propósito:** upgrade/downgrade.
**Request:** `{novo_plano_id, ciclo?}`.
**Response:** `{status:"upgrade_aplicado"|"downgrade_agendado", efetivo_em}`.
**Códigos:** 200, 400, 422 (downgrade impossível por uso atual > limite novo plano).
**US:** `US-BIL-004`.
**Eventos:** `BillingSaas.PlanoMudou`.

---

### `DELETE /v1/billing/assinaturas/minha`
**Propósito:** cancelar assinatura.
**Request:** `{motivo}`.
**Response:** `200 {efetivo_em, dados_preservados_ate}`.
**Códigos:** 200, 409 (já cancelada).
**Eventos:** `BillingSaas.AssinaturaCancelada`.

---

### `POST /v1/billing/cupons/aplicar`
**Propósito:** aplicar cupom à assinatura ativa.
**Request:** `{codigo}`.
**Response:** `200 {desconto:{tipo, valor}, ciclos_restantes}`.
**Códigos:** 200, 404 (cupom não existe), 422 (expirado/esgotado/não aplicável).
**US:** `US-BIL-006`.

---

### `GET /v1/billing/faturas`
**Propósito:** lista faturas do tenant.
**Query:** `?status=&periodo_inicio=&periodo_fim=&page=`.
**Response:** lista paginada.

---

### `GET /v1/billing/faturas/{id}/pdf`
**Propósito:** baixa PDF da fatura.
**Response:** `200 application/pdf`.

---

### `POST /v1/billing/faturas/{id}/pagar`
**Propósito:** tenta cobrança manual (regularização).
**Response:** `200 {status:"paga"|"falhou", motivo?}`.

---

### `GET /v1/billing/faturas/{id}/nfse`
**Propósito:** consulta o estado da NFS-e emitida pela assinatura SaaS (US-BIL-008).
**Response:** `200 {nfse_id, status:"pendente"|"emitida"|"rejeitada"|"cancelada", authorization_code?, pdf_url?, rejection_reason?, emitida_em?}`.
**Códigos:** 200, 404 (fatura ainda não paga ou NFS-e não disparada).
**US:** `US-BIL-008`.

---

### `GET /v1/billing/faturas/{id}/nfse/pdf`
**Propósito:** baixa PDF da NFS-e da assinatura.
**Response:** `200 application/pdf`; 409 se NFS-e ainda não autorizada.
**US:** `US-BIL-008`.

---

## Endpoints (admin Aferê — operador comercial)

### `POST /v1/billing/admin/planos`
**Propósito:** cria/versiona plano. **Papel:** `operador_comercial_afere`.

### `POST /v1/billing/admin/cupons`
**Propósito:** cria cupom. **Request:** `{codigo, tipo, valor, validade_inicio, validade_fim, usos_max, recorrencia, planos_aplicaveis?}`.

### `POST /v1/billing/admin/assinaturas/{id}/reativar`
**Propósito:** força reativação (cliente VIP, negociação). **Request:** `{motivo}` (obrigatório — vai pro histórico).

### `GET /v1/billing/admin/metricas`
**Response:** `{mrr, churn_mensal, conversao_trial, inadimplencia_pct, ...}`.

### `POST /v1/billing/admin/faturas/{id}/nfse/reemitir`
**Propósito:** força reemissão de NFS-e após rejeição (US-BIL-008 fallback manual após investigação).
**Papel:** `operador_comercial_afere` + **MFA obrigatório** (`SEC-MFA-001`).
**Request:** `{motivo}` (vai pra trilha WORM).
**Codigos:** 200, 409 (já emitida com sucesso — bloqueado por `INV-026`).

### `POST /v1/billing/admin/gateway/configurar`
**Propósito:** cadastra/atualiza chaves de API e segredo de webhook do gateway de pagamento.
**Papel:** `operador_comercial_afere` + **MFA obrigatório** (`SEC-MFA-001` — `AC-BIL-002-4`).
**Request:** `{gateway, api_key_cipher, webhook_secret_cipher, ambiente:"sandbox"|"production"}`.
**Resposta:** `201 {gateway_config_id, configurado_em}`.
**Auditoria:** registro WORM obrigatório (`INV-001`); chaves cifradas via KMS (`INV-009`).

---

## Webhooks (entrada — gateway → Aferê)

### `POST /v1/billing/webhooks/{gateway}`
**Propósito:** recebe eventos do gateway (cobrança aprovada, recusada, chargeback).
**Autenticação:** HMAC signature header (verificada — falha = 401).
**Eventos suportados:** `charge.succeeded`, `charge.failed`, `subscription.cancelled`, `chargeback.created`.
**Idempotência:** dedupe por `gateway_event_id`.
**Response:** `200 OK` (sempre — erros internos não devem fazer gateway retentar).
**Internamente:** processamento assíncrono via fila procrastinate.

---

## Eventos consumidos de outros módulos

- `Auth.UsuarioCriado` (para enforcement de limite de usuários do plano).

---

## Rate limits

- `POST /v1/billing/assinaturas` — 5 req/min/tenant.
- `POST /v1/billing/cupons/aplicar` — 10 req/min/tenant.
- Webhooks: sem limite (mas idempotência protege).

---

## Versionamento

- v1 estável; v2 coexistirá 6 meses ao quebrar contrato.
- Mudança em contrato de webhook = comunicar gateway antes.

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US.
- Webhook novo (gateway nova) → ADR + spec específica.
