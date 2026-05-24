# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + **F-C1 FECHADAS** · M3 OS P4 Fase 4 fechado (2026-05-24).
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-24 pós F-C1 P5 2ª passada)

- Hooks `_test-runner.sh`: **288/288 verdes**.
- ruff/mypy: limpos.
- Drill `validar_f_c1`: **10/10 PASS** sem `--rapido` (inclui drill 9 reconhecendo `rotacao-dogfooding-YYYY-MM-DD.md` real + drill 10 break-glass).
- Pytest: **905/0/0** verde (re-validação pós-consertos pendente, suite chave 30/30 OK).

## F-C1 FECHADA sob INV-RITUAL-001 (2026-05-24)

- **P4 entregue:** 14 T-FC1 (settings prod + admin hardening + ADR-0054 webhook out + rotação dogfooding + break-glass + drill).
- **P5 1ª passada:** 5 FAIL + 4 PASS — 5 C + 8 A + 9 M (16 commits de conserto: `d19ad60`..`3e92368`).
- **Consertos causa-raiz** Tasks #12..#24: REGRAS 9 INV, ADR-0054 aceito, router via PYTEST_CURRENT_TEST, break-glass U2F enforce + GATE fail-loud, evento Admin.BreakGlass.CONTA_CRIADA na cadeia, drill 9 ajustado, 5 testes INV-ADMIN-003, conftest docstring honesta, glossário +5 termos, runbook §10, drills reais arquivados (rotação + break-glass).
- **P5 2ª passada:** 10/10 PASS ZERO C/A/M. Doc canônico `docs/faseamento/F-C1/auditoria-familia5.md` `stable`.

## Próximo passo

**M3 OS P4 Fase 5 (Services + use cases — 15 US, T-OS-040..084 ~45 tarefas).** Substitui placeholders dos consumers Fase 4 pelas chamadas reais aos use cases.

## Marcos anteriores fechados

F-A+F-B (ritual completo). M1 `clientes` (ADR-0021). M2 `equipamentos` 65 T-EQP (CVE-2025-68616 mitigado). **F-C1** (14 T-FC1 + 10 auditores ZERO C/A/M; ADR-0054 aceito; 9 INVs novas em REGRAS; drills reais arquivados).

## Pendências rastreadas

10 GATEs Wave A novos (F-C1): GATE-CYBER-BREAKGLASS-U2F-ENFORCE, GATE-CYBER-BREAKGLASS-DRILL, GATE-FC1-ROTACAO-DRILL-REAL (próxima 2026-06-24), GATE-FC1-ENV-PRODUTIVO, GATE-LGPD-DPIA-ADMIN-2, GATE-OBS-BREAKGLASS-METRICS, GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA, GATE-QLD-FC1-2/3, GATE-DEP-DOCKERFILE-SHA-PIN. Total Wave A: 51 prévios + 9 M3 + 10 F-C1 = 70 GATEs. T-OS-040..147 (8 fases M3 OS) restantes.
