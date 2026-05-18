---
owner: roldao
revisado_em: 2026-05-18
proximo_review: 2026-08-18
status: stable
diataxis: explanation
audiencia: agente
lente: 9-performance-banco
auditor: general-purpose (lente DBA/performance PostgreSQL)
veredito: DÉBITO DE PERFORMANCE
---

# AUDIT-09 — Performance / Banco / Migrations / Índices / Triggers PG

> Lente 9 de 10.

## VEREDITO

**DÉBITO DE PERFORMANCE** — base de schema/índices boa e replicável, mas 2 débitos ALTA que doem com escala e que o equipamentos copia cego se não corrigidos: (1) N+1 dentro de transação SERIALIZABLE no bulk_upsert, (2) timeline visão-360 via payload_jsonb__cliente_id que ignora o índice expressional existente.

## O que está bom (manter e replicar)

- RLS sargable: policies com current_setting (STABLE), todo índice de filtro começa por tenant_id.
- UNIQUE parcial em soft-delete (uq_cliente_doc_ativo WHERE deletado_em IS NULL) + manager default alinhado.
- db_index em deletado_em/desbloqueado_em.
- Triggers anti-mutation PL/pgSQL mínimo, BEFORE, custo desprezível.
- Índice expressional para timeline existe (ix_audit_payload_cliente_id).
- Retry com backoff em SerializationFailure; update() em vez de save() pra evitar trigger.

## Débitos

| ID | Descrição | Gravidade | Arquivo:linha | Impacto escala | Replicar? | Conserto |
|---|---|---|---|---|---|---|
| P1 | bulk_upsert faz 1 query/linha pra detectar soft-deleted (loop all_objects.filter().first()) dentro de SERIALIZABLE. | ALTA | repositories.py:220-244 | 1000 linhas = 1000 round-trips serializados segurando lock; import 30-60s + contention | NÃO copiar | 1 query agregada + checagem em set na memória. |
| P2 | Timeline visão-360 usa payload_jsonb__cliente_id (operador ->, containment), não ->> — não casa o índice expressional. | ALTA | views.py:596-602 vs audit/0005:75-77 | auditoria crescendo = seq scan filtrado por tenant a cada visão-360 | SIM (perigoso) | KeyTextTransform/RawSQL emitindo ->> = %s; validar com EXPLAIN. |
| P3 | bulk_create sem batch_size. | MÉDIA | repositories.py:343 | até 1000 num INSERT; frágil se limite subir | SIM (ajustar) | batch_size=500. |
| P4 | Tenant.objects.filter(id=active).get() repetido em toda escrita. | BAIXA | views.py:165,386,804 | +1 query/request multiplicado | SIM (padrão) | Cachear tenant no request/middleware. |
| P5 | Listagem sem paginação custom nem .only(); DRF default faz COUNT(*) por página. | BAIXA | views.py:116-120 | COUNT(*) com RLS é O(n); +30 colunas/linha | SIM | PageNumberPagination + .only(); CursorPagination se crescer. |
| P6 | auditoria append-only sem particionamento. | MÉDIA (futuro) | audit/0001 | tabela que mais cresce; índices incham, VACUUM degrada em 12-24 meses | decisão Foundation, não copiar por módulo | Particionamento declarativo por timestamp (range mensal) antes do 1º tenant com volume. |

Sem ID: migrations 0005/0012 AddField nullable — não travam. CREATE INDEX sem CONCURRENTLY aceitável hoje (tabela vazia) MAS equipamentos deve usar CONCURRENTLY se índice em tabela populada. select_for_update corretamente dentro de atomic.

## Recomendação final

Antes de equipamentos copiar migrations/repositories, corrigir P1 e P2 no próprio clientes (bugs reais, não cosméticos): P1 reescrever detecção soft-deleted em 1 query; P2 alinhar lookup ao índice expressional + EXPLAIN ANALYZE. P3/P4/P5 no mesmo lote (viram template). P6 escalar como decisão de Foundation (particionamento de auditoria). RLS + índices tenant-first + UNIQUE parcial sólidos — replicar. Risco concentrado em importação em lote + timeline JSONB — exatamente o que equipamentos herda.
