# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** Foundation F-A+F-B FECHADAS · Marco 1 `clientes` FECHADO · **Marco 2 `equipamentos` FECHADO** (10/10 PASS ZERO C/A/M na 2ª passada 2026-05-23).
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-23)

- `tests/test_equipamentos*.py + tests/regressao/`: **365/365 passed** em 141s.
- Suite completa: **621 passed em 37min** (OOM resolvido — `mem_limit: 12g` app / 4g db).
- Hooks `_test-runner.sh`: **207/207** verdes (25 hooks ativos).
- `makemigrations --check`: limpo · `ruff check`: zero issues.
- Drill `validar_m2_equipamentos`: **PASS** (18/18 verificações multi-tenant).

## Marco 2 `equipamentos` — FECHADO 2026-05-23

- **65 T-EQP** em 12 fases (US-EQP-001..006 + US-EQP-007 RT).
- 1ª passada (2026-05-22): 7 PASS / 3 FAIL (drift-docs/seguranca/llm).
- **2ª passada (2026-05-23): 10/10 PASS ZERO C/A/M** após conserto causa-raiz dos 11 achados.
- **CVE-2025-68616 WeasyPrint** mitigado in-app (`url_fetcher` custom); GATE-EQP-DEP-WEASYPRINT-UPGRADE Wave A.
- Detalhes em `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.

## Marco 1 — FECHADO

P5 10 auditores PASS ZERO C/A/M. `docs/faseamento/M1-clientes/auditoria-familia5.md`.

## Próximo passo

1. **Marco 3 `ordens-de-servico`** ou **Marco 3 `calibracao`** — definir próximo módulo Wave A com Roldão (faseamento em `docs/faseamento-modulos.md` v8).
2. **Aceite ADRs propostas** (0018 PWA QR scanner, 0019 responsabilidade IA) pelo Roldão antes de US-EQP-003 fase 4.
3. **GATE-EQP-DEP-WEASYPRINT-UPGRADE** Wave A — upgrade weasyprint 62→68 + pydyf<0.11→^0.11.

## Pendências rastreadas (não bloqueiam)

- ADR-0018 (PWA scanner QR) — aguardando aceite Roldão antes de US-EQP-003.
- ADR-0019 Pilar 2 — apólice cyber+E&O pré-1º tenant externo pago.
- GATE-EQP-1..PENTEST (14 itens Wave A — `docs/faseamento/M2-equipamentos/plan.md`).
