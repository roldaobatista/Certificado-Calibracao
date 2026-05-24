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

## Fase 10 (sessão 2026-05-24 noite)

- 5 arquivos regressão entregues: INV-OS-ATIV-002 (cross-tenant), INV-OS-CONC-001 (constraint declarativo), INV-OS-FAT-001 (cancelamento + OS.EscopoAlterado), **INV-OS-SUC-001** (sucessão M&A — `7b7bbee`), **INV-OS-EQP-001** (equipamento baixado — `7b7bbee`). 15/15 testes regressão PASS.
- **T-OS-044 entregue:** pre-check `Equipamento.status IN {sucata, extraviado}` no consumer `Orcamento.Aprovado` (`7b7bbee`).
- **Fase 9 T-OS-105 entregue:** hook `migration-concorrencia-os-check.sh` (`4ef49e9`) — bloqueia migration que cria/remove `idx_atividade_em_execucao_por_equip` ou desativa RLS em `atividade_da_os`. +7 casos no `_test-runner.sh`.
- **Hooks: 288 → 295 ok / 0 falhas.**
- 6º arquivo regressão (`6c99b2c`): INV-OS-CONSBIO-001 + INV-OS-ANAL-001 (6 testes — happy + unhappy + cross-tenant cada).

## Fase 7 (sessão 2026-05-24 noite)

- **4 jobs procrastinate entregues** (`…`): watchdog_calibracao_link (T-OS-090), truncar_geo_lgpd (T-OS-091), retry_anonimizacao_pendente (T-OS-092), detectar_sla_breach (T-OS-093).
- Management command `python manage.py processar_jobs_os [--tenant X] [--job Y]`.
- 6/6 testes Fase 7 PASS.
- **Suíte M3 chave consolidada: 64/64 PASS em 284s.**
- **Hooks: 295/295 verdes.**

## Fase 10 cont. (sessão 2026-05-24 noite)

- 2 arquivos regressão adicionais: INV-OS-ATIV-001 (terminal — 3 testes) + INV-OS-ATIV-005 (executor único — 4 testes). 7/7 PASS.
- **Total Fase 10: 8 arquivos / 30 testes regressão INV-OS.**

## Próximas fatias (restante M3)

- **Fase 9 restante (T-OS-106/107)**: hook sync-merge-foto-appendonly (Wave A — sync mobile não existe) + authz-check estendido (vigilante).
- **Fase 10 restante**: regressão para INV-OS-AUD-001, CAL-LINK-001, GEO-001, SYNC-001, ANON-001 (5 INVs — alguns já cobertos implicitamente em jobs/timeline tests).
- **Predicates no consumer**: T-OS-050/054 (RT competência) — depende de `rt_competencia_cobre`.
- **P5 ritual Spec Kit M3 OS** (10 auditores Família 5) — gate de fechamento.

## Marcos anteriores fechados

F-A+F-B (ritual completo). M1 `clientes` (ADR-0021). M2 `equipamentos` 65 T-EQP (CVE-2025-68616 mitigado). **F-C1** (14 T-FC1 + 10 auditores ZERO C/A/M; ADR-0054 aceito; 9 INVs novas em REGRAS; drills reais arquivados).

## Pendências rastreadas

70 GATEs Wave A. T-OS-090..147 (Fases 7, 9, 10 + ritual P5) restantes. Drift de PRD/spec/AGENTS sobre Fase 5/6/8 acumulada será reconciliado no encerramento M3 OS.
