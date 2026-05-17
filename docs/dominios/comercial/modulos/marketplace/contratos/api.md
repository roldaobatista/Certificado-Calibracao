---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de API — Módulo Marketplace

> Endpoints do módulo. Formato (REST / GraphQL) a definir em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`).
- Autenticação:
  - Vitrine pública: SEM auth obrigatória (endpoints `/public/`).
  - Área do cliente: token Bearer (`Authorization: Bearer <jwt>`).
  - Curadoria: token Bearer + RBAC role `gestor_catalogo`.
- Tenant: subdomínio da URL identifica o tenant; INV-TENANT-001 exige presença em toda query no backend.
- Erros: RFC 7807 Problem Details.
- Idempotência: `Idempotency-Key` em mutações.
- Rate limit forte em endpoints públicos (anti-spam/scraping).

---

## Endpoints públicos (sem auth)

### `GET /v1/public/vitrine`
**Propósito:** retorna metadados da vitrine + categorias.
**Response:** `{ tenant_slug, tema, idioma, categorias: [...] }`.
**Códigos:** 200, 404 (tenant sem marketplace).
**US:** US-MKT-001.

### `GET /v1/public/vitrine/itens`
**Propósito:** lista paginada de itens publicados.
**Query:** `categoria?`, `destaque?`, `busca?`, `page`, `page_size`.
**Response:** `{ itens: [...], total, page }`.
**Códigos:** 200.
**Rate limit:** 60 req/min/IP.
**US:** US-MKT-001.

### `GET /v1/public/vitrine/itens/{slug}`
**Propósito:** detalhe do item.
**Response:** ficha completa + preço (se tabela pública).
**Códigos:** 200, 404, 410 (descontinuado).
**US:** US-MKT-001.

### `POST /v1/public/carrinho`
**Propósito:** cria carrinho anônimo.
**Request:** `{ session_id, utm?: {...} }`.
**Response:** `{ carrinho_id, expira_em }`.
**Códigos:** 201.
**Rate limit:** 10 req/min/IP.

### `POST /v1/public/carrinho/{id}/itens`
**Propósito:** adiciona item ao carrinho (com snapshot de preço).
**Request:** `{ item_vitrine_id, quantidade }`.
**Response:** `{ item_carrinho_id, preco_snapshot }`.
**Códigos:** 201, 404, 422.
**Invariantes:** INV-026 (snapshot).

### `PATCH /v1/public/carrinho/{id}/itens/{item_id}`
**Propósito:** ajustar quantidade ou remover (qty=0).
**Códigos:** 200, 204, 404.

### `POST /v1/public/solicitacao`
**Propósito:** envia carrinho como solicitação de orçamento.
**Request:**
```json
{
  "carrinho_id": "uuid",
  "dados_contato": { "nome": "...", "telefone": "...", "email": "...", "documento": "..." },
  "canal_preferido": "whatsapp",
  "observacoes": "...",
  "termo_lgpd_aceito": true,
  "captcha_token": "..."
}
```
**Response:** `{ solicitacao_id, protocolo, link_acompanhamento }`.
**Códigos:** 201, 400, 422 (LGPD não aceito), 429 (rate limit).
**Eventos:** `Marketplace.SolicitacaoEnviada`.
**Rate limit:** 5 req/hora/IP + CAPTCHA.
**US:** US-MKT-002.

---

## Endpoints autenticados (área do cliente)

### `POST /v1/auth/login`
**Propósito:** login do cliente.
**Request:** `{ email, senha }` ou `{ email, magic_link_token }`.
**Response:** `{ token, expira_em, cliente_id, escopo_visao: [...] }`.
**Códigos:** 200, 401, 423 (bloqueado por tentativas).

### `GET /v1/area-cliente/dashboard`
**Propósito:** resumo do cliente logado.
**Response:** `{ solicitacoes_abertas, orcamentos_pendentes, os_andamento, contratos_ativos, faturas_pendentes }`.
**US:** US-MKT-003.

### `GET /v1/area-cliente/orcamentos`
**Propósito:** lista orçamentos do cliente.
**Query:** `status?`, `page`.
**Códigos:** 200.

### `POST /v1/area-cliente/orcamentos/{id}/aprovar`
**Propósito:** aprovação 1-clique (reusa fluxo US-ORC-002).
**Códigos:** 200, 403, 410 (expirado).
**Eventos:** `Orcamentos.Aprovado`.

### `POST /v1/area-cliente/recorrentes`
**Propósito:** assinar serviço recorrente.
**Request:** `{ item_vitrine_id, periodicidade, observacoes }`.
**Response:** `{ contrato_id }`.
**Eventos:** `Marketplace.AssinouRecorrente`.
**US:** US-MKT-006.

### `POST /v1/area-cliente/pagamento/{orcamento_id}/iniciar`
**Propósito:** inicia checkout de pagamento.
**Response:** `{ redirect_url, gateway, expira_em }`.
**US:** US-MKT-008.

### `GET /v1/area-cliente/certificados`
**Propósito:** lista certificados emitidos do cliente.

---

## Endpoints administrativos (curadoria)

### `GET /v1/admin/vitrine/itens`
**Propósito:** lista itens (incluindo inativos).

### `PATCH /v1/admin/vitrine/itens/{id}`
**Propósito:** edita item da vitrine (destaque, ordem, descrição, ativo).
**Request:** `{ destaque?, ordem?, descricao_marketing?, ativo? }`.
**US:** US-MKT-005.

### `GET /v1/admin/funil`
**Propósito:** dashboard de funil.
**Query:** `de`, `ate`, `utm_source?`.
**Response:** etapas + taxas + valores.
**US:** US-MKT-007.

---

## Webhooks (entrada — recebidos)

### `POST /v1/webhooks/pagamento/{gateway}`
**Propósito:** confirmação de pagamento pelo gateway.
**Auth:** HMAC do gateway.
**Eventos:** `Marketplace.PagamentoConfirmado`.

---

## Eventos consumidos

Ver `../modelo-de-dominio.md` (seção "Eventos consumidos") + `../../../comum/integracoes-inter-modulos.md`.

## Rate limits

- Vitrine pública (GET): 60 req/min/IP.
- Criar carrinho: 10 req/min/IP.
- Enviar solicitação: 5 req/hora/IP + CAPTCHA.
- Área do cliente: 120 req/min/usuário.

## Versionamento

- v1 e v2 coexistem por 6 meses.
- Quebra de contrato exige ADR.

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US.
- Quebra → ADR + janela.
- Endpoint descontinuado → `@deprecated` + Sunset header.
