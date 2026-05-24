# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 FECHADAS · **M3 OS P4 Fase 5 — 17 use cases entregues (2026-05-24)**.
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-24 pós Fase 5 fatias 1–6)

- Hooks `_test-runner.sh`: **288/288 verdes**.
- ruff/mypy: limpos em todo `src/application/operacao/os/` (10 source files) + adapter + entities.
- Suite M3 Fase 5: **23/23 PASS** (4 abrir + 3 adicionar + 3 lifecycle + 5 NC/cancel + 8 avançadas).

## M3 OS Fase 5 (sessão 2026-05-24 noite)

**17 use cases puros entregues** atravessando `DjangoOSRepository` real:

| Bloco | Use case | Commit | ACs cobertos |
|---|---|---|---|
| 1 | T-OS-040 `DjangoOSRepository` | `6e1faa8` | adapter Protocol |
| 2 | T-OS-041 `abrir_os_via_orcamento` + consumer real | `2c9b760` | AC-OS-001-1/2/7/8 |
| 3 | T-OS-048 `adicionar_atividade` | `317fa1a` | AC-OS-002-1/2/4 |
| 3 | T-OS-052 `atribuir_tecnico` + T-OS-055 `iniciar` + T-OS-059 `concluir` | `2db…` | AC-OS-002b-1, AC-OS-003-1/4, AC-OS-004-1/3/4 |
| 4/5 | T-OS-064 `marcar_nao_conformidade` + T-OS-065 `resolver_nc` + T-OS-070 `cancelar_atividade` + T-OS-072 `cancelar_os` | `a329ebb` | AC-OS-005-*, ADR-0042 |
| 4/5/6 | T-OS-063 `coletar_aceite` + T-OS-066 `reabrir_os` + T-OS-077 `reagendar` + T-OS-078 `transferir_tecnico` + T-OS-079 `dispensar_aceite` + T-OS-082 `marcar_no_show` + T-OS-083 `criar_os_avulsa` | `8ce76dc` | AC-OS-004-7, AC-OS-006, AC-OS-012/013/014/015 |

## Próximas fatias (Fase 5 restante e além)

- **Bus publish** (audit/event_helpers): `OS.Aberta`, `AtividadeConcluida`, etc. — caller dos consumers.
- **Predicates externos no consumer**: T-OS-044 (equipamento baixado), T-OS-050/054 (RT competência), T-OS-052 (UMC Lei 13.103).
- **Fase 6**: Query services (T-OS-085..089 — visão 360, listagem, timeline).
- **Fase 7**: Jobs procrastinate (T-OS-090..093 — watchdog cal-link, geo TTL).
- **Fase 8**: ViewSets DRF (T-OS-094..104 — endpoint POST/GET + idempotency-key).
- **Fase 9**: Hooks pré-commit novos (T-OS-105..107).
- **Fase 10**: 13 testes regressão INV (T-OS-108..120).

## Marcos anteriores fechados

F-A+F-B (ritual completo). M1 `clientes` (ADR-0021). M2 `equipamentos` 65 T-EQP (CVE-2025-68616 mitigado). **F-C1** (14 T-FC1 + 10 auditores ZERO C/A/M; ADR-0054 aceito; 9 INVs novas em REGRAS; drills reais arquivados).

## Pendências rastreadas

70 GATEs Wave A (51 prévios + 9 M3 + 10 F-C1). T-OS-085..147 (Fases 6–10) restantes. Drift de PRD/spec após acumular Fase 5 será reconciliado no encerramento M3 OS.
