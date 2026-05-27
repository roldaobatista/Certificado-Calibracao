# .agent/CURRENT.md

> ≤40 linhas. Histórico expandido em `docs/faseamento/diario/`. **Modo:** AUTÔNOMO.

**Fase:** F-A+F-B + M1 + M2 + F-C1 + M3 OS + M4 calibracao + **SAN-PERFIL-TENANT Sprints 1-4 FECHADOS 2026-05-27 noite** ✅. Saneamento puro 100% entregue em sessão única após auditoria 10 lentes detectar FAIL L6 (fraude documental viável — `cmc_cobre` lia tipo_acreditacao do payload). ADR-0067 aceita. Próximo: Wave A propriamente (autorização Roldão).

## Estado da suíte (2026-05-27 noite)

- Drill `validar_san_perfil_tenant_migrations`: **17/17 PASS** (PG real).
- Drill `validar_san_perfil_tenant_snapshots`: **6/6 PASS** (PG real, Sprint 4).
- Relatório evidência defensiva A4: 1 evento pré-saneamento exportado.
- Suite ampla regression+audit+M3+M4: **exit 0** (todos verdes).
- Hooks `_test-runner.sh`: **414/414** verdes / **51 hooks ativos** (+3 ADR-0067).
- pytest geral: 905/0/0 (último full run 2026-05-24; pós-saneamento exige re-run).

## Sessão SAN-PERFIL-TENANT (2026-05-27 — 6 commits)

- `de229b8` docs(SAN-PERFIL-TENANT) — ADR-0067 aceita + spec/plan/tasks ritual Spec Kit + drift geografia MT (1032 linhas).
- `87bbc64` feat Sprints 1+2 — schema multi-step (migrations 0003-0010) + funções SECURITY DEFINER + predicate canônico `tenant_perfil_e` fecha FAIL L6 + 23 testes regressão.
- `de5877f` fix débitos pré-existentes M4 — `subcontratacao.actor_user_id` (7 testes) + `ClienteNotificadoVia.NAO_APLICA`.
- `f51fe47` feat Sprint 3 — `provisionar_tenant` + matriz feature×perfil + job vigência + emenda ADR-0015 + runbook DPO.
- `694ce27` feat Sprint 4 — snapshot `perfil_no_evento` WORM via trigger BEFORE INSERT + GUC `app.perfil_tenant` + retrofit equipamento + retrofit geo_truncamento (perfil A nunca trunca) + drill snapshots + relatório evidência A4.
- `aa56cdf` docs consolida tasks.md status Sprints 1-4 FECHADOS.

## Próxima ação (em execução)

**Auditoria 10 lentes pré-Wave A CONCLUÍDA 2026-05-27 madrugada.** Roldão decidiu "resolver TUDO — críticos, altos, médios, baixos". Plano consolidado em `docs/faseamento/auditorias/PRE-WAVE-A-CONSOLIDADO-rodada-1.md` (5 ondas).

**Em execução:** Onda PRE-A.1 (drift docs ~2h) — AGENTS.md/CLAUDE.md/INDICE.md/memory/clientes-prd/faseamento-FW corrigidos. Falta validar `_test-runner.sh`.

**Próximas ondas:** PRE-A.2 (promover/emenda ADRs ~25h + sessões Roldão) → PRE-A.3 (saneamento 16 PRDs Wave A ~130h em 4 batches paralelos) → PRE-A.4 (bus M3/M4 retrofit + TRACKs + F-C3 ~20d) → PRE-A.5 (F-C2 + drills internos — SEM contratações externas).

**Decisões Roldão 2026-05-27 noite:** HTMX+5 SPAs (ADR-0010); Aferê PJ separada DEPOIS; Onda 3 com 4 agentes paralelos; **zero contratações externas até produção real** (memória `project_sem_contratacoes_externas_ate_producao`).

## ADRs novas e GATEs SAN-PERFIL-TENANT

ADR-0067 aceita (perfil regulatório do tenant como entidade temporal 1ª classe). 7 GATEs Wave A rastreados em `docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md` §"Gates Wave A":
GATE-TENANT-PERFIL-{SCHEMA, PROVISIONING, TEMPLATES-CERT, MATRIZ-RETENCAO, AUTHZ-PREDICATE, TESTES-MATRIZ, OBSERVABILIDADE}.
INV-TENANT-PERFIL-001..007 declaradas em `REGRAS-INEGOCIAVEIS.md`.
