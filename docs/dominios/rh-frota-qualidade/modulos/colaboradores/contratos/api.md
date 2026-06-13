---
owner: Roldão
revisado-em: 2026-06-13
status: draft
modulo: colaboradores
dominio: rh-frota-qualidade
---

# Contrato API — Colaboradores

> Stack ainda não decidida (ADR-0001 pendente). Convenções abaixo são tentativas — assume REST + JSON. Substituir por gRPC/GraphQL se ADR mudar.

## Endpoints MVP-1

### `GET /api/v1/colaboradores`
- **Query params:** `papel?`, `vinculo?`, `ativo?` (bool), `habilidade?`, `q?` (busca nome/cpf), `page?`, `page_size?` (≤100).
- **Auth:** Dono / Gerente / Qualidade(read).
- **Tenant:** `tenant_id` derivado do JWT (INV-TENANT-001).
- **Resposta:** Lista paginada `{ items, total, page }`.

### `POST /api/v1/colaboradores`
- **Body:** `{ nome, cpf, email, telefone, vinculo, papeis: [...], habilidades: [...], comissao_default_pct, documentos: [...] }`.
- **Auth:** Dono.
- **Validações:**
  - CPF formato + dígito verificador.
  - UNIQUE (tenant_id, cpf) → 409 `{ error: "DUPLICATE_CPF", message: "..." }` (INV-024 espelhado).
  - Papel SIGNATARIO sem escopo → 422 `{ error: "SIGNATARIO_SEM_ESCOPO" }` (INV-003).
  - Papel MOTORISTA_UMC sem CNH → **salva com `pendencia_cnh=true`** (R-COL-1). Não retorna 422 no cadastro; o bloqueio ocorre na alocação (frota/agenda).
- **Audit:** Grava INV-001.

### `GET /api/v1/colaboradores/{id}`
- Retorna agregado completo (papéis, habilidades, documentos, comissão).

### `PATCH /api/v1/colaboradores/{id}`
- Mesmo body do POST (partial). CPF imutável após criação.

### `DELETE /api/v1/colaboradores/{id}`
- **Soft delete** = desligamento. Body: `{ data_desligamento, motivo }`. Revoga papéis em cascade.
- Hard delete bloqueado se existe OS / certificado referenciando (INV-025 espírito).

### `POST /api/v1/colaboradores/{id}/papeis`
- Body: `{ papel, data_inicio, escopo_id? }`.

### `DELETE /api/v1/colaboradores/{id}/papeis/{papel_id}`
- Marca revogado_em (não deleta linha — audit).

### `POST /api/v1/colaboradores/{id}/habilidades`
- Body: `{ habilidade_codigo?, habilidade_descricao?, nivel, evidencia_url? }`.

### `GET /api/v1/colaboradores/{id}/auditoria`
- Lista trilha INV-001 (apenas Dono / Qualidade).

## Endpoints de consulta (read-only pra outros módulos)

### `GET /api/v1/colaboradores/elegiveis?habilidade=X&papel=TECNICO`
- Consumido por Operação na alocação de OS.
- Retorna apenas colaboradores ativos com habilidade + papel solicitados.

### `GET /api/v1/colaboradores/{id}/comissao-vigente`
- Consumido por Financeiro no fechamento de comissão BIG-09.
- Retorna `{ pct_default, vigente_desde }`.

## Erros padronizados

```json
{ "error": "CODIGO", "message": "Mensagem em PT-BR sem jargão", "field": "campo_opcional" }
```

Códigos: `DUPLICATE_CPF`, `SIGNATARIO_SEM_ESCOPO`, `CPF_INVALIDO`, `TENANT_LIMIT_EXCEEDED`, `COLABORADOR_INATIVO`.

> **Removidos (R-COL-1/2):** `MOTORISTA_SEM_CNH` — MOTORISTA_UMC sem CNH salva com pendência (não 422); `ASO` — dado de saúde art. 11, dono é módulo `seguranca-trabalho`.

## Rate limit

[INFERÊNCIA] 100 req/min por tenant em endpoints de escrita. Ajustar pós-piloto.

## Não-existem MVP-1

Endpoints de holerite, ponto, férias, eSocial. → V2.
