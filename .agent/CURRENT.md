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

## Auditoria 10 lentes OS+Cal+Cert — RESOLVIDA 2026-05-23

- 179 achados → **128 resolvidos (71%)** em 6 ondas de retrofit; 51 viram GATE-* Wave A.
- **28 CRÍTICOS = 100% fechados.** Marco 3 destravado sob INV-RITUAL-001.
- 5 ADRs novas (0024..0028) + 13 INVs em REGRAS + RIPD geo OS + 4-party DPA + ADR-0021 Zona D.
- Consolidado: `docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-1.md`.

## Próximo passo

1. **GATE-SEG-BPT-1 EMERGENCIAL** — acionar corretora SUSEP humana (Marsh/AON/Howden) com briefing ADR-0028. Apólice BPT antes da próxima recepção em Balanças Solution.
2. **Aceite formal** das 5 ADRs propostas (0024..0028) pelo Roldão.
3. **Marco 3 `os`** — arrancar ritual Spec Kit (spec FORWARD → plan + reviews → tasks → P4 → P5 10 auditores).
4. **Marco 4 `calibracao`** — sequencial ao Marco 3.

## Pendências rastreadas (não bloqueiam Marco 3)

- 51 GATEs Wave A em `OS-CAL-RESOLUCAO-rodada-1.md` (segurança apólices, ISO 17025 validação, observabilidade, drift cosmético).
- ADR-0018 (PWA QR scanner) + ADR-0019 Pilar 2 (apólice) pendentes (Marco 2 GATEs).
