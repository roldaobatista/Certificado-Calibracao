# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** Auditoria 10 lentes pré-Wave A em execução — **Ondas 1+2+3 FECHADAS; Onda 4 PARCIAL (4 de 9 itens); Onda 5 PENDENTE.** 11 commits em 2026-05-27 noite (`27dd0d5`..`32c9b1d`). Consolidado em `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`.

## Estado da suíte (2026-05-27 noite pós Onda 4 batch 2)

- pytest M3+M4 chave: **786 passed / 1 skip** (regressão INV-OS-* + INV-CAL-* + consumers + use cases) em ~8min.
- Hooks `_test-runner.sh`: **413/413 PASS / 51 hooks ativos**.
- Drills PG real SAN-PERFIL: 17/17 migrations + 6/6 snapshots PASS.
- ruff/mypy: limpos.

## Ondas executadas 2026-05-27 noite

- ✅ **Onda PRE-A.1** drift docs — 5 CRÍT + 5 ALTO + 14 MÉD resolvidos.
- ✅ **Onda PRE-A.2** ADRs — 37 ADRs processadas: 24 promovidas + 5 emendas perfil + ADR-0022 v2 + ADR-0025 v2 + ADR-0068 (sucessão RT, novo) + ADR-0069 (bypass cl. 6.2, novo) + ADR-0019 superseded-by 0028 + 3 reservadas (0059/0060/0061).
- ✅ **Onda PRE-A.3** PRDs — 16 PRDs Wave A draft→stable via 4 agentes paralelos. 6 FAIL L6 fechadas + 15 US novas + 20 INVs novas.
- 🟡 **Onda PRE-A.4** bus + TRACKs + F-C3 — INT-01 retrofit M3 OS + INT-02 retrofit M4 calibração (786 testes verdes) + INT-03 perfil_no_evento no envelope + INT-04 hook BLOCK + F-C3 supply-chain (dependabot.yml + pin SHA Dockerfile + 3 workflows).

## Pendente Onda 4 (~8-10d trabalho restante)

- T-CAL-124..133 **10 ViewSets REST M4** (5d — torna produto visível).
- F-C3 paginação DRF + retrofit 621 testes (3d).
- Retrofit Sprint 4 `perfil_no_evento` em `contas-receber` + `fiscal` (1d).
- Limpa-mesa: GATE-FB-4 + GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA + GATE-EQP-RT-AUTHZ + GATE-DEP-001/002 + GATE-EQP-DEP-WEASYPRINT (2.5d).
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` plugado nos 3 use cases M3 (1.5d, fecha ADR-0063 fail-open).

## Pendente Onda 5 (sem contratações externas)

F-C2 dev (structlog real + INV-LOG + endpoints health/ready/deep + SIGTERM + correlation_id contextvar) + drills internos estruturais. GATEs externos rastreados como `GATE-EXTERNO-PRODUCAO` em `docs/conformidade/comum/gates-externos-pre-producao.md` (a criar).

## Decisões Roldão 2026-05-27 noite

HTMX + 5 SPAs / Aferê PJ separada DEPOIS / Onda 3 com 4 agentes paralelos / **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`) / **resolver TUDO — críticos, altos, médios, baixos**.
