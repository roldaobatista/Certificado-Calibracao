---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-16
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: agenda
tipo: plan
proximo-passo: P4 — codar Fatia 1a (domínio puro, T-AGE-010..017; não exige Docker/PG)
relacionados:
  - docs/faseamento/agenda/spec.md
  - docs/faseamento/agenda/reviews-consolidado.md
  - docs/faseamento/agenda/tasks.md
  - docs/dominios/operacao/modulos/agenda/prd.md
---

# Plan — frente `agenda` (P3, derivado da spec P1+P2)

> Regra "não declarar pronto sem rodar" (feedback 2026-05-18): cada fatia tem **Verificação** executada em
> ambiente real antes de seguir. Greenfield de código (não existe `src/**/agenda/` hoje — `T-AGE-000` confirmou).
> Molde técnico = `ordens_servico` (vizinho de domínio, mesmo path aninhado) + ritual `contas-receber` (vizinho de fila).

## 0. Princípio de sequenciamento (ordem por dependência + anti-retrabalho)

Dependência interna: **domínio puro → schema PG → use cases/REST (núcleo autossuficiente com portas-FAKE) →
integrações cross-módulo (adapters reais tocam OS/colaboradores/CR/RT, FECHADOS) → fechamento**. Peças
compartilhadas (predicate `validar_jornada_umc`, `materializar_janela`, VOs `Janela`/`RegimeJornadaResolvido`)
entram no domínio (1a) e são reusadas pelas fatias seguintes. O **núcleo (Fatia 2) entrega calendário +
criação de evento + validação de jornada/overlap/feriado + recorrência SEM tocar nada fechado** (portas com
implementação FAKE em `tests/` e stub em infra) — é o piso garantido. O que depende de tocar módulo fechado
(adapters reais + consumers do bus) é a ÚLTIMA fatia de código (Fatia 3). Mesma disciplina do `contas-receber`.

## 1. Riscos e mitigações (cravados antes de codar)

| # | Risco | Sev | Mitigação | Achado |
|---|-------|-----|-----------|--------|
| R1 | EXCLUDE de overlap **omitir `tenant_id`** → furo de isolamento (RLS não escopa constraint) | **CRIT** | `EXCLUDE USING gist (tenant_id WITH =, tecnico_id WITH =, tstzrange(inicia_at,termina_at,'[)') WITH &&) WHERE (estado != 'cancelado')`; molde `configuracoes_sistema/migrations/0004_exclusion_imposto.py`; `btree_gist` já disponível | TL-AGE-01 |
| R2 | No-show: criar consumer **dentro de CR (FECHADO)** = toque indevido | ALTO | agenda CHAMA `criar_titulo_manual` (use case público de CR — `application/contas_receber/`) via `AReceberPort`; adapter concreto no infra da agenda; perfil server-side no título, nunca do payload | TL-AGE-02 / D-AGE-9 |
| R3 | Estender `colaboradores` (FECHADO) p/ `pendencia_cnh`/`is_tecnico_campo`/`regime_jornada` | ALTO | `is_tecnico_campo` derivado do papel + `pendencia_cnh` já legível via `ColaboradorAgendaPort` (zero extensão); `regime_jornada` por override que mora na AGENDA (`RegimeJornadaColaborador`), não em colaboradores | TL-AGE-03 / D-AGE-12/15 |
| R4 | Jornada gated por perfil A/B/C/D (ERRADO — é eixo trabalhista, ordem pública) | **CRIT (legal)** | `validar_jornada_umc` **perfil-AGNÓSTICO**; discriminado por `regime_jornada`; INV-020 reescrito (espera 1/1 ADI 5322 + R1–R7); **GATE-AGE-JORNADA-TRABALHISTA** (OAB humano pré-prod) | RBC-AGE-01 / ADV-AGE-04 |
| R5 | RT substituto **barra cedo demais** (agendar é planejar) | ALTO | competência projetada à **`data=slot.inicia_at.date()`** (porta RT aceita data injetável — PLAN-AGE-01/RBC-AGE-05), **atravessando `RTSubstituicao` vigente na data do slot ANTES do titular** (ADR-0068 §2.2 — não só `RTCompetencia` do titular — RBC-AGE-04); A determinístico=**412 `SemRTNoSlot`** / A incerto=warning; B/C warning+confirma; D off; **gate duro de NC vive na EMISSÃO** (`certificados`, já existe), não na agenda | RBC-AGE-02/04 / D-AGE-6 |
| R15 | Porta RT projeta competência+substituição mas **não o vínculo do titular** (`encerrado_em`/`data_fim_vigencia` futuro): RT com saída planejada não é detectado | MÉDIO | **aceitar** — agenda é CONSULTIVA (gate duro na emissão, D-AGE-6); documentar limitação; teste UNHAPPY (T-AGE-048) NÃO assume que a agenda barra RT com saída planejada | PLAN-AGE-02 |
| R6 | `regime_jornada` derivado por papel erra o enquadramento real (falso-bloqueio E falso-negativo) | ALTO | resolução fail-safe na porta: override humano vigente → deriva papel → papéis de campo conflitantes sem override = `nao_aplica` + audit `regime_indeterminado` + pendência; **IA NUNCA grava override** (só humano RH/advogado) | D-AGE-15 / ADV-AGE-02 |
| R7 | Consumer relê `obter_perfil_tenant_corrente()` no worker → perfil ATUAL, não do fato gerador (fura CGCRE 8.4) | ALTO | consumer lê `envelope["perfil_no_evento"]`; `None` → fail-closed; **espelha R4 do `contas-receber`** | TL-AGE-06 / RBC-CR-03 |
| R8 | `os.*`/`colaborador.*` já têm consumers → registrar consumer da agenda seria **engolido** | ALTO | `_REGISTRY: dict[str, list]` **já é fan-out** (`audit/outbox_worker.py:94`, resolvido no CR); `registrar_consumer` acumula fns DIFERENTES; cada `@consumer_idempotente` por `consumer_id` único, all-or-nothing por linha | TL-AGE-06 / [[fan-out-bus-consumers-os-concluida]] |
| R9 | Drag-drop aceita evento e **depois** rejeita (viola NFR §9) | MÉDIO | validar overlap + jornada + feriado **ANTES** de gravar; `POST /agenda/validar` pré-save (dry-run); 422/412/409 com payload acionável | NFR §9 / US-AG-002 |
| R10 | Recorrência **duplica** ao re-materializar no job diário | MÉDIO | `UNIQUE(recorrencia_id, ocorrencia_dt)`; `materializar_janela` determinística e idempotente (ADR-0033) | D-AGE-8 |
| R11 | Pré-commit em módulos fechados (OS/colaboradores/CR) trava por hook de invariante em código legado | MÉDIO | skip oficial + justificativa ≥10 chars no diff (não é mascaramento — [[feedback_precommit_modulos_fechados]]); stage seletivo; **nunca commits concorrentes**; pré-commit ~5min | memória projeto / R14 CR |
| R12 | Slots adjacentes colidirem (09:00–10:00 vs 10:00–11:00) | MÉDIO | `tstzrange` **half-open `'[)'`**; teste de borda explícito | D-AGE-13 |
| R13 | `MOTORISTA_UMC` sem CNH/CNH vencida alocado em evento `aloca_em_umc` | MÉDIO | antes de alocar, checar `pendencia_cnh` + validade via porta → **422 `MotoristaSemCNH`** | D-AGE-7 / INV-AG-CNH-001 |
| R14 | Materialização 90d pesada / N+1 na grade multi-técnico (NFR p95≤1s/20téc) | MÉDIO | job batch; horizonte fixo 90d; índice `(tenant_id, tecnico_id, inicia_at)`; grade = **1 query agregada** (`filter(tenant_id, inicia_at__range)` + agrupa por `tecnico_id` no Python), NUNCA 1 query/técnico; `assertNumQueries(N)` com **N fixo (≤3) independente do nº de técnicos** (prova O(1) em técnicos) | D-AGE-8 / AC-AG-001-2 / PLAN-AGE-04 |

## 2. Fatia 1a — domínio puro (`src/domain/operacao/agenda/`)

Criar (molde `src/domain/operacao/os/`):
- `enums.py` — `TipoEvento`(os|bloqueio|descanso_legal|deslocamento|almoco|manutencao_interna|feriado), `EstadoEvento`(agendado|em_execucao|concluido|cancelado|no_show), `MotivoBloqueio`(ferias|treinamento|atestado|outro), `AcaoAuditoria`(criado|movido|reagendado|bloqueado|cancelado|aprovado|no_show|regime_indeterminado) (PLAN-AGE-08), `RegimeJornada`(motorista_profissional|clt_geral|nao_aplica), `FonteRegime`(override_humano|derivado_papel|indeterminado). Todos `str, Enum`.
- `entities.py` — `EventoAgenda`(raiz), `Recorrencia`, `RegistroNoShow`, `CapacidadeTecnico`, `Feriado`, `EventoAuditoriaAgenda`, `RegimeJornadaColaborador` (`@dataclass(frozen=True, slots=True)`).
- `value_objects.py` — `Janela(inicia_at, termina_at)` (valida `inicia<termina`; half-open), `RegraRecorrencia` (RRULE RFC 5545), `ResultadoJornada(ok, violacao, faltante_min, proximo_slot)`, `RegimeJornadaResolvido(regime, fonte)` (`fonte=indeterminado ⇒ regime SEMPRE nao_aplica`).
- `transicoes.py` — `_TRANSICOES: Mapping[EstadoEvento, frozenset]` + `validar_transicao` (Padrão A — D-AGE-3).
- `jornada.py` — `validar_jornada_umc(tecnico, regime, janela, eventos, capacidade) -> ResultadoJornada` (puro; **perfil-agnóstico**; 5 regras R1–R5 + espera 1/1 + R7 noturno advisory; R2 só `motorista_profissional`; R6 non-goal) + `proximo_slot_valido`.
- `recorrencia.py` — `materializar_janela(regra, inicio, dias=90) -> list[datetime]` (puro, determinístico, idempotente).
- `portas.py` — Protocols `@runtime_checkable`: `OSSchedulingPort`, `ColaboradorAgendaPort` (papel/`pendencia_cnh`/`regime_jornada(*, tenant_id, colaborador_id, na_data)`), `RTSubstitutoPort`, `MapsProvider`, `NotificacaoClientePort`, `AReceberPort` + `EventoAgendaRepository`.
- `erros.py` — `JornadaUMCViolada`(422), `SemRTNoSlot`(412), `ConflitoAgenda`(409), `MotoristaSemCNH`(422), `FeriadoNaoConfirmado`(422), `PerfilIndeterminado`/`RegimeIndeterminado` (fail-closed/advisory).

**Verificação 1a:** `pytest tests/test_agenda_dominio_fatia1a.py --no-cov` — domínio puro, sem Django/PG. Cobre:
máquina de estados (happy+unhappy parametrize); **as 5 regras de jornada** por regime (motorista_profissional com
R2 × clt_geral sem R2; espera 1/1; teto diário; DSR 35h/6d; refeição); `RegimeJornadaResolvido` fail-safe
(indeterminado⇒nao_aplica); `materializar_janela` determinística + idempotente; `Janela` half-open; Protocols runtime_checkable.

## 3. Fatia 1b — schema PG (`src/infrastructure/agenda/`)

Criar (molde `src/infrastructure/ordens_servico/` + `0004_exclusion_imposto.py`):
- `apps.py` — `AgendaConfig` (`label = "agenda"`); registra consumers no `ready()` (Fatia 3, com `# TODO Fatia 3`).
- `models.py` — `EventoAgenda`, `Recorrencia`, `RegistroNoShow`, `CapacidadeTecnico`, `Feriado`, `EventoAuditoriaAgenda`, `RegimeJornadaColaborador` (tabelas achatadas; `_choices(enum)`; `revision`). CHECK `atividade_id NOT NULL` quando `tipo='os'` (D-AGE-2 / INV-AG-ATIVIDADE-001); UNIQUE `(recorrencia_id, ocorrencia_dt)` (R10).
- `mappers.py` + `repositories.py` (`DjangoEventoAgendaRepository` implementa Protocol).
- Migrations (sequência ordens_servico):
  - `0001_initial.py` — CreateModel + índices (`(tenant_id, tecnico_id, inicia_at)` — R14).
  - `0002_rls_policies.py` — ENABLE+FORCE+4 policies (padrão v2) em TODAS as tabelas.
  - `0003_exclusion_overlap.py` — **EXCLUDE GIST** `(tenant_id WITH =, tecnico_id WITH =, tstzrange '[)' WITH &&) WHERE estado != 'cancelado'` (R1/R12 — INV-AG-OVERLAP-001); garante `btree_gist`.
  - `0004_triggers_worm.py` — `EventoAuditoriaAgenda` + `RegistroNoShow` + `RegimeJornadaColaborador` INSERT-only (block-update/delete); eventos passados imutáveis (move = update timestamps + append auditoria — D-AGE-3).
  - `0005_grants_app_user.py`.
  - `0006_seed_authz.py` — ações `agenda.{criar,mover,cancelar,bloquear,no_show,resolver_conflito,enquadrar_regime,ver}` × papéis.
  - `0007_seed_feriados.py` — catálogo nacional (D-AGE-10).
- `audit/acoes_canonicas.py` — bloco `ACOES_AGENDA` (slugs lowercase `agenda.*`) + união `ACOES_CANONICAS`. **Sem migration de CHECK** (sintático).
- `management/commands/validar_agenda.py` — drill estrutural (RLS enabled/force, ≥4 policies, EXCLUDE GIST presente, triggers WORM INSERT-only, UNIQUE recorrência, grants).

**Verificação 1b:** `pytest tests/test_agenda_schema_fatia1b.py --no-cov --reuse-db` (`transaction=True`). Cobre:
RLS ENABLE+FORCE+4 policies + isolamento cross-tenant; **EXCLUDE GIST rejeita overlap mesmo técnico/tenant E
permite mesmo horário em técnicos diferentes**; half-open (09–10 vs 10–11 OK); CHECK atividade_id; UNIQUE recorrência;
auditoria/no-show/regime INSERT-only RAISE; **drill de concorrência REAL do EXCLUDE** (2 transações/conexões
simultâneas disputando o mesmo slot → exatamente 1 commita, a outra → violação EXCLUDE/409; molde commit `88483e3`
do CR — PLAN-AGE-05). `validar_agenda` verde.

## 4. Fatia 2 — use cases + REST (NÚCLEO autossuficiente; portas com FAKE; não toca módulo fechado)

`src/application/operacao/agenda/`:
- `validar_evento.py` — dry-run pré-save (`POST /agenda/validar`): overlap + jornada (`regime` via porta) + feriado + CNH; retorna `{ok, violacoes[]}` SEM gravar (R9).
- `criar_evento.py` — valida ANTES de gravar (overlap 409 / jornada 422 / feriado-não-confirmado 422 / CNH 422); grava `EventoAgenda` + `EventoAuditoriaAgenda(criado)`; publica `agenda.evento.alocado`; jornada bloqueada → `agenda.jornada_umc.violada` + audit WORM.
- `criar_bloqueio.py` — `EventoAgenda(tipo=bloqueio)` férias/treino/atestado/outro (US-AG-004); cobre slot atribuído → alerta/obriga reatribuição.
- `mover_evento.py` / `reagendar_evento.py` — revalida tudo; eventos passados imutáveis (D-AGE-3); reagenda + grava + **enfileira** aviso (stub `NotificacaoClientePort`); publica `agenda.evento.reagendado`.
- `registrar_no_show.py` — `RegistroNoShow`(custo, cobrar_cliente) INSERT-only; cobrável → `AReceberPort.criar_titulo_manual` (FAKE na Fatia 2); publica `agenda.no_show.registrado`.
- `resolver_conflito.py` — `{manter_novo, manter_antigo, reagendar_ambos}` + razão≥30 **server-side**; publica `agenda.conflito.resolvido`.
- `materializar_recorrencia.py` — job (command) materializa janela 90d idempotente (R10).
- `feriados.py` — CRUD custom por tenant (estadual/municipal/empresa) + leitura do seed nacional.
- `sugerir_slot.py` — US-AG-006 lógica interna: RT subst (FAKE) → competência → livre 7d (horizonte fixo).
- `capacidade_dia.py` — indicador `horas_alocadas/horas_úteis` (75%/90%) com default 8h (D-AGE-11).
- `enquadrar_regime.py` — humano (RH/gerente) grava override `RegimeJornadaColaborador` (INSERT-com-vigência); **IA nunca chama isto automaticamente** (R6).

`src/infrastructure/agenda/`:
- `serializers.py` (sem `perfil`/`regime` derivado vindo do payload — server-side), `views.py` (`AgendaViewSet` + actions `validar`/`mover`/`bloquear`/`no_show`/`resolver_conflito`/`enquadrar_regime`; grade read-only multi-técnico + por `tecnico_id` self-RLS US-AG-007), `urls.py`.
- Idempotência REST (`Idempotency-Key`); **unicidade de overlap garantida pelo EXCLUDE GIST → 409** (sem advisory lock — PLAN-AGE-06, mesma escolha do CR: 1 mecanismo por garantia); `publicar_evento(outbox=True)` no `atomic`.
- `tests/fakes/agenda_fakes.py` — fakes das 6 portas (OSScheduling/ColaboradorAgenda/RTSubstituto/Maps/Notificacao/AReceber) p/ a Fatia 2 rodar isolada.

**Verificação 2:** `pytest tests/test_agenda_api_fatia2.py --no-cov --reuse-db` (`transaction=True`). Cobre: criar
evento OK (201); overlap mesmo técnico→409; jornada viola→422 `JornadaUMCViolada` (regime motorista_profissional);
`regime=nao_aplica`→não valida (aloca); feriado sem confirmar→422; `POST /validar` dry-run não grava; reagendar
revalida + enfileira aviso; no-show cobrável chama `AReceberPort` (FAKE) + publica; resolver conflito razão<30→422;
recorrência materializa 90d sem duplicar (replay); sem Idempotency-Key→400/428; cross-tenant retrieve→404;
grade multi-técnico `assertNumQueries(N)` com **N fixo p/ 5 e 20 técnicos** (prova O(1) em técnicos — PLAN-AGE-04).

## 5. Fatia 3 — integrações cross-módulo (adapters reais tocam OS/colaboradores/CR/RT FECHADOS) + INVs

> **R11:** commits desta fatia tocam módulos fechados → pré-commit pode pegar hook de invariante em código legado;
> resolver com skip oficial + justificativa. Stage seletivo; nunca commits concorrentes.

- **3a — Adapters reais das portas (infra da agenda; molde TL-AGE-04 — concreto no infra, não use case importando app de OS):**
  - `OSSchedulingAdapter` → chama `application/operacao/os/atribuir_tecnico.py` (escreve `tecnico_executor_id`+`agendada_para`; OS transita PENDENTE→AGENDADA) + lê atividade via repo/query (não SQL cru — TL-AGE-05).
  - `ColaboradorAgendaAdapter` → papel + `pendencia_cnh` via `PapelColaboradorOutputSerializer` (D-AGE-7/12); `regime_jornada(na_data)`: query override vigente `RegimeJornadaColaborador` → fallback deriva do papel → ambíguo=`indeterminado` (R6).
  - `RTSubstitutoAdapter` → predicate canônico de competência **projetado à `data=slot.inicia_at.date()`** (a porta aceita data injetável — PLAN-AGE-01/RBC-AGE-05), **atravessando `RTSubstituicao` vigente na data do slot ANTES do titular** (ADR-0068 §2.2 — RBC-AGE-04); A determinístico=412 / A incerto=warning. **Limitação documentada (PLAN-AGE-02/R15):** projeta competência+substituição, NÃO o vínculo do titular (`encerrado_em` futuro) — aceitável (agenda é CONSULTIVA; gate duro na emissão).
  - `AReceberAdapter` → monta `CriarTituloManualInput` (cliente como `ReferenciaPIIAnonimizavel` + `perfil_no_evento` **server-side**, obrigatórios no `__post_init__`) + instancia `DjangoTituloRepository()` + chama `criar_titulo_manual.executar(inp, repo=repo)` (PLAN-AGE-03/R2/D-AGE-9).
  - **Pendência P3 RESOLVIDA (revisão):** o predicate de competência aceita data injetável (`responsavel_tecnico/predicates.py` `hoje: date|None`; `predicates_os.py` `data`) — a porta passa `data=slot.inicia_at.date()`, ZERO toque em módulo fechado. **Confirmar na codificação QUAL função canônica atravessa `RTSubstituicao` (ADR-0068);** se nenhuma projetar a substituição a data futura, é débito de leitura/wiring (não código novo de domínio fechado), resolvido no início da 3a.
- **3b — Consumers do bus (fan-out — R8):** `@consumer_idempotente` registrados no `apps.py:ready()` (cada `registrar_consumer` em `try/except ValueError: pass` — re-registro do MESMO fn levanta `ValueError`, molde `ordens_servico/apps.py` — PLAN-AGE-07): `os.aberta`/`os.cancelada`/`os.reaberta`/`os.atividade_concluida`/`os.atividade_cancelada` (libera/cria/cancela slot); `colaborador.desligado` (cancela agenda futura) + `papel_atribuido`/`papel_revogado`; `tenant.rt.trocado` + **`tenant.rt.substituicao_declarada`/`tenant.rt.substituicao_encerrada`** (revisa atribuições futuras quando muda titular OU substituição — RBC-AGE-04). Perfil do envelope (R7).
- **3c — `ColaboradorReferenciadoPort.esta_referenciado` (agenda implementa p/ colaboradores):** técnico com agenda futura não é hard-deletado (D-AGE-12). Arquivo NOVO + registro; toca colaboradores só no wiring (R11).
- **3d — INVs + hooks (família INV-AG-* ao mestre):**
  - Cravar em `REGRAS-INEGOCIAVEIS.md`: INV-AG-JORNADA-UMC-001, -REGIME-001, -OVERLAP-001, -ATIVIDADE-001, -PERFIL-001, -RECORRENCIA-001, -CNH-001, -AUDIT-WORM-001, -NOSHOW-AR-001 (INV-020 já reescrito no P3).
  - Hooks (molde ordens_servico): `agenda-overlap-tenant-check.sh` (EXCLUDE com tenant_id — INV-AG-OVERLAP-001), `agenda-jornada-perfil-agnostica-check.sh` (jornada não gateada por perfil — INV-AG-JORNADA-UMC-001), `agenda-regime-server-side-check.sh` (regime nunca do payload + IA não grava override — INV-AG-REGIME-001). Registrar no `pre-commit-manifest.tsv`.

**Verificação 3:** `pytest tests/test_agenda_crossmodulo_fatia3.py tests/test_agenda_api_fatia2.py --no-cov --reuse-db`
(+ fatia2 p/ regressão) + `bash .claude/hooks/_test-runner.sh`. Cobre: criar evento `tipo=os` chama `atribuir_tecnico`
real (OS→AGENDADA); 2 atividades da mesma OS em técnicos ≠ OK (D-AGE-2/US-AG-013); RT projetado ao slot
(A determinístico=412 / A incerto=warning / B-C warning / D off — **UNHAPPY por perfil**); regime override vence
derivação + indeterminado→audit (R6); no-show cobrável cria título real em CR (D-AGE-9); consumers fan-out
(`os.concluida` libera slot SEM engolir os consumers existentes — R8); `colaborador.desligado` cancela agenda futura;
`tenant.rt.trocado` revisa; `esta_referenciado` bloqueia hard-delete; hooks novos verdes.

## 6. P8/P9 — fechamento

- **P8:** `matriz-reconciliacao.md` (US↔código↔teste; INV↔enforcement↔teste-com-ID; **reconciliação PRD↔spec**:
  `BloqueioAgenda`(PRD)=`EventoAgenda(tipo=bloqueio)`(spec); "12 ocorrências"(PRD)=janela 90d mín-visível(spec);
  `AReceber.criar`(PRD)=`criar_titulo_manual` via porta(spec); `RegistroNoShow.dispara cobrança`(PRD)=publica+chama CR).
  **ADR só se a revisão do plan indicar** — decisão D-AGE-15 já resolvida SEM ADR (tech-lead P3); reconciliação de
  nomenclatura vai na matriz, não em ADR. `STATUS-GERADO.md` (`status-projeto.sh --check`). Frontmatters → `stable`.
  Atualizar `plano-dependencia-sistema.md` (N5 — agenda destrava atribuição de técnico fail-open lazy na OS).
- **P9:** mutirão de auditores roteados (INV-RITUAL-003). Esperados sempre: seguranca, qualidade, llm-correctness,
  performance, observabilidade, idempotencia. Condicionais: supplychain (só se tocar pyproject — improvável),
  conformidade-lgpd (toca PII de colaborador/cliente — **SIM**). Produto no merge. MÉDIO+ bloqueia (INV-RITUAL-001);
  2ª passada escopada + adversarial (R5/R6 do ritual).

## 7. Revisão do plan — CONCLUÍDA (2026-06-16)

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES** (PLAN-AGE-01..08, todas incorporadas acima). Confirmou no
  código real: sequenciamento 1a→1b→2→3 sólido (núcleo 2 não importa módulo fechado — fakes reais); EXCLUDE byte-a-byte
  igual ao molde `0004_exclusion_imposto.py`; `_REGISTRY` já é fan-out (`setdefault`+`append`, `dispatch` itera todos —
  sem retrofit); `criar_titulo_manual` chamável (`executar(inp, *, repo)`); `pendencia_cnh` legível sem estender
  colaboradores. **Item 5 (D-AGE-6) RESOLVIDO:** porta RT aceita `data` projetada (zero toque em módulo fechado).
  Achados: PLAN-AGE-01 (data≠instante — ALTO), -02 (não projeta vínculo — ALTO), -03 (AReceberAdapter monta input+repo —
  MÉD), -04 (grade O(1) — MÉD), -05 (drill concorrência EXCLUDE — MÉD), -06 (remover advisory lock — MÉD), -07
  (try/except no fan-out — BAIXO), -08 (`AcaoAuditoria` reagendado/bloqueado — BAIXO).
- ✅ `consultor-rbc-iso17025` — **CONFIRMA com 2 ressalvas** (incorporadas). As 2 decisões centrais ÍNTEGRAS: jornada
  perfil-agnóstica (não regate por perfil) + RT planejar-não-emitir (gate duro na emissão). Achados: **RBC-AGE-04**
  (ALTO — projeção ao slot deve atravessar `RTSubstituicao` da ADR-0068 + consumers de substituição na 3b → R5/3a/3b),
  RBC-AGE-05 (MÉD — predicate aceita data injetável; confirmar função canônica que atravessa substituição → 3a),
  RBC-AGE-06 (BAIXO — independência cl. 6.2.5/ADR-0026 é non-goal da agenda → §8).
- ✅ `advogado-saas-regulado` — jornada/regime revisados no P2 (ADV-AGE-01..04, incorporados); não reaberto (a revisão
  do plan não mudou o enquadramento `regime_jornada`).

**Limites escalados (honestidade dos subagentes):** (1) concorrência REAL do EXCLUDE sob 20+ técnicos = drill PG
cronometrado pré-prod (não confiar só na suíte); (2) enquadramento trabalhista do `regime_jornada` = advogado OAB
humano (GATE-AGE-JORNADA-TRABALHISTA); (3) NC cl. 6.2.5/7.8 na 1ª supervisão CGCRE = consultor RBC humano credenciado.

**P3 FECHADO. Próximo passo = P4 (codar Fatia 1a — domínio puro, T-AGE-010..017; não exige Docker/PG).**

## 8. Non-goals do plan

Não construir: `MapsProvider` real (rota/TSP), roteirização, sugestão automática por skill/proximidade, integração
Google/Outlook, reserva de veículo UMC, push mobile, contraproposta/portal de cliente, capacity-planning em lote,
bot WhatsApp, envio real de notificação (omnichannel), feriado por API externa, controle de ponto (R6 — é folha/frota),
cálculo de adicional noturno/DSR em dinheiro (folha Wave C). **Não valida independência de RT cl. 6.2.5 (ADR-0026)** —
é gate de revisão/emissão (`calibracao`/`certificados`), NÃO de agendamento; a agenda no máximo dá *advisory* de "mesmo
executor", nunca bloqueia (RBC-AGE-06). GATEs: AGE-MAPS/OMNICHANNEL/PORTAL/CAPACITY/AR/FERIADO-API/JORNADA-TRABALHISTA/
PRD-UX-STATES. RAT/DPIA/minutas CONGELADOS (GATE-LGPD-RAT-CONSOLIDACAO).
