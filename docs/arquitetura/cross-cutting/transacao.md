---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — transação

> **Pra quê:** sem boundary explícito, transação fica longa e vaza lock; ou curta demais e perde atomicidade.

---

## Princípio

**Transação dura o mínimo necessário** pra manter consistência da regra de negócio.

```
abre → faz mudanças no banco → fecha (commit/rollback)
```

Nunca: abrir transação que inclui chamada HTTP externa, espera de usuário, lock cross-tenant.

---

## Isolation level padrão

`READ COMMITTED` (default Postgres) na maioria.

`REPEATABLE READ` em:
- Cálculo financeiro que depende de múltiplas tabelas (fechar lançamento + atualizar saldo)
- Numeração sequencial (próximo certificado)

`SERIALIZABLE` em casos extremos:
- Operações financeiras críticas
- Conciliação bancária

---

## Boundary

| Local | Boundary |
|-------|----------|
| Django view simples | Decorator `@transaction.atomic` no view |
| Use case multi-step | Manager do use case abre + commita |
| Job Celery | Cada job tem sua transação curta; chunks grandes dividem em sub-jobs |
| Migration | DRF migrations rodam em transação (default Django) |
| Webhook receiver | Transação curta por evento; idempotency check antes |

---

## Antipatterns proibidos

```python
# ❌ ruim — transação inclui chamada HTTP
with transaction.atomic():
    pedido = Pedido.objects.create(...)
    response = requests.post("https://plugnotas/emit", ...)  # ← BAD
    pedido.nfse_id = response.json()["id"]
    pedido.save()
```

```python
# ✅ bom — transação curta + idempotência
pedido = Pedido.objects.create(...)
# fora da transação
response = call_plugnotas_idempotent(pedido.id, ...)
with transaction.atomic():
    pedido.nfse_id = response["id"]
    pedido.save()
```

---

## Lock pessimista quando necessário

```python
with transaction.atomic():
    pedido = Pedido.objects.select_for_update().get(pk=id)
    # mudanças aqui ficam atômicas
    pedido.status = "PAGO"
    pedido.save()
```

Atenção: `select_for_update` segura lock até commit; se transação inclui chamada externa, lock pode durar muito.

---

## Multi-tenant + transação

RLS é aplicada **dentro** da transação. Middleware Django seta `app.tenant_id` no início do request via `SET LOCAL app.tenant_id = ...`. Esse `SET LOCAL` vale só pela transação corrente.

Conexão reusada por outro tenant subsequente precisa resetar tenant_id (ver `isolamento-multi-tenant.md`).

---

## Hooks / verificação

Auditor Segurança verifica:
- Transação contendo `requests.get/post/...` → CONCERN ou FAIL
- `transaction.atomic` aninhado profundo → CONCERN (Savepoints OK; manter ≤ 2 níveis)
- Migration que abre lock longa em tabela com dados → CONCERN

---

## Referências

- `idempotencia.md`
- `isolamento-multi-tenant.md`
- `retry.md`
- PostgreSQL docs: transaction isolation
