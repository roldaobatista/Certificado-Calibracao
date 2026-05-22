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

## Marcos fechados

- **Marco 1 `clientes`** — P5 10 auditores ZERO C/A/M. `docs/faseamento/M1-clientes/auditoria-familia5.md`.
- **Marco 2 `equipamentos`** — 65 T-EQP, 2ª passada P5 ZERO C/A/M (CVE-2025-68616 WeasyPrint mitigado). `docs/faseamento/M2-equipamentos/auditoria-familia5.md`.

## Auditoria 10 lentes OS+Cal+Cert — 2 rodadas RESOLVIDAS 2026-05-23

- **R1:** 179 achados → 128 resolvidos (71%) em 6 ondas; 51 GATEs Wave A.
- **R2 (pós-retrofit R1):** 80 achados → **52 resolvidos (65%)** em Onda 7 (5 sub-ondas); 28 GATEs Wave A.
- **Total: 34 CRÍTICOS = 100% fechados** (28 R1 + 6 R2). Marco 3 OS destravado P1 **e P4**.
- 6 ADRs novas (0024..0029) + 22 INVs em REGRAS + RIPD geo OS + DPIA biometria touch + texto AceiteAtividade v1.0 + 4-party DPA + ADR-0021 Zona D.
- Consolidados: `docs/faseamento/auditorias/OS-CAL-RESOLUCAO-rodada-{1,2}.md`.

## Próximo passo

1. **GATE-SEG-BPT-1 EMERGENCIAL** — corretora SUSEP humana + briefing ADR-0028.
2. **Aceite formal** das 6 ADRs propostas (0024..0029) pelo Roldão.
3. **Marco 3 `os` — P1 (spec FORWARD)** pode arrancar imediatamente. P4 destravado.
4. **Marco 4 `calibracao`** — sequencial; pode arrancar P1 após Marco 3 P4 começar.

## Pendências rastreadas (não bloqueiam Marco 3)

- 51 GATEs Wave A em `OS-CAL-RESOLUCAO-rodada-1.md` (segurança apólices, ISO 17025 validação, observabilidade, drift cosmético).
- ADR-0018 (PWA QR scanner) + ADR-0019 Pilar 2 (apólice) pendentes (Marco 2 GATEs).
