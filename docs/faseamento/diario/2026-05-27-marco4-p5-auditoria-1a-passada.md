---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-06-27
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: diario-de-sessao
relacionados:
  - .agent/CURRENT.md
  - docs/faseamento/M4-calibracao/auditoria-familia5.md
  - docs/faseamento/diario/2026-05-26-marco4-p4-fases5-10.md
---

# 2026-05-27 — Marco 4 P5 1ª passada Família 5

## Sessão autônoma (em curso)

4 commits sequenciais + 1ª passada formal dos 10 auditores Família 5:

| Commit | Conteúdo |
|---|---|
| `174a828` | Fase 6 FECHADA — 5 query services puros (orcamento + historico + escopo + proficiencia + subcontratacao); +44 tests |
| `060810c` | Fase 10 Batch X — 11 tests regressão INV-CAL-INC-004/RT-002/IDEMP-001 |
| `83b9945` | `docs/faseamento/M4-calibracao/auditoria-familia5.md` DRAFT — autoavaliação preliminar |
| `1607b40` | Fase 10 Batch Y — 8 tests regressão INV-CAL-CONF-001/DEC-001 + sweep tasks.md drift |

**Suite M4:** 563 → 629 tests (+66 esta sessão). **Hooks:** 377/377.

## 1ª passada Família 5 (2026-05-27 — 10 auditores em paralelo)

| Lente | Veredito | C | A | M | B/CONCERN |
|---|---|---|---|---|---|
| Segurança | **FAIL** | 1 | 3 | 4 | 3 |
| Qualidade | **FAIL** | 0 | 1 | 4 | 1 + 3 CONCERN |
| Produto | **FAIL** | 0 | 3 | 3 | 1 |
| Drift docs | **FAIL** | 0 | 4 | 9 | 4 |
| LLM correctness | **CONCERNS** | 0 | 0 | 0 | 1 |
| Performance | **PASS** | 0 | 0 | 0 | 2 |
| Observabilidade | **FAIL** | 0 | 0 | 3 | 1 |
| Idempotência | **FAIL** | 1 | 2 | 2 | 0 |
| Supply chain | **PASS** | 0 | 0 | 0 | 2 |
| Conformidade LGPD | **FAIL** | 0 | 0 | 1 | 1 |
| **Total** | **7 FAIL / 1 CONCERN / 2 PASS** | **2** | **13** | **26** | **~18** |

**INV-RITUAL-001 bloqueia fechamento — 41 itens C/A/M abertos.**

## Achados CRÍTICOS (2)

1. **SEG-CAL-01** — Spoofing identidade cliente em `recepcionar` (`serializers.py:29-33` + `views.py:127-128`). `cliente_referencia_hash` + `cliente_key_id` aceitos do body. **Conserto Batch S2:** derivar server-side a partir de `cliente_id` + tenant.
2. **IDEMP-CAL-01** — 3 POSTs entregues sem `Idempotency-Key` (views.py recepcionar/configurar/cancelar). **Conserto Batch S3:** aplicar `IdempotencyMixin` padrão M3 OS.

## 5 Batches conserto causa-raiz planejados

1. **S1 drift-docs** (4A + 9M + 4B) — em execução. AGENTS.md hooks 377/48; +ADR-0065; +bullet M4; CLAUDE.md; CURRENT.md ≤40 linhas; diário 2026-05-26 + 2026-05-27.
2. **S2 segurança + LGPD** (1C + 3A + 4M + 1M-LGPD).
3. **S3 idempotência** (1C + 2A + 2M).
4. **S4 observabilidade** (3M + 1B).
5. **S5 produto + qualidade** (3A + 1A + 7M).

**Próxima passada formal Família 5** após S1..S5 entregar conserto.

## Detalhes em

- `docs/faseamento/M4-calibracao/auditoria-familia5.md` §3 (Achados estruturados) + §4 (Plano de conserto) + §5 (GATEs Wave A rastreados).
