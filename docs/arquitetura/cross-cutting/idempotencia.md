---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — idempotência

> **Pra quê:** retry seguro depende de idempotência. Sem isso, NF-e duplicada + cobrança em dobro + certificado triplo. Em vendor regulado, idempotência é não-negociável.

---

## Princípio

> **Mesma chave de idempotência + mesma operação = mesmo resultado**, mesmo se chamada 10x.

---

## Quando é obrigatório

- Toda chamada que modifica estado em parceiro externo (NF-e, gateway pagamento, e-mail transacional, WhatsApp)
- Todo job Celery / procrastinate
- Toda emissão de certificado
- Toda criação de OS
- Todo registro fiscal
- Webhook receiver (parceiro pode entregar 2x)

---

## Mecanismo padrão

1. **Cliente gera UUID** (chave idempotente) **uma vez** — antes da 1ª tentativa
2. **Envia chave em header** (`Idempotency-Key: <uuid>`) ou no body (`idempotency_key: <uuid>`)
3. **Servidor verifica:**
   - Se chave já processada com sucesso → retorna resultado em cache (200/201 com mesmo body)
   - Se chave já processada com erro permanente → retorna mesmo erro
   - Se chave em processo → 409 Conflict ou aguarda (configurável)
   - Se chave nova → processa, salva resultado em cache por N dias (24h-30d dependendo do caso)
4. **Cache da resposta** indexada pela chave + endpoint + hash do body

---

## TTL do cache de idempotência

| Operação | TTL |
|----------|-----|
| Emitir NF-e | 30 dias |
| Emitir certificado | 30 dias |
| Job Celery | 24h |
| Webhook receiver | 7 dias |
| Login | 5 min |

---

## Implementação Django

```python
# decorator
@idempotent(ttl_days=30)
def emit_certificate(tenant, payload, idempotency_key):
    # cria certificado; retorna resultado
    ...
```

Decorator salva em `idempotency_cache` (tabela ou Redis) com:
- `tenant_id + endpoint + idempotency_key` como índice composto
- `request_body_hash` (pra detectar reuso de chave com body diferente — erro de cliente)
- `response_status + response_body` (pra replay)
- `expires_at`

---

## Casos especiais

| Cenário | Tratamento |
|---------|------------|
| Cliente reusa chave com body diferente | 400 + "Chave idempotente já usada com payload diferente" |
| Servidor cai depois de processar mas antes de salvar cache | Próxima tentativa reprocessa — operação subjacente precisa ser idempotente nativamente (ex: NF-e tem chave própria que SEFAZ rejeita duplicado) |
| Cache expira antes do cliente desistir | Operação subjacente decide; SEFAZ rejeita duplicada (chave única na NFe ID) |

---

## Operações sem idempotência nativa

Alguns parceiros não suportam idempotência. Mitigações:
- **Locks pessimistas** (`SELECT ... FOR UPDATE`)
- **Verificar antes de criar** (e.g., antes de criar OS, consultar se já existe `idempotency_key` na tabela)
- **Pattern saga** com compensação (não cobrir aqui)

---

## Hooks / verificação

Auditor Qualidade verifica em pre-commit:
- Função decorada `@retryable` sem decorator `@idempotent` → FAIL
- Endpoint POST/PUT/PATCH sem cabeçalho `Idempotency-Key` documentado → CONCERN
- Job procrastinate sem chave idempotente → FAIL

---

## Referências

- `retry.md`
- `transacao.md`
- ADR-0008 (fiscal — chave NFe é idempotência nativa do parceiro)
