---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — timeout

> **Pra quê:** sem timeout explícito, request pode pendurar pra sempre + recurso vaza. "Timeout default da lib" varia e é unreliable.

---

## Princípio

**Toda chamada externa tem timeout explícito.** Sem exceção.

```python
# ❌ ruim
response = requests.get(url)

# ✅ bom
response = requests.get(url, timeout=(connect_timeout, read_timeout))
```

---

## Tabela de timeouts padrão

| Tipo de chamada | Connect | Read | Total |
|-----------------|---------|------|-------|
| Chamada interna (DB, Redis) | — | 5s | 5s |
| HTTP a parceiro normal | 3s | 10s | 13s |
| HTTP a parceiro lento (PlugNotas, gateway) | 5s | 30s | 35s |
| WhatsApp BSP | 5s | 30s | 35s |
| KMS encrypt/decrypt | 2s | 5s | 7s |
| LLM gateway (síncrono) | 5s | 60s | 65s |
| LLM gateway (job async) | 5s | 300s | 305s |
| Job Celery worker total | — | 600s | 600s |

---

## Timeout em request HTTP do usuário

Total: **30s** máximo end-to-end (usuário desiste depois disso).

Se operação > 30s, **converter pra async**: retornar 202 + job ID + polling/webhook.

Exemplo: emissão de NFS-e pode demorar 1-3 min → endpoint retorna 202 imediatamente + cliente faz polling em `/jobs/<id>` ou recebe webhook.

---

## Propagação de timeout

```
Usuario → API (30s budget)
   ↓ (3s gasto)
API → DB (5s timeout, sobra 27s)
   ↓ (1s gasto)
API → PlugNotas (35s timeout — não cabe; usa 25s)
```

Quando budget esgotar, request cancela explicitamente (não deixa pendurando).

---

## Cancelamento

Quando timeout dispara:
- Conexão fechada
- Recurso liberado (connection pool, lock)
- Audit log com `event: <operacao>.timeout`
- Erro classificado como `InfrastructureError` (retryable)

---

## Hooks / verificação

Auditor Qualidade detecta em pre-commit:
- `requests.get/.post/etc()` sem `timeout=` → FAIL
- `httpx.get/.post()` sem timeout → FAIL
- `socket.connect()` sem timeout → CONCERN

---

## Referências

- `retry.md` (timeout dispara retry)
- `erro.md` (timeout vira InfrastructureError)
- `observabilidade.md` (alerta latência p99 > 3x baseline)
