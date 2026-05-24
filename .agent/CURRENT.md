# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + M3 P4 Fase 4 fechados · **F-C1 P4 + P5 1ª passada concluídas; consertos causa-raiz P5 aplicados em 2026-05-24.**
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-24 pós consertos P5)

- Hooks `_test-runner.sh`: **288/288 verdes**.
- ruff/mypy: limpos.
- Drill `validar_f_c1`: **10/10 PASS** (drill 9 ajustado pra exigir convenção `rotacao-dogfooding-YYYY-MM-DD.md` real).
- Pytest: **905/0/0** verde (re-rodar após consertos P5 pra confirmar).

## F-C1 P5 — 1ª passada (2026-05-24)

10 auditores rodaram: 5 FAIL (segurança, qualidade, produto, drift-docs, llm, observabilidade) + 4 PASS (perf, idemp, supplychain, lgpd). Total: 5 CRÍTICO + 8 ALTO + 9 MÉDIO.

**Consertos causa-raiz P5 (Tasks #12..#22 fechadas):** REGRAS 9 INV, ADR-0054 aceito, router via PYTEST_CURRENT_TEST, break-glass U2F enforce + GATE fail-loud, criar_admin_recovery grava Admin.BreakGlass.CONTA_CRIADA, drill 9 valida convenção real, 5 testes INV-ADMIN-003, conftest docstring honesta, +5 termos glossário, runbook §10 procedimentos canônicos. **Pendente:** Task #13 (AGENTS.md), #24 (drills Roldão), #25 (2ª passada).

## Próximo passo

(1) Task #13 AGENTS.md; (2) Task #24 Roldão drills; (3) re-rodar 10 auditores 2ª passada; (4) consolidar auditoria-familia5.md ZERO C/A/M.

## Marcos anteriores fechados

F-A+F-B (ritual Spec Kit completo). M1 `clientes` (10 auditores ZERO C/A/M; ADR-0021). M2 `equipamentos` 65 T-EQP (2ª passada ZERO C/A/M; CVE-2025-68616 mitigado). M3 OS P1+P2+P3+P4 Fases 1-4 (próximo: Fase 5 Services após F-C1 fechar).

## Pendências rastreadas

51+9 GATEs Wave A + T-OS-040..147 (8 fases M3 OS) + GATE-CYBER-BREAKGLASS-U2F-ENFORCE (Wave A).
