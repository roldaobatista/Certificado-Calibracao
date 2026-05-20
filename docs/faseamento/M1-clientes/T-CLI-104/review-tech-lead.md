---
owner: tech-lead-saas-regulado
revisado-em: 2026-05-20
status: stable
---

# Review tech-lead — T-CLI-104

Veredito: **AJUSTAR antes de `/implement`**.

## Crítico (bloqueia merge)

- **T2 — UPSERT no MESMO atomic perde contagem em rollback do
  request.** Caller fail-loud relança exceção → Django rollback →
  contador volta zerado. **Resultado: breaker cego nas falhas que
  ele existe pra contar.** Correção: **conexão paralela autocommit
  `breaker_writer`** (alias separado).

## Altos

- **T3 — bucket fixo 5min subestima borda.** Falha no segundo 4:59
  + zera no 5:00 = alerta passa. **Trocar pra tabela de eventos
  crus `(tenant_id, ts, ok)` + sliding window `now() - interval '5
  min'`**.
- **C2 — 0.1% nunca atinge em dogfooding (≤100/dia).** **OR lógico
  obrigatório**: `(pct ≥ 0.1% AND total ≥ 1000) OR (falhas ≥ 3 em
  5min)`.

## Médios

- **T5 — nome quebra padrão slug.** Usar
  `sistema.breaker_acesso_pii.disparado` + `.normalizado`.
- **design.md:99 — gravar `ok` na cadeia F-A é gargalo** (hash chain
  serial por tenant). Tabela de eventos crus separada resolve.
- **T4 — idempotência do command:** chave `(tenant_id, janela)` no
  `causation_id` → UNIQUE no `bus_outbox` dedup.

## Testes adicionais

- Drill de rollback do request (golden T2).
- Drill de concorrência 50t × 100r = 15000 sem perda.

## Limites honestos

Race condition de connection pool com autocommit em carga 50+
tenants só drill cronometrado em F-C revela. Pré-1º tenant pago,
pentest externo.
