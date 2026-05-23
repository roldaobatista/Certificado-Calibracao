---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
modulo: webhook-out
dominio: suporte-plataforma
relacionados:
  - docs/adr/0054-webhook-out-provider.md
  - docs/arquitetura/anti-corrosion-layer.md
---

# PRD — Módulo Webhook Out (Saída de eventos para sistemas externos do tenant)

> Permite que cada tenant assine eventos do Aferê e receba via HTTP POST em URL própria (Zapier, Make, n8n, sistema interno). **PRÉ-REQUISITO Wave A** — Balanças Solution (dogfooding) já demanda integração.

## 1. O que este módulo é

Camada de **saída controlada do bus interno** (procrastinate + outbox v10). Tenant configura endpoint (URL + secret HMAC), seleciona subset de eventos do catálogo, e Aferê entrega POST assinado com retry exponencial, dead letter e circuit breaker — tudo via porta `OutboundWebhookProvider` (#19 ACL, ADR-0054).

## 2. Por que existe

Sem webhook saída, tenant que quer integrar (notificar Slack quando NC abrir, criar tarefa no Asana quando OS criar, gravar BigQuery quando certificado emitir) precisa fazer **polling** da API REST — alto custo, alta latência, perde eventos. Webhook é padrão de mercado SaaS B2B.

## 3. Personas

- **P-WH-01 Admin tenant** — configura endpoint, lê estatísticas.
- **P-WH-02 Operador Aferê** — investiga dead letter, ajusta rate limit.

## 4. Escopo

- Cadastro de endpoint (URL HTTPS, secret HMAC, lista de eventos assinados, rate limit, ativo/inativo).
- Entrega POST com headers `X-Afere-Signature` (HMAC sha256), `X-Afere-Idempotency-Key`, `X-Afere-Event-Type`, `X-Afere-Tenant-Id`.
- Retry exponencial 1m/5m/30m/2h/12h (5 tentativas).
- Dead letter PG por tenant; UI lista falhas e permite reentrega manual.
- Circuit breaker por endpoint (5 falhas seguidas em 10min abre; fechado após 30min ok).
- Rotação de secret (Aferê gera novo; tenant tem 7 dias pra trocar; sistema aceita ambos no período).
- Painel: % entrega, latência média p95, falhas últimas 24h.

## 5. Non-goals

- **Webhook IN** (Aferê recebendo eventos externos) — fica em `integracoes-externas`.
- **Transformação de payload custom por tenant** (ANTI-11) — payload é o envelope v10 canônico.
- **OAuth out / token bearer** — só HMAC; OAuth out vai pra `integracoes-externas` Wave B.
- **Fan-out massivo** (>1000 endpoints por tenant) — V2/V3.

## 6. User Stories

### US-WH-001: Tenant cadastra endpoint

**Como** admin tenant, **quero** cadastrar URL + secret HMAC + lista de eventos, **para** receber notificação no meu sistema externo.

- **AC-WH-001-1**: GIVEN admin autenticado, WHEN abre "Webhooks Out > Novo", THEN preenche URL (HTTPS obrigatório), seleciona eventos (multi-select do catálogo v10), gera secret (clique no botão; Aferê devolve uma vez).
- **AC-WH-001-2**: GIVEN URL aponta pra IP privado RFC 1918 ou metadata cloud (169.254.169.254), WHEN salva, THEN sistema rejeita (mitigação SSRF — INV-WEBHOOK-001).
- **AC-WH-001-3**: GIVEN endpoint salvo, WHEN próximo evento do tipo assinado ocorrer, THEN sistema entrega POST.

### US-WH-002: Entrega assinada + retry

**Como** sistema, **quero** entregar com HMAC sha256, retry exponencial e dead letter, **para** garantir entrega resiliente.

- **AC-WH-002-1**: GIVEN evento publicado no bus E endpoint assinou, WHEN entrega dispara, THEN POST com header `X-Afere-Signature: sha256=<HMAC(secret, body)>` + `X-Afere-Idempotency-Key`.
- **AC-WH-002-2**: GIVEN endpoint retorna 2xx em 10s, WHEN sucesso, THEN grava `Webhook.Entregue`.
- **AC-WH-002-3**: GIVEN endpoint retorna não-2xx ou timeout, WHEN falha, THEN agenda retry 1m → 5m → 30m → 2h → 12h; após 5 falhas → dead letter + `Webhook.DeadLettered`.
- **AC-WH-002-4 (circuito)**: GIVEN 5 falhas seguidas em 10min, WHEN sistema detecta, THEN circuito abre (`Webhook.CircuitoAberto`); novas entregas pausam 30min; após 30min faz half-open com 1 tentativa.

**Invariantes:** `INV-WEBHOOK-001`, `INV-TENANT-001`.

### US-WH-003: Painel de entregas + reentrega manual

**Como** admin tenant, **quero** ver últimas 24h de entregas + reentregar falhas, **para** debugar integração quebrada.

- **AC-WH-003-1**: painel mostra tabela: evento, status, tentativas, último erro, latência.
- **AC-WH-003-2**: GIVEN entrega em dead letter, WHEN clico "Reentregar", THEN sistema cria nova tentativa preservando payload original.

### US-WH-004: Rotação de secret

**Como** admin tenant, **quero** rotacionar secret HMAC sem indisponibilidade, **para** girar credenciais periodicamente.

- **AC-WH-004-1**: GIVEN rotação iniciada, WHEN Aferê gera novo, THEN sistema aceita ambos por 7 dias; depois desativa antigo automaticamente.

## 7. Métricas

- % entrega bem-sucedida (200/204) > 99%.
- p95 latência entrega < 500ms (excluindo retry).
- Dead letter < 0,1% das entregas.

## 8. NFR

- **Performance:** entrega assíncrona (não bloqueia produtor); p95 < 500ms; throughput 10k events/min por instância.
- **Segurança:** TLS obrigatório; HMAC sha256; SSRF guards (RFC 1918 + 169.254.x.x + 127.0.0.0/8 negados); rate limit 60 req/min/tenant (configurável).
- **Disponibilidade:** SLO 99,9% (latência) — falhas não derrubam produtor.
- **Idempotência:** chave `idempotency_key` permite consumer detectar replay.

## 9. Glossário

Termos canônicos em `docs/glossario.md`.

## 10. Como evolui

- Evento novo no catálogo v10 → automaticamente disponível pra assinatura (sem release).
- Layout do envelope v10 muda → versionamento `X-Afere-Schema-Version`.
- Bug security (SSRF/replay) → patch imediato + ADR.
