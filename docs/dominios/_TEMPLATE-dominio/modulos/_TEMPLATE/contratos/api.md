---
owner: roldao
revisado_em: 2026-05-16
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo [NOME] (TEMPLATE)

> Endpoints / IPC do módulo. Formato (REST / GraphQL / RPC) a definir em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`) ou header (a definir em ADR).
- Autenticação: via header `Authorization` (token Bearer ou similar — ver `auth/`).
- Tenant: identificado por header `X-Tenant-ID` OU subdomain OU dentro do token. INV-TENANT-001 exige presença em toda query.
- Erros: formato padrão (RFC 7807 Problem Details recomendado).
- Idempotência: endpoints de mutação aceitam `Idempotency-Key` header.

---

## Endpoints

### `POST /v1/[recurso]`
**Propósito:** [1 linha]
**Persona/papel autorizada:** [via RBAC]
**Request body:**
```json
{
  "campo1": "valor",
  "campo2": 123
}
```
**Response (sucesso):**
```json
{
  "id": "uuid",
  ...
}
```
**Response (erro):** padrão de erro
**Códigos:** 201 (criado), 400 (input inválido), 401 (não autenticado), 403 (sem permissão), 409 (conflito), 422 (validação)
**Invariantes:** `INV-NNN`
**US:** `US-[MOD]-NNN`
**Eventos disparados:** `[ModuloA].[EventoX]` (ver `../modelo-de-dominio.md`)

---

### `GET /v1/[recurso]/{id}`
(mesmo formato)

---

## Eventos consumidos de outros módulos

Ver `../../../comum/integracoes-inter-modulos.md` pra contrato detalhado.

## Rate limits

- [Endpoint sensível] — ex: 10 req/min/tenant
- Default: [definir em ADR-0001]

## Versionamento

- v1, v2 coexistem por 6 meses (janela de migração).
- Quebra de contrato exige ADR + bump CHANGELOG seção "Removido" ou "Modificado".

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US.
- Quebra de contrato → ADR + janela de migração + comunicação aos integradores.
- Endpoint descontinuado → marcar `@deprecated` + headers de Sunset (RFC 8594).
