---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Engenharia Técnica

> Endpoints do módulo. Formato consolidado em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação: header `Authorization: Bearer ...`.
- Tenant: `X-Tenant-ID` ou claim. `INV-TENANT-001` aplica.
- Erros: RFC 7807.
- Idempotência: mutações aceitam `Idempotency-Key`.
- Upload de anexo grande: presigned URL para Backblaze B2 (evita passar bytes pelo backend).

---

## Endpoints — Projetos

### `POST /v1/engenharia/projetos`
**Propósito:** criar projeto técnico (rascunho).
**Request:** `{ "codigo", "titulo", "descricao", "cliente_id", "categoria", "equipamento_id_principal"? }`.
**Response 201:** `{ "id", "status": "rascunho", "revisao_corrente": { "id", "letra": "A" } }`.
**Códigos:** 201, 400, 401, 403, 409 (código duplicado), 422.
**US:** `US-ENG-001`.
**Eventos:** `Engenharia.ProjetoCriado`.

### `GET /v1/engenharia/projetos` (lista paginada com filtros)
### `GET /v1/engenharia/projetos/{id}`
### `PATCH /v1/engenharia/projetos/{id}` (metadados)

---

## Endpoints — Revisões

### `POST /v1/engenharia/projetos/{projeto_id}/revisoes`
**Propósito:** criar nova revisão (próxima letra).
**Request:** `{ "motivo_revisao": "...", "copiar_de_revisao_id"? }`.
**Response 201:** `{ "id", "letra": "B", "status": "rascunho" }`.

### `POST /v1/engenharia/revisoes/{id}/submeter`
**Propósito:** submeter revisão para aprovação.
**Request:** `{ "aprovador_id"?, "via_bpm"? }`.
**Response 200:** status `em_aprovacao`.
**Eventos:** `Engenharia.RevisaoSubmetida`.
**US:** `US-ENG-002`.

### `POST /v1/engenharia/revisoes/{id}/aprovar`
**Request:** `{ "comentario"?, "tipo_assinatura": "interna"|"icp_brasil", "assinatura_payload": {...} }`.
**Response 200:** status `aprovada`; AprovacaoTecnica criada.
**Códigos:** 200, 403 (sem permissão), 409 (não está em aprovação), 422.
**Eventos:** `Engenharia.RevisaoAprovada`.
**US:** `US-ENG-002`.

### `POST /v1/engenharia/revisoes/{id}/rejeitar`
**Request:** `{ "comentario": "..." }`.
**Eventos:** `Engenharia.RevisaoRejeitada`.

### `POST /v1/engenharia/revisoes/{id}/marcar-obsoleta`
**Request:** `{ "motivo": "..." }`.

### `GET /v1/engenharia/revisoes/{id}`
### `GET /v1/engenharia/projetos/{projeto_id}/revisoes` (histórico)

### `GET /v1/engenharia/revisoes/diff?revisao_a={id}&revisao_b={id}`
**Response:** diff estruturado (campos, anexos add/del, BOM diff, memorial diff).
**US:** `US-ENG-007`.

---

## Endpoints — Anexos

### `POST /v1/engenharia/revisoes/{revisao_id}/anexos/presigned-url`
**Propósito:** obter URL pré-assinada do Backblaze B2 pra upload direto.
**Request:** `{ "nome_original", "mime_type", "tamanho_bytes", "categoria" }`.
**Response 200:** `{ "upload_url", "anexo_id" (provisório), "headers_obrigatorios": {...} }`.

### `POST /v1/engenharia/anexos/{id}/confirmar`
**Propósito:** confirmar conclusão do upload (cliente passou pelo B2; backend valida hash).
**Request:** `{ "hash_sha256" }`.
**Response 200:** `{ "id", "storage_path", "kms_key_id" }`.

### `GET /v1/engenharia/anexos/{id}` (metadados)
### `GET /v1/engenharia/anexos/{id}/download` (URL temporária)
### `DELETE /v1/engenharia/anexos/{id}` (soft delete; nunca apaga fisicamente em revisão aprovada)

---

## Endpoints — BOM

### `PUT /v1/engenharia/revisoes/{id}/bom`
**Propósito:** substituir BOM completa de uma revisão (em rascunho).
**Request:** `{ "linhas": [{"posicao","componente_id","descricao_ad_hoc","quantidade","unidade","referencia_desenho","observacao"}] }`.
**Códigos:** 200, 409 (revisão aprovada — imutável), 422 (posição duplicada).
**Eventos:** `Engenharia.BOMAtualizada`.
**US:** `US-ENG-005`.

### `GET /v1/engenharia/revisoes/{id}/bom`

---

## Endpoints — Biblioteca de Componentes

### `POST /v1/engenharia/biblioteca/componentes`
**Request:** `{ "fabricante","modelo","descricao","categoria","preco_referencial","unidade_padrao","datasheet_anexo_id"? }`.
**Códigos:** 201, 409 (fabricante+modelo já existe), 422.
**US:** `US-ENG-004`.

### `GET /v1/engenharia/biblioteca/componentes?q=...&categoria=...`
### `GET /v1/engenharia/biblioteca/componentes/{id}` (inclui contagem de projetos que usam)
### `PATCH /v1/engenharia/biblioteca/componentes/{id}`

---

## Endpoints — Memorial / Especificações / Cálculos

### `PUT /v1/engenharia/revisoes/{id}/memorial`
**Request:** `{ "escopo","premissas","solucoes","normas_aplicaveis","consideracoes_finais" }`.
**US:** `US-ENG-006`.

### `POST /v1/engenharia/revisoes/{id}/memorial/gerar-pdf`
**Response 202:** geração assíncrona; retorna `job_id`. Resultado consultado em `GET /v1/engenharia/jobs/{job_id}`.

### `PUT /v1/engenharia/revisoes/{id}/especificacoes`
**Request:** `{ "especificacoes": [{"chave","valor","unidade","tolerancia"}] }`.

### `POST /v1/engenharia/revisoes/{id}/calculos`
**Request:** `{ "titulo","valores_chave":{...},"planilha_anexo_id","metodo","norma_referencia" }`.

---

## Endpoints — Vinculação

### `POST /v1/engenharia/revisoes/{id}/vincular`
**Request:** `{ "entidade_tipo":"os|orcamento|equipamento|contrato","entidade_id","papel" }`.
**US:** `US-ENG-003`.

### `GET /v1/engenharia/revisoes/{id}/vinculacoes`
### `GET /v1/engenharia/entidades/{tipo}/{id}/projetos` (rastreabilidade reversa)

---

## Endpoints — Histórico

### `GET /v1/engenharia/projetos/{id}/historico`
**Response:** lista cronológica de HistoricoAlteracao.
**US:** `US-ENG-008`.

---

## Eventos consumidos

- `BPM.AprovacaoConcedida` (com `contexto.tipo == "engenharia.revisao"`) → dispara aprovação técnica.
- `BPM.AprovacaoRejeitada` (idem) → dispara rejeição.

Ver `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- Upload presigned URL: 30 req/min/usuário.
- Listagens: 60 req/min/usuário.
- Geração de PDF de memorial: 10 req/min/tenant (operação cara).

## Versionamento

- v1, v2 coexistem por 6 meses.
- Quebra de contrato (BOM, eventos) → ADR + janela.

## Como esta lista evolui

- Endpoint novo → linkar US.
- Quebra → ADR + janela.
- Descontinuação → `@deprecated` + headers Sunset.
