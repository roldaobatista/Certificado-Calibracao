---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/adr/0006-feature-flags.md
---

# Contratos API — Módulo Release Management

---

## Convenções

- REST sobre HTTPS.
- Auth: Bearer token. Admin Aferê (gestão de flags/releases) requer papel global; tenant admin gerencia próprios opt-ins.
- Tenant: `INV-TENANT-001`.
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key`.

---

## Endpoints — Releases e Notas

### `GET /v1/releases`
**Propósito:** Histórico de releases.
**Query:** `ambiente`, `tipo`, `desde`, `ate`, `page`.
**Auth:** opcional (releases podem ser públicas).
**Códigos:** 200.

### `GET /v1/releases/{versao_semver}`
**Propósito:** Detalhe + notas.

### `POST /v1/releases` (admin)
**Propósito:** Criar rascunho.
**Request:**
```json
{"versao_semver":"2.5.0","tipo":"minor","commit_hash":"...","ambiente":"producao","requer_janela_manutencao":false}
```

### `POST /v1/releases/{id}/notas` (admin)
**Propósito:** Anexar release notes.

### `POST /v1/releases/{id}/publicar` (admin)
**Propósito:** Mudar status pra publicada.
**Validação:** notas presentes, breaking_changes (se MAJOR) preenchidos.
**Eventos:** `release.publicada`.
**US:** `US-REL-001`, `US-REL-002`.

### `POST /v1/releases/{id}/reverter` (SRE + aprovação)
**Propósito:** Rollback.
**Eventos:** `release.revertida`.

---

## Endpoints — Feature Flags

> Schema e regras detalhadas em `docs/adr/0006-feature-flags.md`.

### `GET /v1/feature-flags` (admin)
**Propósito:** Listar flags.
**Query:** `status`, `tipo`, `proprietario_modulo`, `cleanup_pendente`.

### `POST /v1/feature-flags` (admin)
**Propósito:** Criar flag.
**Request:**
```json
{"chave":"novo-editor-os","descricao":"...","tipo":"boolean","valor_default":false,"proprietario_modulo":"operacao/ordens-servico"}
```
**Response 201:** flag + `data_revisao_obrigatoria` = criada_em + 90d.
**Eventos:** `feature_flag.alterada`.

### `PUT /v1/feature-flags/{chave}/regras` (admin)
**Propósito:** Substituir conjunto de regras.
**Request:**
```json
{"regras":[{"escopo":"tenant","escopo_valor":"tenant-uuid","valor":true,"prioridade":1},{"escopo":"plano","escopo_valor":"enterprise","valor":true,"prioridade":2}]}
```
**Eventos:** `feature_flag.alterada` + cache invalidado.
**Invariantes:** `INV-001` (auditoria de mudança).
**US:** `US-REL-003`.

### `POST /v1/feature-flags/{chave}/aposentar` (admin)
**Propósito:** Cleanup.
**Eventos:** `feature_flag.aposentada`.

### `GET /v1/feature-flags/avaliar` (tenant + cliente em runtime)
**Propósito:** Avaliar flags para o contexto atual (tenant + usuário).
**Query:** `chaves` (array — bulk pra performance).
**Response 200:**
```json
{"novo-editor-os": true, "exportacao-bulk": false}
```
**SLO:** < 10ms p95 (cache local + invalidação push).

---

## Endpoints — Beta

### `POST /v1/release/beta/inscricoes` (tenant admin)
**Propósito:** Inscrever tenant no beta.
**Eventos:** `beta.tenant_inscrito`.
**US:** `US-REL-004`.

### `DELETE /v1/release/beta/inscricoes/{tenant_id}` (tenant admin)
**Propósito:** Cancelar.
**Eventos:** `beta.tenant_cancelado`.

---

## Endpoints — Homologação

### `POST /v1/release/homologacao/ambientes` (tenant Enterprise)
**Propósito:** Provisionar.
**US:** `US-REL-005`.

### `POST /v1/release/homologacao/ambientes/{id}/atualizar-snapshot`
**Propósito:** Atualizar dados anonimizados.

### `DELETE /v1/release/homologacao/ambientes/{id}`
**Propósito:** Desprovisionar.

---

## Endpoints — Migrações

### `POST /v1/release/migracoes` (SRE)
**Propósito:** Planejar migração.
**Request:**
```json
{"release_id":"...","nome":"add-coluna-x","tipo":"aditiva","plano_rollback":"..."}
```

### `POST /v1/release/migracoes/{id}/aprovar` (aprovador)
**Validação:** destrutiva exige 2 aprovadores diferentes.
**US:** `US-REL-006`.

### `POST /v1/release/migracoes/{id}/executar` (SRE)
**Validação:** status aprovada.
**Eventos:** `migracao.iniciada`, `migracao.checkpoint`, `migracao.concluida` ou `migracao.falhou`.

### `POST /v1/release/migracoes/{id}/reverter` (SRE)
**Validação:** checkpoints reversíveis disponíveis.

---

## Endpoints — Breaking Changes

### `POST /v1/release/breaking-changes` (PM)
**Propósito:** Anunciar.
**Validação:** `efetivo_em - anunciado_em >= 60 dias`.
**Eventos:** `breaking_change.anunciado`.
**US:** `US-REL-008`.

### `GET /v1/release/breaking-changes`
**Propósito:** Listar (público).

### `GET /v1/public/breaking-changes` (sem auth)
**Propósito:** Integradores consultam sem token.

**Headers de deprecation em endpoints afetados:**
- `Deprecation: true`
- `Sunset: <data RFC 7231>`
- `Link: <guia_migracao>; rel="deprecation"`

---

## Endpoints — Recursos por Plano

### `GET /v1/release/recursos-plano/{chave_flag}`
**Propósito:** Quais planos têm acesso à feature.
**US:** `US-REL-010`.

---

## Rate limits

- Avaliação de flag: alta (10k req/min/tenant — bulk preferível).
- Mutações admin: 60/min/admin.
- Default: 300/min/tenant.

## Versionamento

v1 ativa. Mudança em contrato de flag → ADR-0006 + janela 60d.

## Como evolui

Endpoint novo → US. Quebra → ADR + janela + headers Deprecation.
