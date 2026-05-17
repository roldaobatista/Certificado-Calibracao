---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: clientes
dominio: comercial
diataxis: reference
---

# Contratos API — Módulo Clientes

> Estilo REST/JSON. Formato final (REST puro vs GraphQL) a confirmar em ADR-0001.

## Convenções

- Prefixo `/v1/clientes`.
- Header `X-Tenant-ID` obrigatório (INV-TENANT-001 — toda query usa).
- Bearer token via `Authorization`.
- Erros: RFC 7807 (Problem Details).
- Idempotência: POST aceita `Idempotency-Key`.

## Endpoints

### `POST /v1/clientes`
Criar cliente PF ou PJ.
**Body:** `{tipo: "PF|PJ", documento, nome_ou_razao, telefones[], emails[], endereco?, contatos?, lgpd_aceite: {versao, canal}}`
**Resposta 201:** `{id, criado_em, ...campos}`
**Erros:** 400 (validação CPF/CNPJ), 409 (duplicado — retorna `{cliente_existente_id}`), 422 (LGPD aceite ausente).
**Invariantes:** INV-024, INV-TENANT-001/002.
**Evento:** `Cliente.Criado`.
**US:** US-CLI-001.

### `GET /v1/clientes`
Listar clientes com filtros.
**Query:** `q` (busca fuzzy), `segmento`, `rating`, `bloqueado`, `pagina`, `tamanho` (max 100).
**Resposta:** `{itens[], total, pagina, tamanho}`.

### `GET /v1/clientes/{id}`
Detalhes do cliente.
**Resposta:** todos os campos + arrays de endereços + contatos + segmentos + limite/uso + status bloqueio.

### `GET /v1/clientes/{id}/timeline`
Visão 360° — eventos cronológicos.
**Query:** `desde`, `ate`, `tipos[]`, `pagina`.
**Resposta:** `{eventos[], proximo_cursor}`.
**Performance:** p95 < 1.5s para até 500 eventos (US-CLI-002).

### `PATCH /v1/clientes/{id}`
Atualizar campos seletivos.
**Body:** subset de campos.
**Erros:** 409 (conflito de versão — optimistic locking).
**Evento:** `Cliente.Atualizado`.

### `POST /v1/clientes/{id}/bloquear`
Aplicar bloqueio comercial.
**Body:** `{motivo, justificativa}`.
**Permissão:** financeiro ou dono.
**Evento:** `Cliente.Bloqueado`.
**US:** US-CLI-004.

### `POST /v1/clientes/{id}/desbloquear`
Remover bloqueio.
**Body:** `{justificativa}`.
**Evento:** `Cliente.Desbloqueado`.

### `POST /v1/clientes/dedup/preview`
Sugerir duplicatas de um documento/contato.
**Body:** `{documento?, telefone?, email?}`.
**Resposta:** lista de clientes candidatos com score.

### `POST /v1/clientes/{id}/mesclar`
Mesclar 2 cadastros (US-CLI-005).
**Body:** `{cliente_perdedor_id, campos_escolhidos: {...}}`.
**Resposta 200:** `{cliente_master_id, eventos_migrados: N}`.
**Evento:** `Cliente.Dedup.Mesclado`.

### `POST /v1/clientes/importar`
Importação em lote (US-CLI-003).
**Body multipart:** arquivo CSV/XLSX + opcional `mapeamento` JSON.
**Resposta 202 (async):** `{job_id}`.

### `GET /v1/clientes/importar/{job_id}`
Status do job de importação.
**Resposta:** `{status: "rodando|concluido|falhou", criados, atualizados, rejeitados, erros[]}`.

### `GET /v1/clientes/{id}/exportar`
Exportar dados do cliente (LGPD art. 18 — portabilidade).
**Query:** `formato` (json/csv).
Ver `exports.md`.

### `DELETE /v1/clientes/{id}`
**SOFT-DELETE.** Não remove fisicamente — marca `arquivado_em`.
**Permissão:** dono ou DPO.
**Restrição:** se houver NF-e emitida, bloqueia hard-delete por retenção fiscal (INV-026 + retenção).

## Eventos consumidos

- `OS.Concluida` (operação) → atualiza timeline + métrica `ultima_os_em`.
- `Certificado.Emitido` (operação) → timeline.
- `Fatura.Vencida` (financeiro) → considera bloqueio automático via régua OP11.
- `NPS.Respondido` (crm) → timeline + atualiza rating se regra ativa.

## Rate limits

- `POST /clientes`: 60 req/min/tenant.
- `POST /importar`: 5 req/hora/tenant.
- Demais: 600 req/min/tenant (default).

## Versionamento

v1, v2 coexistem 6 meses. Quebra exige ADR.

## Como evolui

Endpoint novo → linkar US-CLI-NNN. Quebra → ADR + comunicação.
