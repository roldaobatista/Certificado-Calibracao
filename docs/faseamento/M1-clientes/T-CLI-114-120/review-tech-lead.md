---
owner: tech-lead-saas-regulado
revisado-em: 2026-05-20
status: stable
---

# Review tech-lead — US-CLI-006 (T-CLI-114..120)

Veredito: **AJUSTAR + APROVA INCREMENTAL** — destrava T-CLI-115/118/120; bloqueia T-CLI-114/117 até correções.

## T1..T6

- **T1** 8 endpoints REST — APROVA. Cada `tipo` tem authz/SLA/payload distinto.
- **T2** sanitizar `payload_resposta` — **REJEITA**. Sanitizar payload de `acesso` art. 18 II esvazia retorno legítimo. **2 campos**: `payload_resposta_titular` (PII pro titular; cifrado KMS Wave A — Marco 1 deixa JSONB com TTL 30d) + `payload_auditoria` (sanitizado).
- **T3** UNIQUE — date-bucket bloqueia 2º pedido legítimo do mesmo titular. Trocar por UNIQUE `(causation_id)` global. Anti-abuse via rate-limit (Wave A).
- **T4** signal `post_save` — frágil (`.update()`, `bulk_update`, raw SQL bypassam). Usar **trigger PG `AFTER INSERT/UPDATE ON cliente`** pra escrever `OperacaoTratamentoCliente`.
- **T5** outbox sempre publica revogação (consumer noop em Marco 1) — valida contrato pré-Wave A.
- **T6** `_tem_nf_emitida` retorna False + comentário GATE-CLI-M2 (registrado em `faseamento-foundation-waves.md`).

## BLOQs adicionais

- **BLOQ-TL-1**: validador idade em CREATE+UPDATE + CHECK constraint PG (`data_nascimento IS NULL OR data_nascimento <= now() - interval '18 years'`).
- **BLOQ-TL-2**: denylist PII sensível — concorda com A1 advogado. Word-boundary `\b` + termos ≥5 chars + lista enxuta.
- **BLOQ-TL-3**: anti-corrosion — `_tem_nf_emitida` via porta `NFGateway` (stub em Marco 1 retorna False).

## Limites honestos

Não consigo validar sem rodar: N+1 do signal em importação CSV; race UNIQUE causation_id com outbox idempotency; bypass Unicode no termset PII. Drill 50×1000 igual FA-A5 pré-1º tenant pago.
