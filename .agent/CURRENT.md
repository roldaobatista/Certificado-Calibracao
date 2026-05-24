# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`.

**Fase:** F-A+F-B + M1 + M2 + F-C1 FECHADAS · **M3 OS Fases 5+6+8 ENTREGUES (2026-05-24)**.
**Modo:** AUTÔNOMO.

## Estado da suíte (2026-05-24 pós Fase 5+6+8)

- Hooks `_test-runner.sh`: **288/288 verdes**.
- ruff/mypy: limpos em `src/application/operacao/os/`, `src/infrastructure/ordens_servico/{views,serializers,repositories,consumers}`.
- Suite M3 chave: **37/37 PASS** em 131s (8 arquivos `test_m3_os_*.py`).

## M3 OS Fases entregues (sessão 2026-05-24 noite)

**18 use cases puros + adapter + bus publish + 4 query services + 11 endpoints REST**:

| Fase | Escopo | Commit | Testes |
|---|---|---|---|
| 5 Bloco 1 | T-OS-040 `DjangoOSRepository` | `6e1faa8` | isinstance Protocol OK |
| 5 Bloco 2 | T-OS-041 `abrir_os_via_orcamento` + consumer real | `2c9b760` | 4/4 |
| 5 Bloco 3 | T-OS-048 adicionar_atividade | `317fa1a` | 3/3 |
| 5 Bloco 3 | T-OS-052/055/059 atribuir + iniciar + concluir | `2db…` | 3/3 |
| 5 Bloco 4/5 | T-OS-064/065/070/072 NC + cancelar | `a329ebb` | 5/5 |
| 5 Bloco 4/5/6 | T-OS-063/066/077/078/079/082/083 aceite + reabrir + 5 avançadas | `8ce76dc` | 8/8 |
| 5 Bus | `audit.event_helpers.publicar_evento` no consumer + ACOES_OS canônicas + bug fix `marcar_idempotencia` | `56b33f9` | 2/2 |
| 6 | T-OS-085..088 query services: visao 360 + listagem + timeline + do_tecnico | `…` | 6/6 |
| 8 | T-OS-094..099 ViewSets DRF: OS + Atividade + 11 endpoints + ACTION_MAP authz | `…` | 6/6 |

## Próximas fatias (restante M3)

- **Fase 7 (T-OS-090..093)**: 4 jobs procrastinate (watchdog cal-link, geo TTL 5a, anonimização retry, SLA breach watcher).
- **Fase 9 (T-OS-105..107)**: 3 hooks novos (migration-concorrencia-os, sync-merge-foto-appendonly, authz-check estendido).
- **Fase 10 (T-OS-108..120)**: 13 testes regressão INV (1 por INV-OS).
- **Predicates no consumer**: T-OS-044 (equipamento_baixado pré-use-case) + T-OS-050/054 (RT competência).
- **P5 ritual Spec Kit M3 OS** (10 auditores Família 5) — gate de fechamento.

## Marcos anteriores fechados

F-A+F-B (ritual completo). M1 `clientes` (ADR-0021). M2 `equipamentos` 65 T-EQP (CVE-2025-68616 mitigado). **F-C1** (14 T-FC1 + 10 auditores ZERO C/A/M; ADR-0054 aceito; 9 INVs novas em REGRAS; drills reais arquivados).

## Pendências rastreadas

70 GATEs Wave A. T-OS-090..147 (Fases 7, 9, 10 + ritual P5) restantes. Drift de PRD/spec/AGENTS sobre Fase 5/6/8 acumulada será reconciliado no encerramento M3 OS.
