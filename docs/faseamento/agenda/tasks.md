---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-16
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: agenda
tipo: tasks
relacionados:
  - docs/faseamento/agenda/plan.md
  - docs/faseamento/agenda/spec.md
---

# Tasks — frente `agenda` (T-AGE-NNN, derivado do plan)

> Status em tempo real: `[ ]` pendente · `[x]` feito (com data/onda/testes) · `[~]` parcial. Numeração em dezenas
> por fatia, com saltos para inserir tarefas intermediárias (molde contas-receber). Refs apontam para D-AGE-N / INV / AC / R / TL-AGE.
> **Pré-condição de início (T-AGE-010+):** revisão do plan (plan §7) — tech-lead confirma sequenciamento + EXCLUDE
> com tenant_id + RT projetado; consultor-rbc re-confirma jornada/RT.

## Fatia 1a — domínio puro (`src/domain/operacao/agenda/`) — ✅ DONE 2026-06-16 (69 testes; ruff+mypy limpos; revisão crítica Opus)

> **Revisão crítica Opus (antes do commit) — 2 bugs encontrados e consertados na CAUSA-RAIZ + 3 testes de regressão:**
> (1) `_cruza_noturno` marcava QUALQUER evento >2h como noturno (heurística de duração errada — ex: 09:00-13:00 virava "noturno") → reescrito como **interseção real** com a janela `[22h,05h)`; (2) `materializar_janela` `WEEKLY;INTERVAL>1` quebrava a paridade na **virada de ano** (`ano*53+semana ISO`) → alinhado à semana calendário (`_segunda_da_semana`, WKST default). Testes que passavam por motivo errado (R5 bloqueava antes do R7; só checavam `ok`) agora têm caso explícito que CHEGA ao R7.
> **Débitos rastreados (refinamento / Fatia 2 / Wave B — NÃO bloqueiam; gate real = GATE-AGE-JORNADA-TRABALHISTA, advogado OAB humano):**
> - **R4 (DSR):** valida total de horas livres ≥35h em 6 dias, NÃO o BLOCO contínuo de 35h (simplificação mais permissiva). Refinar quando o enquadramento for validado por OAB.
> - **R1 (inter-jornada):** mede entre dias-calendário distintos — turnos cruzando meia-noite são aproximação (documentado no docstring).
> - **`proximo_slot_valido`:** usa `datetime.now()` como default — a Fatia 2 (use case) deve SEMPRE injetar `a_partir_de` (determinismo no domínio).
> - **`validar_jornada_umc` retorna a PRIMEIRA violação;** o `POST /agenda/validar` da Fatia 2 (lista `violacoes[]`) chama por etapas ou evolui a função.
> - Decisão de impl.: `EventoSimples` (não-frozen) interno em `jornada.py` evita import circular com `entities`; VO `TecnicoJornada` encapsula `is_tecnico_campo`+`aloca_em_umc`; recorrência sem `dateutil` (não está nas deps).

- [x] **T-AGE-010** `enums.py` — `TipoEvento`/`EstadoEvento`/`MotivoBloqueio`/`AcaoAuditoria`(+`reagendado`/`bloqueado`/`regime_indeterminado` — PLAN-AGE-08)/`RegimeJornada`/`FonteRegime` (`str,Enum`). Ref: D-AGE-3/15; spec §4.
- [x] **T-AGE-011** `entities.py` — `EventoAgenda`(raiz)/`Recorrencia`/`RegistroNoShow`/`CapacidadeTecnico`/`Feriado`/`EventoAuditoriaAgenda`/`RegimeJornadaColaborador` (`frozen+slots`). Ref: D-AGE-2/3/15; spec §4.
- [x] **T-AGE-012** `value_objects.py` — `Janela` (half-open, `inicia<termina`), `RegraRecorrencia` (RRULE), `ResultadoJornada`, `RegimeJornadaResolvido` (`fonte=indeterminado⇒nao_aplica`). Ref: D-AGE-13/15.
- [x] **T-AGE-013** `transicoes.py` — `_TRANSICOES` Mapping (Padrão A) + `validar_transicao`. Ref: D-AGE-3.
- [x] **T-AGE-014** `jornada.py` — `validar_jornada_umc(...)` puro, **perfil-agnóstico**, 5 regras R1–R5 + espera 1/1 + R7 noturno advisory (R2 só motorista_profissional; R6 non-goal) + `proximo_slot_valido`. Ref: D-AGE-4; INV-020/INV-AG-JORNADA-UMC-001; R4.
- [x] **T-AGE-015** `recorrencia.py` — `materializar_janela(regra, inicio, dias=90)` puro/determinístico/idempotente. Ref: D-AGE-8; R10.
- [x] **T-AGE-016** `portas.py` (6 Protocols `@runtime_checkable` + `EventoAgendaRepository`; `ColaboradorAgendaPort.regime_jornada(*, tenant_id, colaborador_id, na_data)`) + `erros.py` (hierarquia spec §4). Ref: D-AGE-5/6/7/9/15.
- [x] **T-AGE-017** `tests/test_agenda_dominio_fatia1a.py` — máquina estados (happy+unhappy); **5 regras de jornada por regime** (motorista_profissional c/ R2 × clt_geral s/ R2; espera 1/1; teto; DSR; refeição); `RegimeJornadaResolvido` fail-safe; `materializar_janela` idempotente; `Janela` half-open; Protocols. **Verificação 1a** (`--no-cov`).

## Fatia 1b — schema PG (`src/infrastructure/agenda/`) — ✅ DONE 2026-06-17 (28 testes; ruff+mypy limpos; 65/65 drill estrutural PASS; validar_agenda PASS)

> **Verificação 1b concluída 2026-06-17.** 8 migrations aplicadas: 0001_initial + 0002_rls_policies + 0003_exclusion_overlap (EXCLUDE GIST) + 0004_triggers_worm (INSERT-only WORM) + 0005_grants_app_user + 0006_seed_authz + 0007_seed_feriados (54 feriados nacionais 2025-2030) + 0008_alter_* (NO-OP drift cosmético). `validar_agenda` 65/65 PASS. 28 testes: RLS cross-tenant UNHAPPY, CHECK atividade_id, UNIQUE recorrência, INSERT-only WORM, EXCLUDE GIST (overlap/half-open/cross-tenant/cross-técnico/cancelado), concorrência real (deadlock e IntegrityError ambos válidos, invariante `<=1 commit`), seed feriados. Correção: `tests/conftest.py` + catálogo `_SEED_MIGRATIONS` com agenda 0006/0007.
> **Ajuste pós-commit (ADR-0030 — vigência canônica):** pré-commit da Fatia 1b bloqueado pelo hook `vigencia-canonica-check.sh` — campos `vigente_desde`/`vigente_ate` violavam o padrão canônico. Renomeados para `vigencia_inicio`/`vigencia_fim` em todos os artefatos: `entities.py`, `models.py`, `mappers.py`, `migrations/0001_initial.py`, `migrations/0008_alter_*`, `migrations/0004_triggers_worm.py` (comentários SQL), `tests/test_agenda_dominio_fatia1a.py` e `tests/test_agenda_schema_fatia1b.py`. Banco DEV e `test_afere` re-sincronizados. Verificação: `makemigrations --check` = "No changes detected", `validar_agenda` 65/65 PASS, 97 testes verdes, ruff + mypy limpos.
> **Revisão crítica Opus (antes do commit):** EXCLUDE `0003` confere (tenant_id 1ª coluna, `tstzrange '[)'`, `WHERE estado != cancelado`, btree_gist sem CREATE EXTENSION); teste de concorrência **não-mascara** (`assert not erros_inesperados` + invariante `≤1 commit` + `≤1 linha` no banco; deadlock e IntegrityError ambos abortam a tx conflitante); drill 65/65 + 28 testes reconfirmados pelo revisor. **Débito cosmético rastreado:** `0008_alter_*` é `AlterField` só de `help_text` (Django não gera DDL — NO-OP no banco) — squash no `0001` fica para housekeeping (greenfield; consolidar exige recriar o banco de teste de forma controlada, não vale o risco agora).

- [x] **T-AGE-020** `apps.py` (`label=agenda`; `ready()` com `# TODO Fatia 3: consumers`) + `models.py` (7 models achatados; `_choices(enum)`; `revision`; CHECK `atividade_id NOT NULL` quando `tipo='os'` — INV-AG-ATIVIDADE-001; UNIQUE `(recorrencia_id, ocorrencia_dt)` — R10). Ref: D-AGE-2/8.
- [x] **T-AGE-021** `mappers.py` + `repositories.py` (`DjangoEventoAgendaRepository` implementa Protocol). Ref: D-AGE-1.
- [x] **T-AGE-022** migration `0001_initial` (CreateModel + índice `(tenant_id, tecnico_id, inicia_at)` — R14). Ref: D-AGE-1.
- [x] **T-AGE-023** migration `0002_rls_policies` (ENABLE+FORCE+4 policies v2, todas as tabelas). Ref: D-AGE-14; INV-TENANT-*.
- [x] **T-AGE-024** migration `0003_exclusion_overlap` — **EXCLUDE GIST** `(tenant_id WITH =, tecnico_id WITH =, tstzrange '[)' WITH &&) WHERE estado != 'cancelado'`; `btree_gist`. Molde `0004_exclusion_imposto.py`. Ref: D-AGE-13; TL-AGE-01/R1/R12; INV-AG-OVERLAP-001.
- [x] **T-AGE-025** migration `0004_triggers_worm` — `EventoAuditoriaAgenda`/`RegistroNoShow`/`RegimeJornadaColaborador` INSERT-only (block-update/delete); eventos passados imutáveis (D-AGE-3). Ref: INV-AG-AUDIT-WORM-001.
- [x] **T-AGE-026** migrations `0005_grants_app_user` + `0006_seed_authz` (ações `agenda.*` × papéis) + `0007_seed_feriados` (catálogo nacional — D-AGE-10). Ref: D-AGE-10/14.
- [x] **T-AGE-026b** `audit/acoes_canonicas.py` — bloco `ACOES_AGENDA` (slugs lowercase) + união `ACOES_CANONICAS`. **Sem migration de CHECK** (sintático). Ref: D-AGE-5.
- [x] **T-AGE-027** `management/commands/validar_agenda.py` (drill: RLS+FORCE+4 policies, EXCLUDE GIST presente, triggers INSERT-only, UNIQUE recorrência, grants) + `tests/test_agenda_schema_fatia1b.py` (RLS, cross-tenant, **overlap rejeitado mesmo téc + permitido téc≠**, half-open 09-10/10-11, CHECK atividade_id, INSERT-only RAISE, **drill concorrência REAL do EXCLUDE** — 2 conexões disputam o slot, 1 commita/outra IntegrityError OU deadlock ambos válidos, molde commit `88483e3` — PLAN-AGE-05). **Verificação 1b** (`--reuse-db transaction=True`).

## Fatia 2 — use cases + REST (núcleo autossuficiente; portas FAKE; NÃO toca módulo fechado)

- [ ] **T-AGE-030** `validar_evento.py` (dry-run `POST /agenda/validar`: overlap+jornada+feriado+CNH, sem gravar — R9) + `tests/fakes/agenda_fakes.py` (fakes das 6 portas). Ref: US-AG-002; R9.
- [ ] **T-AGE-031** `criar_evento.py` — valida ANTES de gravar (409/422/412); grava + `EventoAuditoriaAgenda(criado)`; publica `agenda.evento.alocado`; jornada bloqueada→`agenda.jornada_umc.violada`+audit WORM. Ref: D-AGE-3; AC-AG-002/003; INV-AG-JORNADA-UMC-001/OVERLAP-001.
- [ ] **T-AGE-032** `criar_bloqueio.py` (US-AG-004 — férias/treino/atestado/outro; cobre slot atribuído→alerta) + `feriados.py` (CRUD custom + seed — US-AG-005). Ref: D-AGE-10; AC-AG-004/005.
- [ ] **T-AGE-033** `mover_evento.py`/`reagendar_evento.py` — revalida; passados imutáveis (D-AGE-3); reagenda+grava+**enfileira** aviso (stub Notificacao); publica `agenda.evento.reagendado`. Ref: US-AG-008; AC-AG-008.
- [ ] **T-AGE-034** `registrar_no_show.py` (`RegistroNoShow` INSERT-only; cobrável→`AReceberPort` FAKE; publica `agenda.no_show.registrado`) + `resolver_conflito.py` (`{manter_novo,manter_antigo,reagendar_ambos}` razão≥30 server-side; publica `agenda.conflito.resolvido`). Ref: US-AG-011/012; AC-AG-011/012; INV-AG-NOSHOW-AR-001.
- [ ] **T-AGE-035** `materializar_recorrencia.py` (job/command — janela 90d idempotente — R10) + `capacidade_dia.py` (75%/90%, default 8h — D-AGE-11; US-AG-010). Ref: D-AGE-8/11; AC-AG-009/010; INV-AG-RECORRENCIA-001.
- [ ] **T-AGE-036** `sugerir_slot.py` (US-AG-006 lógica interna: RT subst FAKE→competência→livre 7d; **independência cl. 6.2.5/ADR-0026 NÃO é critério de sugestão** — no máximo advisory "mesmo executor", nunca bloqueia — RBC-AGE-06) + `enquadrar_regime.py` (humano grava override `RegimeJornadaColaborador` INSERT-com-vigência; **IA nunca chama** — R6). Ref: D-AGE-15; AC-AG-006; INV-AG-REGIME-001.
- [ ] **T-AGE-037** `serializers.py` (sem perfil/regime do payload — server-side) + `views.py` (`AgendaViewSet` + actions; grade multi-técnico read-only **em 1 query agregada, O(1) em técnicos** — PLAN-AGE-04; por `tecnico_id` self-RLS US-AG-007) + `urls.py`; idempotência REST + **overlap garantido pelo EXCLUDE→409, SEM advisory lock** (PLAN-AGE-06) + `publicar_evento(outbox=True)` no `atomic`. Ref: D-AGE-13/14; US-AG-001/007.
- [ ] **T-AGE-038** `tests/test_agenda_api_fatia2.py` — criar OK(201); overlap mesmo téc→409; jornada motorista_profissional viola→422; `regime=nao_aplica`→aloca; feriado sem confirmar→422; `/validar` não grava; reagendar revalida+enfileira; no-show cobrável chama AReceber FAKE; conflito razão<30→422; recorrência replay sem duplicar; sem Idempotency-Key→400/428; cross-tenant→404; grade `assertNumQueries(N)` com **N fixo p/ 5 e 20 técnicos** (O(1) em técnicos — PLAN-AGE-04). **Verificação 2**.

## Fatia 3 — integrações cross-módulo (adapters reais tocam OS/colaboradores/CR/RT FECHADOS — R11) + INVs

### 3a — Adapters reais das portas (infra da agenda)
- [ ] **T-AGE-040** `OSSchedulingAdapter` → `application/operacao/os/atribuir_tecnico.py` (OS PENDENTE→AGENDADA) + leitura de atividade via repo (não SQL cru — TL-AGE-04/05). Ref: D-AGE-5; AC-AG-013; INV-AG-ATIVIDADE-001.
- [ ] **T-AGE-041** `ColaboradorAgendaAdapter` → papel + `pendencia_cnh` (`PapelColaboradorOutputSerializer`) + `regime_jornada(na_data)` (override vigente→deriva papel→indeterminado — R6); **422 `MotoristaSemCNH`** (R13). Ref: D-AGE-7/12/15; INV-AG-CNH-001/REGIME-001.
- [ ] **T-AGE-042** `RTSubstitutoAdapter` → predicate canônico de competência **projetado à `data=slot.inicia_at.date()`** (porta aceita data injetável — RESOLVIDO na revisão), **atravessando `RTSubstituicao` vigente na data do slot ANTES do titular** (ADR-0068 §2.2 — RBC-AGE-04); A determinístico=412/A incerto=warning/B-C warning/D off. **Limitação (PLAN-AGE-02/R15):** não projeta vínculo do titular (`encerrado_em` futuro) — agenda é consultiva. Confirmar na codificação a função canônica que atravessa substituição. Ref: D-AGE-6; AC-AG-014; INV-AG-PERFIL-001.
- [ ] **T-AGE-043** `AReceberAdapter` → monta `CriarTituloManualInput` (cliente `ReferenciaPIIAnonimizavel` + `perfil_no_evento` **server-side**, obrigatórios no `__post_init__`) + instancia `DjangoTituloRepository()` + `criar_titulo_manual.executar(inp, repo=repo)` (PLAN-AGE-03/R2). Ref: D-AGE-9; AC-AG-012; GATE-AGE-AR.

### 3b — Consumers do bus (fan-out — R8)
- [ ] **T-AGE-044** consumers `@consumer_idempotente` (registrados em `apps.py:ready()`, cada `registrar_consumer` em `try/except ValueError: pass` — PLAN-AGE-07): `os.aberta`/`os.cancelada`/`os.reaberta`/`os.atividade_concluida`/`os.atividade_cancelada`; `colaborador.desligado`/`papel_atribuido`/`papel_revogado`; `tenant.rt.trocado` + **`tenant.rt.substituicao_declarada`/`tenant.rt.substituicao_encerrada`** (RBC-AGE-04). Perfil do envelope (R7); fan-out aditivo sem retrofit (R8). Ref: spec §6; ADR-0068; INV-BUS-001.

### 3c — `esta_referenciado` p/ colaboradores (R11)
- [ ] **T-AGE-045** `ColaboradorReferenciadoPort.esta_referenciado` (técnico com agenda futura não hard-deletado) — arquivo NOVO + wiring (toca colaboradores só no registro — R11). Ref: D-AGE-12.

### 3d — INVs + hooks (família INV-AG-* ao mestre)
- [ ] **T-AGE-046** Cravar `## INV-AG-*` em `REGRAS-INEGOCIAVEIS.md` (molde INV-FIN): JORNADA-UMC-001/REGIME-001/OVERLAP-001/ATIVIDADE-001/PERFIL-001/RECORRENCIA-001/CNH-001/AUDIT-WORM-001/NOSHOW-AR-001 — 6 colunas, enforcement REAL (migrations/hooks/testes nomeados). INV-020 já reescrito (P3). Ref: spec §5.
- [ ] **T-AGE-047** 3 hooks (molde ordens_servico): `agenda-overlap-tenant-check.sh` (EXCLUDE c/ tenant_id), `agenda-jornada-perfil-agnostica-check.sh` (jornada não gateada por perfil), `agenda-regime-server-side-check.sh` (regime nunca do payload + IA não grava override). Registrar `pre-commit-manifest.tsv` + casos no `_test-runner.sh`. Ref: spec §5.
- [ ] **T-AGE-048** `tests/test_agenda_crossmodulo_fatia3.py` — `tipo=os` chama `atribuir_tecnico` real (OS→AGENDADA); 2 atividades mesma OS téc≠ OK; RT projetado à `data=slot` atravessa `RTSubstituicao` (A det=412/A inc=warning/B-C/D — **UNHAPPY por perfil**); **RT com saída planejada (`encerrado_em` futuro) NÃO é barrado pela agenda** (PLAN-AGE-02/R15 — comportamento esperado, gate na emissão); regime override vence + indeterminado→audit; no-show cria título real CR; consumers fan-out SEM engolir existentes (R8); `colaborador.desligado` cancela futura; `tenant.rt.trocado`/`substituicao_*` revisa; `esta_referenciado` bloqueia hard-delete; hooks verdes. **Verificação 3** + `_test-runner.sh`.

## P8/P9 — fechamento

- [ ] **T-AGE-060** P8: `matriz-reconciliacao.md` (US↔código↔teste; INV↔enforcement↔teste-com-ID; **reconciliação PRD↔spec**: `BloqueioAgenda`=`EventoAgenda(tipo=bloqueio)`; "12 ocorrências"=janela 90d; `AReceber.criar`=`criar_titulo_manual` via porta). TST-004: `tests/regressao/test_inv_ag_agenda.py` (testes nomeados por ID). `STATUS-GERADO` regenerado. Frontmatters→`stable`. `plano-dependencia-sistema.md` N5 (agenda destrava atribuição fail-open lazy da OS). **ADR só se a revisão indicar** (D-AGE-15 já sem ADR). Ref: plan §6.
- [ ] **T-AGE-061** P9: mutirão auditores roteados (sempre: seguranca/qualidade/llm-correctness/performance/observabilidade/idempotencia; +conformidade-lgpd PII; produto no merge). MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial. **Fecha módulo agenda — Wave A.** Ref: plan §6.

## Pré-condições antes de iniciar T-AGE-040+ (Fatia 3 — cross-módulo)

- ✅ Revisão do plan (plan §7) CONCLUÍDA — tech-lead APROVA C/ CORREÇÕES (PLAN-AGE-01..08) + consultor-rbc CONFIRMA c/ 2 ressalvas (RBC-AGE-04..06), tudo incorporado em plan+tasks.
- 🔲 **Na codificação da 3a (T-AGE-042):** confirmar QUAL função canônica de competência atravessa `RTSubstituicao` (ADR-0068) projetada a data futura; se nenhuma, débito de leitura/wiring (não código novo em módulo fechado).
