---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: proposta
diataxis: explanation
audiencia: agente
relacionados:
  - docs/arquitetura/anti-corrosion-layer.md
  - docs/dominios/suporte-plataforma/modulos/webhook-out/prd.md
  - docs/adr/0005-engine-automacoes.md
---

# ADR-0054 — `OutboundWebhookProvider` (19ª porta ACL) + módulo `webhook-out`

> **Status:** proposta. **PRÉ-REQUISITO Wave A** — Roldão vai pedir webhook saída no dogfooding Balanças Solution (integrar com automações próprias dele). Resolve achado **G-INT-4**.
> **Decisor:** Roldão.
> **Bloqueia:** integração de qualquer tenant com sistema externo (Zapier, Make, n8n, webhook próprio).

---

## Glossário

| Termo | Tradução |
|---|---|
| **Webhook out** | Aferê "chama de volta" um endereço web do cliente quando algo acontece (OS criada, certificado emitido). |
| **HMAC** | "Assinatura" que prova que a mensagem veio do Aferê, não de um impostor. |
| **Dead letter** | "Fila de envelopes que não conseguiram entregar"; operador inspeciona depois. |

---

## Contexto

Bus de eventos Aferê hoje é interno (procrastinate + outbox). Tenant que quer integrar com Zapier/Make/n8n/sistema próprio não tem como — precisa do Aferê enviar HTTP POST para URL dele quando evento ocorre. Sem porta + módulo, agente IA inventaria implementação direta com `requests.post()` em domínio (proibido pela ACL).

## Decisão

### 1. Porta nova `OutboundWebhookProvider` (19ª da ACL)

```python
class OutboundWebhookProvider(Protocol):
    def entregar(
        self,
        tenant_id: TenantId,
        endpoint_id: UUID,           # config do tenant: url + secret
        evento: EventoEnvelope,      # mesmo envelope v10 do bus interno
        idempotency_key: str,
    ) -> EntregaResult: ...

    def listar_falhas(self, tenant_id: TenantId) -> list[FalhaEntrega]: ...
    def reentregar(self, entrega_id: UUID) -> EntregaResult: ...
```

Implementações: `HttpxOutboundWebhookProvider` (1ª, retry exponencial, dead letter PG), `MockOutboundWebhookProvider` (testes).

### 2. Módulo `webhook-out` (PRD novo)

Tenant configura endpoints via UI:
- URL HTTPS (obrigatório TLS, hostname público)
- Secret HMAC (Aferê gera; tenant copia; rotacionável)
- Eventos assinados (subset do catálogo v10)
- Rate limit por tenant (default 60 req/min; ajustável)

### INV-WEBHOOK-001

**Toda entrega tem (a) header `X-Afere-Signature: sha256=<HMAC(secret, body)>`; (b) header `X-Afere-Idempotency-Key`; (c) timeout 10s; (d) retry exponencial 1m/5m/30m/2h/12h (5 tentativas); (e) dead letter após 5 falhas; (f) circuit breaker por endpoint (5 falhas seguidas em 10min abre, fechado após 30min ok).** Veredito: ALTO. Hook bloqueia código que envie webhook sem assinatura HMAC.

### Eventos emitidos pelo módulo

- `Webhook.Entregue` / `Webhook.Falhou` / `Webhook.CircuitoAberto` / `Webhook.DeadLettered`

## Alternativas rejeitadas

1. **Não oferecer webhook; cliente usa API REST** — exige cliente fazer polling, custo + latência altos.
2. **Webhook direto sem porta** — quebra ACL; agente IA copia padrão em qualquer módulo.
3. **Usar serviço externo (Svix/Hookdeck)** — lock-in + LGPD (dado pessoal sai do BR).

## Consequências

**Positivas:** desbloqueia integração Zapier/Make/n8n; Roldão usa direto em Balanças Solution dogfooding.
**Negativas:** manter retry/dead letter/circuito é manutenção contínua; SSRF risk (URL de tenant pode apontar pra IP interno) — mitigação: allowlist de schemes, denylist RFC 1918 + metadata.

## Referências

- ACL porta #19 (este ADR cria)
- RFC 1918 (IPs privados a bloquear)
- Padrão Stripe Webhooks (HMAC sha256, idempotency-key)
