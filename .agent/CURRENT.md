# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS + **M4 calibracao FECHADO 2026-05-27** ✅. 1ª passada (41 C/A/M) → 6 batches S1..S6.1 conserto causa-raiz → 2ª passada Família 5 (10 auditores): 8 PASS + 2 CONCERNS BAIXO carryover (seguranca GATE-KMS; drift-docs CONCERNS→PASS pós-S6.1). LLM-correctness subiu CONCERNS→PASS. Próximo: Wave A (autorização Roldão).

## Estado da suíte (2026-05-27)

- pytest M4 chave: **629/629** verde em ~27s.
- pytest geral: 905/0/0 (último full run 2026-05-24).
- Hooks `_test-runner.sh`: **379/379** verdes / **48 hooks ativos**.
- ruff/mypy: limpos nos paths novos.

## Histórico em `docs/faseamento/diario/`: 2026-05-25-{saneamento,marco4-p2-4-reviews,marco4-p3-matriz-e-tasks}.md + 2026-05-26-marco4-p4-fases5-10.md + 2026-05-27-marco4-p5-auditoria-1a-passada.md.

## Sessão pós-M4 (2026-05-27 — 11 commits)

- S1..S6.1 conserto causa-raiz Marco 4 P5 (consolidados em diário do dia).
- `8e8017a` FECHAMENTO M4 — INV-RITUAL-001 satisfeito (10/10 auditores PASS).
- `1b8f71c` + `4b63ee4` S7+S7.1 drift cross-marco (19 itens zerados; revalidação PASS).
- `5ab78cb` diário consolidado.
- Detalhe em `docs/faseamento/diario/2026-05-27-marco4-fechamento-e-housekeeping.md`.

## Estado pós-fechamento (limpo)

10 auditores Família 5 PASS (2ª passada M4 + revalidação drift cross-marco PASS). Zero achado bloqueante aberto. GATEs Wave A rastreados em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §6.

## Próxima ação (escolha Roldão)

1. **Wave A**: promover 12 ADRs propostas + drill PG real + plugar 7 ViewSets restantes.
2. **Marco 5** (certificados emitidos): próximo módulo natural após M4.
3. **F-C2** (observabilidade) / **F-C3** (resiliência): pré-1º deploy externo.

## ADRs M4 e GATEs Wave A

ADRs aceitas: **0040** (padrão metrológico entidade separada), **0064** (HMAC anual + KMS 25a), **0065** (concorrência: UNIQUE + CAS + advisory lock), **0066** (fail-open lazy `cmc_cobre` + `procedimento_vigente_para`). 33 GATE-CAL-* + GATE-OS-* (~20) + 3 GATE-DEP rastreados em `docs/faseamento/M4-calibracao/auditoria-familia5.md` §5.
