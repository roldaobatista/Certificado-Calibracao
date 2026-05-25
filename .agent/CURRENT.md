# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 FECHADAS · **M3 OS P4 entregue / P5 em conserto causa-raiz (2026-05-24)**.
**Modo:** AUTÔNOMO.

## Estado da suíte (verificado 2026-05-24)

- pytest geral: **905/0/0** em 26min.
- Suite M3 chave: **89/89 PASS** em 415s (10 arquivos `test_m3_os_*.py` + 13 arquivos `tests/regressao/test_inv_os_*.py`).
- Hooks `_test-runner.sh`: **309/309** verdes / **42 hooks ativos** (+migration-concorrencia-os-check + sync-merge-foto-appendonly + authz-check predicates M3 do Marco 3 OS Fase 9).
- ruff/mypy: limpos nos paths novos.

## M3 OS — P4 entregue (Fases 1-10)

18 use cases + 4 query services + 11 endpoints REST + 4 jobs procrastinate + 7 consumers + 3 sagas + 13 regressões INV-OS (48 testes) + 3 hooks novos. Diário completo: `docs/faseamento/diario/2026-05-24-marco3-os-fases-1-10.md`.

## M3 OS — P5 1ª passada (2026-05-24)

| Auditor | Veredito | C | A | M |
|---|---|---|---|---|
| LLM-correctness / performance / observabilidade / supplychain / LGPD | **PASS** | 0 | 0 | 0 |
| Segurança | **FAIL** | 0 | 2 | 4 |
| Qualidade | **FAIL** | 4 | 3 | 3 |
| Produto | **FAIL** | 0 | 1 | 3 |
| Drift-docs | **FAIL** | 0 | 8 | 5 |
| Idempotência | **FAIL** | 0 | 0 | 7 |
| **Total** | **5 PASS / 5 FAIL** | **4** | **14** | **22** |

INV-RITUAL-001 bloqueia fechamento. Detalhes em `docs/faseamento/M3-os/auditoria-familia5.md`.

## Conserto causa-raiz em curso (2ª passada agendada)

Ordem batch: **drift-docs → idempotência → qualidade → produto → segurança**. Restantes 11..12 (integração + sagas + carga + drill) ficam como GAP Wave A. Predicates T-OS-050/054 (RT competência) ficam como GATE Wave A.

## Pendências rastreadas

70+ GATEs Wave A (5 GATE-OS-PERF + GATE-OS-BUS-BRIDGE-1 + GATE-OBS-LOG-EXTRA-1 + GATE-OBS-METRIC-OS-1 + GATE-IDEMP-HOOK-DETECT-ACTION + GATE-OS-SYNC-WAVE-A + GATE-OS-SUCESSAO-EVIDENCIA + GATE-OS-ANON-RETRY-1 + GATE-OS-VALIDAR-DRILL + GATE-OS-CONSBIO-TEXTO-OAB + GATE-OS-DPIA-OAB + GATE-DEP-001/002 herdados).
