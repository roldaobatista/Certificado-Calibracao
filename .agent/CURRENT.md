# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** Auditoria 10 lentes pré-Wave A em execução — **Ondas 1+2+3 FECHADAS; Onda 4 PARCIAL (5 de 9 itens — +T-CAL-124); Onda 5 PENDENTE.** 12 commits em 2026-05-27 noite (`27dd0d5`..`c66cf90`). Consolidado em `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md`.

## Estado da suíte (2026-05-27 noite pós T-CAL-124)

- pytest M4 chave (5 módulos calibração + 2 regressões INV-CAL + LeituraViewSet smoke): **153/153 PASS** em 7.5s.
- pytest M3+M4 amplo (último full): 786 passed / 1 skip.
- Hooks `_test-runner.sh`: **413/413 PASS / 51 hooks ativos**.
- Drills PG real SAN-PERFIL: 17/17 migrations + 6/6 snapshots PASS.
- ruff/mypy: limpos (13 issues pré-existentes em migrations + models.py:1550 não tocados).

## Ondas executadas 2026-05-27 noite

- ✅ **Onda PRE-A.1** drift docs — 5 CRÍT + 5 ALTO + 14 MÉD resolvidos.
- ✅ **Onda PRE-A.2** ADRs — 37 ADRs processadas: 24 promovidas + 5 emendas perfil + ADR-0022 v2 + ADR-0025 v2 + ADR-0068 (sucessão RT, novo) + ADR-0069 (bypass cl. 6.2, novo) + ADR-0019 superseded-by 0028 + 3 reservadas (0059/0060/0061).
- ✅ **Onda PRE-A.3** PRDs — 16 PRDs Wave A draft→stable via 4 agentes paralelos. 6 FAIL L6 fechadas + 15 US novas + 20 INVs novas.
- 🟡 **Onda PRE-A.4** bus + TRACKs + F-C3 — INT-01 retrofit M3 OS + INT-02 retrofit M4 calibração (786 testes verdes) + INT-03 perfil_no_evento no envelope + INT-04 hook BLOCK + F-C3 supply-chain (dependabot.yml + pin SHA Dockerfile + 3 workflows).

## Pendente Onda 4 (~8-10d trabalho restante)

- T-CAL-124 ✅ **FECHADO 2026-05-27 noite** (commit `c66cf90`): LeituraViewSet (registrar-leitura + corrigir/rasura cl. 7.5) + 2 adapters Django (DjangoLeituraRepository + DjangoLeituraCorrecaoRepository) + helper `derivar_user_id_hash` + 8 testes serializer + **DRIFT FIX crítico**: `calibracao/urls.py` nunca estava plugado em `config/urls.py` raiz (CalibracaoViewSet T-CAL-123 estava órfã de roteamento desde P5).
- T-CAL-125..133 **9 ViewSets REST M4 restantes** (4-5d). ⚠️ **GAP estrutural descoberto**: `ComponenteIncertezaSnapshot` (domain) NÃO tem `tipo_origem_componente`/`distribuicao`/`divisor`/`formula_calculo` que o model `ComponenteIncerteza` exige `NOT NULL`. Use case `calcular_orcamento_incerteza` foi testado só com `FakeRepository` — nunca rodou em PG real. Mesmo padrão deve afetar 5+ snapshots restantes. **Antes do batch 2 dos ViewSets, retrofit domain⇔model é pré-requisito** (1-2d). Rastrear como GATE-CAL-DOMAIN-MODEL-DRIFT.
- F-C3 paginação DRF + retrofit 621 testes (3d).
- Retrofit Sprint 4 `perfil_no_evento` em `contas-receber` + `fiscal` (1d).
- Limpa-mesa: GATE-FB-4 + GATE-FC1-CRIAR-RECOVERY-SENHA-COMPLEXA + GATE-EQP-RT-AUTHZ + GATE-DEP-001/002 + GATE-EQP-DEP-WEASYPRINT (2.5d).
- GATE-OS-VALIDAR-DRILL + GATE-CAL-DRILL-LOCAL drills PG real (1d).
- GATE-OS-GRANDEZA-EM-ATIVIDADE — retrofit `AtividadeDaOS.grandeza` plugado nos 3 use cases M3 (1.5d, fecha ADR-0063 fail-open).

## Pendente Onda 5 (sem contratações externas)

F-C2 dev (structlog real + INV-LOG + endpoints health/ready/deep + SIGTERM + correlation_id contextvar) + drills internos estruturais. GATEs externos rastreados como `GATE-EXTERNO-PRODUCAO` em `docs/conformidade/comum/gates-externos-pre-producao.md` (a criar).

## Decisões Roldão 2026-05-27 noite

HTMX + 5 SPAs / Aferê PJ separada DEPOIS / Onda 3 com 4 agentes paralelos / **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`) / **resolver TUDO — críticos, altos, médios, baixos**.
