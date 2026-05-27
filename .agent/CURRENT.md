# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS FECHADAS. **M4 calibracao P3 ENTREGUE + P4 ~156/160 T-CAL. P5 1ª passada Família 5 CONCLUÍDA 2026-05-27 (2 PASS / 1 CONCERN / 7 FAIL = 41 itens C/A/M). Batches S1+S2+S3+S5-inicial+S4+S5-restante FECHADOS — 2 CRÍTICO + 13 ALTO + 21/26 MÉDIO zerados. Pronto pra 2ª passada Família 5.**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-27)

- pytest M4 chave: **629/629** verde em ~27s (último full run 2026-05-26 — novos testes regressão pendentes drill PG).
- pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **379/379** verdes / **48 hooks ativos** (+2 cases M4 P9 hash-versionado).
- ruff/mypy: limpos nos paths novos.

## Histórico em `docs/faseamento/diario/`: 2026-05-25-{saneamento,marco4-p2-4-reviews,marco4-p3-matriz-e-tasks}.md + 2026-05-26-marco4-p4-fases5-10.md + 2026-05-27-marco4-p5-auditoria-1a-passada.md.

## CRÍTICOS — 2/2 ZERADOS ✅

1. ~~**SEG-CAL-01**~~ — ✅ fixed `146ef9b` (server-side hash PII).
2. ~~**IDEMP-CAL-01**~~ — ✅ fixed `4b58c24` (IdempotencyMixin + payload mismatch).

## Próximas ações (em ordem)

1. ~~**Batch S1 drift-docs**~~ ✅ fixed `7c06411` (13 C/A/M zerados).
2. ~~**Batch S2 segurança + LGPD**~~ ✅ parcial `146ef9b` (1C + 1A + 3M zerados; SEG-CAL-02/04/05/06 abertos).
3. ~~**Batch S3 idempotência**~~ ✅ fixed `4b58c24` (1C + 2A zerados).
4. ~~**Batch S5 inicial (ADR-0066)**~~ ✅ fixed `ae524e5` (2 ALTOs PROD-CAL-01/02 zerados).
5. ~~**Batch S4 observabilidade**~~ ✅ this lote — `append_evento_calibracao` use case (`src/application/.../append_evento_calibracao.py`) + `DjangoEventoDeCalibracaoRepository` (advisory lock + HMAC) + plug nas views (recepcionar/configurar/cancelar emitem evento WORM); logs `extra={tenant_id, correlation_id}` nos jobs + 3 actions; `_serializar_snapshot` agora retorna `correlation_id`.
6. ~~**Batch S5 restante**~~ ✅ this lote — SEG-CAL-02 (filtro tenant explícito em `obter_por_id`); SEG-CAL-04 (use case enforce `recebedor==actor` + `recebedor!=executor` cl. 6.2.5); SEG-CAL-05 (`run_in_tenant_context` em cada job); SEG-CAL-06 (migration 0014 GRANT app_user 23 tabelas); PROD-CAL-03 (use case `cancelar_calibracao` T-CAL-095); Q-CAL-01 (12 classes `TestINV_CAL_*` em `tests/regressao/test_inv_cal_classes_nomeadas.py`); Q-CAL-03 (regressão fail-open lazy); Q-CAL-04 (regressão UUID digit-heavy).
7. **2ª passada Família 5** ⏳ próximo — INV-RITUAL-001 destravado.

## ADRs aceitas escopo M4

- **0040** — Padrão metrológico como entidade separada (saneamento pré-M4).
- **0064** — Rotação anual HMAC + KMS Multi-Region 25a.
- **0065** — Concorrência calibração (UNIQUE composto + CAS + advisory lock).
- **0066** ✅ aceita 2026-05-27 — Fail-open lazy `cmc_cobre` + `procedimento_vigente_para` Wave A, paralela a ADR-0063.

## Pendências Wave A rastreadas

33 GATE-CAL-* novos M4 (12 RBC + 8 advogado + 3 tech-lead + 10 produto/seg/idemp) + GATE-OS-* (~20 M3) + 3 GATE-DEP (argon2/SHA workflows/SHA Dockerfile) carry-over. Detalhe em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5.
