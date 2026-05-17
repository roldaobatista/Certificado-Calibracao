---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — retry

> **Pra quê:** sem política de retry, falha transiente vira erro permanente; ou retry agressivo derruba parceiro.

---

## Quando retry

✅ Erro **transiente**:
- Timeout de rede / DNS
- 502/503/504 do parceiro
- Connection reset
- Lock momentâneo de banco

❌ NÃO retry:
- 400/401/403/404/422 (cliente errou)
- 500 com mensagem clara de bug do parceiro
- `DomainError` (regra de negócio)
- Token expirado (faz refresh, não retry direto)

---

## Política padrão — exponential backoff com jitter

```python
attempts = 0
max_attempts = 5
base = 1.0  # segundo
max_delay = 60.0
while attempts < max_attempts:
    try:
        result = call_external()
        break
    except TransientError:
        attempts += 1
        delay = min(base * (2 ** attempts), max_delay)
        delay += random.uniform(0, delay * 0.1)  # jitter 10%
        sleep(delay)
else:
    # esgotado — vai pra dead letter
    raise MaxRetriesExceeded(...)
```

Tempo total máximo: ~2 min (1+2+4+8+16+32 = 63s com jitter).

---

## Variações

| Cenário | max_attempts | base | max_delay |
|---------|--------------|------|-----------|
| Chamada síncrona em request HTTP | 2 | 0.5 | 2 | (usuário esperando — não pode demorar) |
| Job Celery / procrastinate | 5 | 1 | 60 |
| Fiscal (PlugNotas/Focus) — NF-e | 3 (mas com fallback de provider) | 5 | 30 |
| WhatsApp BSP | 5 | 2 | 120 |
| KMS | 3 | 1 | 10 |

---

## Dead letter

Após esgotar:
- Job vai pra fila `failed_<queue>`
- Audit log com SEV-2
- Roldão notificado se pattern repete (3+ falhas mesmo job em 24h)
- Operador pode reprocessar manualmente após investigar

---

## Idempotência obrigatória

Retry seguro requer idempotência. Ver `idempotencia.md` — toda função retryável tem `chave_idempotente` (UUID gerado uma vez, reusado em retry).

---

## Circuit breaker

Se taxa de erro em parceiro > 50% nos últimos 60s → **circuit open** por 5 min. Requests novos falham rápido (`ServiceTemporarilyUnavailable`) sem tentar.

Após 5 min: meio-aberto (1 request de teste). Se sucesso, fecha; se erro, reabre.

Implementação: usar `pybreaker` ou similar quando código existir.

---

## Hooks / verificação

Auditor Qualidade verifica:
- Função chamando API externa sem `@retryable` decorator → CONCERN
- Retry sem max_attempts → FAIL
- `time.sleep()` em código de produção (não-teste) sem comentário → CONCERN

---

## Referências

- `erro.md` (categorias de erro)
- `idempotencia.md`
- `timeout.md`
- `observabilidade.md` (alertas de circuit breaker open)
