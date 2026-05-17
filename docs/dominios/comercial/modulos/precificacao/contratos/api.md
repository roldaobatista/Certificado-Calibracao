---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Precificação

> Endpoints do módulo. Formato (REST / GraphQL) a definir em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Auth: token Bearer obrigatório em todos os endpoints (não há endpoint público).
- Tenant: header `X-Tenant-ID` ou subdomínio; INV-TENANT-001 exige presença.
- RBAC: roles `gestor_pricing`, `aprovador_desconto`, `vendedor` (calculo).
- Erros: RFC 7807.
- Idempotência: `Idempotency-Key` em mutações.
- Determinismo: `calcularPreco` é determinístico (mesmo input → mesmo output, dado mesma versão de regras).

---

## Endpoints — Regras de formação de preço

### `GET /v1/regras`
**Propósito:** lista regras ativas + rascunhos.
**Query:** `item_id?`, `status?` (ativa/rascunho), `page`.
**Códigos:** 200.
**RBAC:** gestor_pricing.

### `POST /v1/regras`
**Propósito:** cria rascunho de regra.
**Request:**
```json
{
  "item_catalogo_id": "uuid",
  "modo": "margem_alvo",
  "margem_alvo_percentual": 25.0,
  "margem_piso_percentual": 5.0
}
```
**Códigos:** 201, 422.
**RBAC:** gestor_pricing.

### `POST /v1/regras/{id}/publicar`
**Propósito:** publica rascunho como nova versão imutável.
**Códigos:** 200, 409 (rascunho inválido), 422.
**Eventos:** `Precificacao.RegraPublicada`.
**Invariantes:** INV-026.

---

## Endpoints — Tabelas de preço

### `GET /v1/tabelas`
**Códigos:** 200.

### `POST /v1/tabelas`
**Propósito:** cria rascunho de tabela.
**Request:** `{ nome, tipo, criterio_aplicacao, validade_de?, validade_ate? }`.
**Códigos:** 201.

### `PATCH /v1/tabelas/{id}/precos`
**Propósito:** define preços por item no rascunho.
**Request:** `{ itens: [{ item_id, preco_sugerido, preco_minimo, desconto_max_padrao }] }`.
**Códigos:** 200.

### `POST /v1/tabelas/{id}/publicar`
**Propósito:** publica nova versão imutável.
**Códigos:** 200.
**Eventos:** `Precificacao.TabelaPublicada`.
**Invariantes:** INV-026.

### `GET /v1/tabelas/aplicavel`
**Propósito:** resolve qual tabela se aplica a um cliente/contexto.
**Query:** `cliente_id`, `regiao?`, `contrato_id?`.
**Response:** `{ tabela_id, versao, precedencia_aplicada }`.

---

## Endpoints — Cálculo de preço

### `POST /v1/calcular`
**Propósito:** calcula preço sugerido, mínimo, margem resultante.
**Request:**
```json
{
  "item_catalogo_id": "uuid",
  "cliente_id": "uuid",
  "quantidade": 1,
  "deslocamento_km": 50,
  "desconto_percentual_aplicado": 10.0,
  "vendedor_id": "uuid",
  "regime_fiscal_cliente": "simples_nacional",
  "parcelamento": { "parcelas": 3 }
}
```
**Response:**
```json
{
  "calculo_id": "uuid",
  "preco_sugerido": 150.00,
  "preco_minimo": 110.00,
  "preco_aplicado_apos_desconto": 135.00,
  "margem_bruta_percentual": 25.0,
  "margem_liquida_percentual": 18.0,
  "imposto_simulado": 13.50,
  "comissao_simulada": 6.75,
  "custo_deslocamento": 25.00,
  "parcela_valor": 47.81,
  "alerta_abaixo_minimo": false,
  "regra_versao": "v3",
  "tabela_versao": "v7"
}
```
**Códigos:** 200, 422 (faltam dados), 409 (sem regra cadastrada).
**Performance:** p95 < 200ms.
**RBAC:** vendedor + gestor_pricing.
**Invariantes:** INV-026 (snapshot persistido).

### `GET /v1/calcular/{calculo_id}`
**Propósito:** recupera snapshot de cálculo (auditoria).
**Códigos:** 200, 404.

---

## Endpoints — Aprovação de desconto

### `POST /v1/aprovacoes`
**Propósito:** vendedor solicita aprovação.
**Request:** `{ orcamento_id, item_orcamento_id?, desconto_percentual, margem_resultante, justificativa? }`.
**Códigos:** 201.
**Eventos:** `Precificacao.AprovacaoSolicitada`.

### `GET /v1/aprovacoes`
**Propósito:** lista pedidos (filtro por status, aprovador).
**Query:** `status?`, `aprovador_papel?`, `vendedor_id?`, `page`.
**RBAC:** aprovador_desconto vê os próprios; gestor_pricing vê todos.

### `POST /v1/aprovacoes/{id}/decidir`
**Propósito:** aprovador decide.
**Request:** `{ decisao: "aprovado" | "negado", justificativa? }`.
**Códigos:** 200, 403 (não é aprovador desta faixa), 409 (já decidido).
**Eventos:** `Precificacao.AprovacaoDecidida`.

---

## Endpoints — Faixas de aprovação

### `GET /v1/faixas-aprovacao` / `POST` / `PATCH` / `DELETE`
**Propósito:** CRUD de faixas.
**RBAC:** gestor_pricing.
**Validação:** sem sobreposição no mesmo escopo (422 se violar).

---

## Endpoints — Histórico

### `GET /v1/historico-preco-praticado`
**Query:** `item_id?`, `cliente_id?`, `de`, `ate`, `page`.
**Response:** série temporal + estatísticas.
**RBAC:** gestor_pricing.
**Invariantes:** WORM (só leitura).

---

## Endpoints — Parâmetros do tenant

### `GET /v1/parametros` / `PATCH /v1/parametros`
**Propósito:** ler/configurar custo_por_km, taxa_juros_parcelamento, regime_fiscal_default, margem_piso_default.
**RBAC:** gestor_pricing.

---

## Eventos consumidos

Ver `../modelo-de-dominio.md`.

## Rate limits

- `POST /v1/calcular`: 600 req/min/tenant (alto, é em tempo real na UI).
- Demais mutações: 60 req/min/usuário.

## Versionamento

- v1 e v2 coexistem por 6 meses.
- Mudança em fórmula de cálculo → ADR (impacto em audit trail).

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US.
- Quebra → ADR + janela.
- Endpoint descontinuado → `@deprecated` + Sunset header.
