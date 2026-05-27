# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 ~156/160 T-CAL. P5 1ª passada Família 5 CONCLUÍDA 2026-05-27 (2 PASS / 1 CONCERN / 7 FAIL = 41 itens C/A/M). Batches S1 (drift-docs 13C/A/M) + S2 (segurança SEG-CAL-01 CRÍTICO + 4 ALTOs/MÉDIOs) + S3 (idempotência IDEMP-CAL-01 CRÍTICO + 2 ALTOs) FECHADOS. ADR-0066 aceita (S5 inicial: 2 ALTOs PROD-CAL-01/02 zerados via fail-open documentado).**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-27)

- pytest M4 chave: **629/629** verde em ~27s.
- pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **377/377** verdes / **48 hooks ativos** (M4 P9 — 6 hooks novos).
- ruff/mypy: limpos nos paths novos.

## Histórico em `docs/faseamento/diario/`: 2026-05-25-{saneamento,marco4-p2-4-reviews,marco4-p3-matriz-e-tasks}.md + 2026-05-26-marco4-p4-fases5-10.md + 2026-05-27-marco4-p5-auditoria-1a-passada.md.

## CRÍTICOS — 2/2 ZERADOS ✅

1. ~~**SEG-CAL-01**~~ — ✅ fixed `146ef9b` (server-side hash PII).
2. ~~**IDEMP-CAL-01**~~ — ✅ fixed `4b58c24` (IdempotencyMixin + payload mismatch).

## Próximas ações (em ordem)

1. ~~**Batch S1 drift-docs**~~ ✅ fixed `7c06411` (13 C/A/M zerados).
2. ~~**Batch S2 segurança + LGPD**~~ ✅ parcial `146ef9b` (1C + 1A + 3M zerados; SEG-CAL-02/04/05/06 abertos).
3. ~~**Batch S3 idempotência**~~ ✅ fixed `4b58c24` (1C + 2A zerados).
4. **Batch S4 observabilidade** ⏳ pendente (3 MÉDIO + 1 BAIXO — exige use case `append_evento_calibracao` + retrofit 16 use cases).
5. **Batch S5 produto + qualidade** parcial — ADR-0066 ✅ (2 ALTOs PROD-CAL-01/02 zerados); falta: PROD-CAL-03 (cancelar implementar OU rebaixar), Q-CAL-01 (renomear 12 classes TestINV_CAL_*), Q-CAL-02..05, SEG-CAL-02/04/05/06.
6. **2ª passada Família 5** após restante de S2/S4/S5.

## ADRs aceitas escopo M4

- **0040** — Padrão metrológico como entidade separada (saneamento pré-M4).
- **0064** — Rotação anual HMAC + KMS Multi-Region 25a.
- **0065** — Concorrência calibração (UNIQUE composto + CAS + advisory lock).
- **0066** ✅ aceita 2026-05-27 — Fail-open lazy `cmc_cobre` + `procedimento_vigente_para` Wave A, paralela a ADR-0063.

## Pendências Wave A rastreadas

33 GATE-CAL-* novos M4 (12 RBC + 8 advogado + 3 tech-lead + 10 produto/seg/idemp) + GATE-OS-* (~20 M3) + 3 GATE-DEP (argon2/SHA workflows/SHA Dockerfile) carry-over. Detalhe em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5.
