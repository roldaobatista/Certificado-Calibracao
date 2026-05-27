# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS + **M4 calibracao FECHADO 2026-05-27** ✅. 1ª passada (41 C/A/M) → 6 batches S1..S6.1 conserto causa-raiz → 2ª passada Família 5 (10 auditores): 8 PASS + 2 CONCERNS BAIXO carryover (seguranca GATE-KMS; drift-docs CONCERNS→PASS pós-S6.1). LLM-correctness subiu CONCERNS→PASS. Próximo: Wave A (autorização Roldão).

## Estado da suíte (2026-05-27)

- pytest M4 chave: **629/629** verde em ~27s.
- pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **379/379** verdes / **48 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## Histórico em `docs/faseamento/diario/`: 2026-05-25-{saneamento,marco4-p2-4-reviews,marco4-p3-matriz-e-tasks}.md + 2026-05-26-marco4-p4-fases5-10.md + 2026-05-27-marco4-p5-auditoria-1a-passada.md.

## Batches conserto P5 (todos commitados)

- S1 `7c06411` drift-docs (13 C/A/M).
- S2 `146ef9b` segurança+LGPD parcial (1C + 1A + 3M; SEG-CAL-01 CRÍTICO).
- S3 `4b58c24` idempotência (1C + 2A; IDEMP-CAL-01 CRÍTICO).
- S5-inicial `ae524e5` ADR-0066 fail-open lazy (2 ALTOs PROD-CAL-01/02).
- S4+S5-restante `6464dfe` observabilidade + SEG-CAL-02/04/05/06 + PROD-CAL-03 + Q-CAL-01/03/04 (1 ALTO + 13 MÉDIO).
- S6 corrente — drift-docs sync 377→379 + ADR-0066 no header + auditoria L33 + CURRENT compactado.

## 2ª passada Família 5 — 2026-05-27

10 auditores em paralelo: 8 PASS limpo (seg→CONCERNS BAIXO carryover; supplychain; idempotencia; observabilidade; llm-correctness — subiu de CONCERNS pra PASS; qualidade; lgpd; performance; produto — 1 CONCERN BAIXO docstring já consertado nesta sessão) + 1 CONCERNS drift-docs (resolvido em S6).

## Próxima ação

**Wave A** — aguardando autorização Roldão. Pré-requisitos: PRDs `stable`, ADRs propostas (0003/0004/0008/0009/0010/0014/0015/0016/0018/0019/0034/0035) viram aceitas.

## ADRs M4 e GATEs Wave A

ADRs aceitas: **0040** (padrão metrológico entidade separada), **0064** (HMAC anual + KMS 25a), **0065** (concorrência: UNIQUE + CAS + advisory lock), **0066** (fail-open lazy `cmc_cobre` + `procedimento_vigente_para`). 33 GATE-CAL-* + GATE-OS-* (~20) + 3 GATE-DEP rastreados em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5.
