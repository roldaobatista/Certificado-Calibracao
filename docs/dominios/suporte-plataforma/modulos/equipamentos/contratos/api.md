---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: equipamentos
dominio: suporte-plataforma
---

# Contratos de API — Equipamentos do cliente

## Convenções

- Versionamento via path (`/v1/`) — [INFERÊNCIA] confirmar em ADR-0001.
- Auth via Bearer. Tenant via header `X-Tenant-ID` (`INV-TENANT-001`).
- Erros formato RFC 7807.
- Mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `POST /v1/equipamentos`
**Propósito:** cadastrar equipamento.
**Autorização:** metrologista, almoxarife, atendente.
**Request:**
```json
{
  "cliente_id": "uuid",
  "tag": "BAL-001",
  "numero_serie": "ABC123",
  "fabricante": "Toledo",
  "modelo": "9094",
  "faixa_medicao": "0-30kg",
  "classe_exatidao": "III"
}
```
**Response 201:** equipamento + URL do QR.
**Erros:** 409 (TAG duplicada no tenant), 422 (cliente inexistente).
**Invariantes:** `INV-TENANT-001`.
**US:** US-EQP-001.
**Eventos:** `Equipamento.cadastrado`.

---

### `GET /v1/equipamentos/{id}`
**Propósito:** ficha 360°.
**Response 200:** equipamento + versões + histórico cert. + OS abertas + eventos.
**US:** US-EQP-003.

---

### `GET /v1/equipamentos?busca=&status=&cliente_id=`
**Propósito:** lista.
**Response 200:** paginação cursor.

---

### `PATCH /v1/equipamentos/{id}`
**Propósito:** editar atributo.
**Comportamento:**
- Campo imutável (TAG, NS, fabricante) com `cert_emitido=true` → 422 "campo imutável após emissão".
- Campo versionável com `cert_emitido=true` → cria `EquipamentoVersao` nova.
- Sem certificado → UPDATE direto.

**Erros:** 422 (INV-025), 404, 403.
**Invariantes:** `INV-025`.
**US:** US-EQP-002.
**Eventos:** `Equipamento.versao_criada` (se aplicável).

---

### `POST /v1/equipamentos/{id}/sucatear`
**Pré:** sem OS aberta.
**Erros:** 409 (OS aberta).
**Eventos:** `Equipamento.sucateado`.

---

### `POST /v1/equipamentos/{id}/transferir`
**Request:** `{ "novo_cliente_id": "uuid", "motivo": "string" }`
**Eventos:** `Equipamento.transferido`.

---

### `GET /v1/equipamentos/{id}/qr`
**Response:** PDF da etiqueta.

---

### `GET /v1/qr/{hash}` (público autenticado)
**Propósito:** redireciona scanner para ficha 360°.
**Erros:** 404 (QR revogado/equip. removido).

---

## Rate limits

- `GET /v1/qr/*`: 60 req/min/usuário.
- Default: a definir ADR-0001.

## Versionamento

v1, v2 coexistem por 6 meses. Quebra de contrato → ADR + janela de migração.

## Como evolui

- Endpoint novo → linkar US.
- Quebra de contrato → ADR.
