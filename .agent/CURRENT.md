# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 ~156/160 T-CAL (4 grupos TRACK Wave A). P5 1ª passada Família 5 CONCLUÍDA 2026-05-27: 2 PASS (performance + supply chain) / 1 CONCERNS (llm-correctness) / 7 FAIL com 2 CRÍTICO + 13 ALTO + 26 MÉDIO. 5 batches conserto causa-raiz em execução (S1 drift-docs em andamento).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-27)

- pytest M4 chave: **629/629** verde em ~27s.
- pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **377/377** verdes / **48 hooks ativos** (M4 P9 — 6 hooks novos).
- ruff/mypy: limpos nos paths novos.

## Histórico em `docs/faseamento/diario/`: 2026-05-25-{saneamento,marco4-p2-4-reviews,marco4-p3-matriz-e-tasks}.md + 2026-05-26-marco4-p4-fases5-10.md + 2026-05-27-marco4-p5-auditoria-1a-passada.md.

## CRÍTICOS abertos (2)

1. **SEG-CAL-01** — Spoofing identidade cliente em `recepcionar` (serializer aceita `cliente_referencia_hash` do body). Batch S2.
2. **IDEMP-CAL-01** — 3 POSTs sem `Idempotency-Key`. Batch S3.

## Próximas ações (em ordem)

1. **Batch S1 drift-docs** ⏳ — em execução: AGENTS.md §3/§11/§12; CLAUDE.md; CURRENT.md (este); diário M4-26/27 criados; faltam tasks.md frontmatter draft + revisar 🟡 proposta em §11.
2. **Batch S2 segurança + LGPD** (1 CRÍTICO + 3 ALTO + 5 MÉDIO).
3. **Batch S3 idempotência** (1 CRÍTICO + 2 ALTO + 2 MÉDIO).
4. **Batch S4 observabilidade** (3 MÉDIO + 1 BAIXO).
5. **Batch S5 produto + qualidade** (3 ALTO + 1 ALTO + 7 MÉDIO).
6. **2ª passada Família 5** após S1..S5.

## ADRs aceitas escopo M4

- **0040** — Padrão metrológico como entidade separada (saneamento pré-M4).
- **0064** — Rotação anual HMAC + KMS Multi-Region 25a.
- **0065** — Concorrência calibração (UNIQUE composto + CAS + advisory lock).
- **0066** (esperada Batch S5) — Fail-open lazy `cmc_cobre` + `procedimento_vigente_para` Wave A, paralela a ADR-0063.

## Pendências Wave A rastreadas

33 GATE-CAL-* novos M4 (12 RBC + 8 advogado + 3 tech-lead + 10 produto/seg/idemp) + GATE-OS-* (~20 M3) + 3 GATE-DEP (argon2/SHA workflows/SHA Dockerfile) carry-over. Detalhe em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5.
