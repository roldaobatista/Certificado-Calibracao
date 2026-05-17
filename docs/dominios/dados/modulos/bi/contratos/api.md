---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/dominios/dados/modulos/bi/modelo-de-dominio.md
---

# Contratos de API — Módulo BI

> Endpoints / IPC. Formato (REST / GraphQL) a definir em ADR-0001.

---

## Convenções

- Versionamento via path (`/v1/`) — confirma em ADR.
- Autenticação: header `Authorization: Bearer <token>`.
- Tenant: identificado por token + header `X-Tenant-ID`. `INV-TENANT-001` exige presença em toda query (validador no middleware).
- Erros: RFC 7807 (Problem Details).
- Idempotência: mutações aceitam `Idempotency-Key`.

---

## Endpoints

### `GET /v1/bi/dashboards`
**Propósito:** lista dashboards visíveis para o usuário/papel.
**RBAC:** qualquer papel autenticado (filtrado por RBAC do dashboard).
**Response:** lista de `{ id, nome, area, dono_papel, atualizado_em }`.
**Códigos:** 200, 401, 403.
**Invariantes:** `INV-TENANT-001..004`.
**US:** US-BI-001, US-BI-002.

---

### `GET /v1/bi/dashboards/{id}`
**Propósito:** detalhe do dashboard + widgets resolvidos com dados.
**Response:** `{ id, nome, widgets: [...] }` onde cada widget já vem com `valor_calculado` + `defasagem_segundos`.
**Códigos:** 200, 401, 403, 404.

---

### `POST /v1/bi/dashboards`
**Propósito:** criar dashboard.
**RBAC:** `analista` ou `admin`.
**Request:** `{ nome, area, layout, dono_papel }`.
**Códigos:** 201, 400, 401, 403, 422.
**US:** US-BI-014 (parcial).

---

### `GET /v1/bi/kpis/{codigo}`
**Propósito:** valor atual de um KPI.
**Query params:** `periodo_inicio`, `periodo_fim`, `granularidade`, `filtros[]`.
**Response:** `{ codigo, valor, unidade, target, defasagem_segundos, serie_temporal: [...] }`.
**Códigos:** 200, 401, 403, 404, 422.
**US:** todas (cada KPI exposto pela API).

---

### `GET /v1/bi/kpis/{codigo}/drill-down`
**Propósito:** detalhe que compõe o KPI (lista subjacente).
**Query params:** `periodo_*`, `filtros[]`, `paginacao`.
**Response:** `{ total, itens: [...] }` com dados granulares.
**US:** US-BI-001 (AC-3).

---

### `POST /v1/bi/relatorios`
**Propósito:** criar relatório customizado.
**RBAC:** `analista`.
**Request:** `{ nome, definicao: { metricas: [...], filtros: [...], agrupamentos: [...] } }`.
**Response:** `{ id, ... }`.
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** definição validada contra catálogo permitido para o papel; `INV-TENANT-001..004`.
**US:** US-BI-014.

---

### `POST /v1/bi/relatorios/{id}/executar`
**Propósito:** executar relatório agora.
**Request:** `{ formato: "json" | "csv" | "xlsx" | "pdf" }`.
**Response:** se `json` → dados inline; senão → URL temporária no storage (B2) + tempo de expiração.
**Códigos:** 200, 401, 403, 404, 413 (resultado muito grande).
**Eventos:** dispara `BI.RelatorioGerado` se formato não-json.
**US:** US-BI-014.

---

### `POST /v1/bi/agendamentos`
**Propósito:** agendar envio de relatório/dashboard.
**Request:** `{ relatorio_id OR dashboard_id, cron, destinatarios: [...], formato, risco_lgpd_aceito_para_externos: bool }`.
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** destinatário externo (não-usuário do tenant) exige flag `risco_lgpd_aceito = true`.
**US:** US-BI-015.

---

### `DELETE /v1/bi/agendamentos/{id}`
**Propósito:** revogar agendamento.
**RBAC:** dono do agendamento ou admin.
**Códigos:** 204, 401, 403, 404.

---

### `POST /v1/bi/links-publicos`
**Propósito:** gerar link público para dashboard.
**RBAC:** `analista` ou `admin`.
**Request:** `{ dashboard_id, expira_em, escopo_dados: "agregado" | "cliente_especifico", cliente_alvo_id?, senha?, restricao_ip? }`.
**Response:** `{ id, token, url_publica, qrcode_base64 }`.
**Códigos:** 201, 400, 401, 403, 422.
**Invariantes:** `INV-TENANT-001..004`; escopo + expiração OBRIGATÓRIOS.
**Eventos:** dispara `Auditoria.LinkPublicoCriado` (módulo Auditoria).
**US:** US-BI-016.

---

### `DELETE /v1/bi/links-publicos/{id}`
**Propósito:** revogar link público.
**RBAC:** dono ou admin.
**Códigos:** 204.
**Efeito:** link expira imediatamente.

---

### `GET /publico/bi/{token}` (rota pública, **não-versionada**, **sem `/v1`**)
**Propósito:** acessar dashboard via link público.
**Autenticação:** opcional (token + senha se configurada).
**Response:** HTML/JSON do dashboard filtrado pelo escopo.
**Códigos:** 200, 401 (senha errada), 410 (expirado), 429 (rate limit).
**Invariantes:** `INV-TENANT-*` (nunca cruza tenants), rate limit por IP.
**Rate limit:** 30 req/min por IP; após 5 tentativas de senha errada → bloqueio 1h.
**Eventos:** dispara `BI.LinkPublicoAcessado` a cada hit.

---

## Eventos consumidos de outros módulos

Ver `../../../comum/integracoes-inter-modulos.md`. Resumo:
- `Financeiro.LancamentoCriado` → atualiza data marts financeiros.
- `OS.Concluida` → atualiza produtividade técnica + SLA.
- `Comercial.OrcamentoAprovado` → atualiza funil.
- `Estoque.MovimentacaoRegistrada` → atualiza indicadores estoque.
- `Calibracao.CertificadoEmitido` → atualiza indicadores laboratório.

## Rate limits

- `GET /v1/bi/kpis/*` — 60 req/min/tenant.
- `POST /v1/bi/relatorios/*/executar` — 10 req/min/usuário (relatórios pesados).
- `GET /publico/bi/{token}` — 30 req/min/IP.
- Default: 120 req/min/tenant.

## Versionamento

- v1, v2 coexistem por 6 meses.
- Quebra de contrato → ADR + bump CHANGELOG + Sunset header (RFC 8594).

## Como esta lista evolui

- Endpoint novo → adicionar + linkar US-BI-*.
- Quebra → ADR + janela migração.
- Endpoint deprecado → `@deprecated` + Sunset header.
