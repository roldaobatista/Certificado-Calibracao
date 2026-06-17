---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: agenda
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/agenda/spec.md
  - docs/faseamento/agenda/plan.md
  - docs/faseamento/agenda/tasks.md
  - docs/dominios/operacao/modulos/agenda/prd.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `agenda` (Fatias 1a–3d / P8)

> Rastreabilidade US→código→teste + INV→enforcement→teste-com-ID (TST-004) + reconciliação
> PRD↔spec. Fonte do mapeamento: **varredura do código real** (`src/{domain,application,
> infrastructure}/.../agenda/` + `src/infrastructure/colaboradores/`) em 2026-06-17.
> Frente **nível 5** (operação): calendário gerencial multi-técnico que aloca **atividades de
> OS** (ADR-0023/0051), valida **jornada UMC (Lei 13.103)** perfil-agnóstica e materializa
> recorrências. **Suíte: 173 casos verdes** (`pytest --no-cov --reuse-db`, 2026-06-17 — 69 1a
> + 28 1b + 23 2 + 24 3 cross + 29 regressão-INV). **NÃO usa ADR nova** (D-AGE-15 já resolvido
> em P3 sem ADR; emenda de spec + 1 método de porta).

## 1. Rastreabilidade US ↔ código ↔ teste

| US / entidade | Núcleo Wave A | INV | Arquivo de código (símbolo) | Status |
|---|---|---|---|---|
| US-AG-001 calendário multi-técnico | grade semanal por técnico **em 1 query agregada O(1) em técnicos** (PLAN-AGE-04) | INV-TENANT-* | `infrastructure/.../views.py` (`AgendaViewSet.list`) · `repositories.py` (`listar_por_tenant`) | ✅ |
| US-AG-002 drag valida jornada+conflito | dry-run `POST /agenda/validar` (sem gravar) + `criar_evento` valida overlap+UMC antes de gravar | INV-AG-JORNADA-UMC-001, INV-AG-OVERLAP-001 | `application/.../validar_evento.py` · `criar_evento.py` · `views.py` (`validar`/`criar`) | ✅ |
| US-AG-003 bloqueio claro 13.103 | 422 `JornadaUMCViolada{motivo, faltante_min, proximo_slot}` + audit WORM | INV-AG-JORNADA-UMC-001, INV-AG-AUDIT-WORM-001 | `domain/.../jornada.py` (`validar_jornada_umc`, `proximo_slot_valido`) · `erros.py` (`JornadaUMCViolada`) | ✅ |
| US-AG-004 bloqueio com motivo | `EventoAgenda(tipo=bloqueio)` férias/treino/atestado/outro (não valida jornada) | — | `application/.../criar_bloqueio.py` · `enums.py` (`MotivoBloqueio`) · `views.py` (`bloquear`) | ✅ |
| US-AG-005 feriados + confirmação | seed nacional (54 feriados 2025–2030) + CRUD custom; flag `confirmar_feriado` | — | `application/.../feriados.py` · migration `0007_seed_feriados` · `erros.py` (`FeriadoNaoConfirmado`) | ✅ (API externa = GATE-AGE-FERIADO-API) |
| US-AG-006 sugerir slot (chamado→OS) | RT subst→competência→livre 7d; independência cl. 6.2.5 **NÃO é critério** (advisory, nunca bloqueia — RBC-AGE-06) | INV-AG-PERFIL-001 | `application/.../sugerir_slot.py` (usa `proximo_slot_valido` jornada-aware) | ✅ |
| US-AG-007 técnico vê própria agenda | endpoint read-only por `tecnico_id` (self-RLS) | INV-TENANT-* | `views.py` (`list` filtrado por `tecnico_id`) · `repositories.py` (`listar_por_tenant`) | ✅ |
| US-AG-008 reagendar notifica cliente | reagenda + revalida + **enfileira** aviso (stub `_NotificacaoStub` Wave A) + audit | INV-AG-JORNADA-UMC-001 | `application/.../reagendar_evento.py` · `mover_evento.py` · `views.py` (`reagendar`/`mover`) | ✅ (envio real = GATE-AGE-OMNICHANNEL) |
| US-AG-009 recorrência | RRULE materializa por **janela 90d** idempotente; `UNIQUE(recorrencia_id, ocorrencia_dt)` | INV-AG-RECORRENCIA-001 | `domain/.../recorrencia.py` (`materializar_janela`) · `application/.../materializar_recorrencia.py` | ✅ |
| US-AG-010 capacidade do dia | indicador `horas_alocadas/horas_úteis` (75% atenção / 90% crítico); default 8h | — | `application/.../capacidade_dia.py` · `entities.py` (`CapacidadeTecnico`) · migration `0008` (defaults) | ✅ |
| US-AG-011 resolver conflito | `{manter_novo, manter_antigo, reagendar_ambos}` + razão ≥30 **server-side** | INV-AG-OVERLAP-001 | `application/.../resolver_conflito.py` (`OpcaoConflito`) · `erros.py` (`JustificativaConflitoCurta`) | ✅ |
| US-AG-012 no-show + custo | `RegistroNoShow` INSERT-only; cobrável→`AReceberPort.criar_titulo_manual` (CR real) | INV-AG-NOSHOW-AR-001, INV-AG-AUDIT-WORM-001 | `application/.../registrar_no_show.py` · `infrastructure/.../adapters.py` (`AReceberAdapter`) | ✅ (origem título = GATE-AGE-NO-SHOW-AGENDA) |
| US-AG-013 agendar ATIVIDADE | `atividade_id` NOT NULL quando `tipo=os`; 2 atividades da mesma OS em técnicos ≠ ok; **criar evento tipo=os transita a OS PENDENTE→AGENDADA** | INV-AG-ATIVIDADE-001 | `domain/.../entities.py` (`EventoAgenda.__post_init__`) · CHECK migration `0001` · `criar_evento.py` (passo 5.5 chama `os_port.atribuir_tecnico`) · `adapters.py` (`OSSchedulingAdapter.atribuir_tecnico` + ACL `ErroAtribuirTecnico→ConflitoAgenda`) | ✅ **wired** (GATE-AGE-OS-WIRING FECHADO 2026-06-17) — teste integração `test_criar_evento_os_transita_atividade_para_agendada` (OS+atividade reais → AGENDADA) |
| US-AG-014 RT substituto perfil-aware | `criar_evento` chama `rt_port` projetado à `data=slot.inicia_at.date()`: perfil A + ausência determinística → **412 `SemRTNoSlot` (fail-closed)**; B/C → aviso não-bloqueante; D → off; grandeza vazia → fail-open (AC-OS-002-3) | INV-AG-PERFIL-001 | `application/.../criar_evento.py` (passo 4.5) · `infrastructure/.../adapters.py` (`RTSubstitutoAdapter` + `OSSchedulingAdapter.obter_atividade` expõe grandeza) · `views.py` (`except SemRTNoSlot → 412`) | ✅ **wired** (decisão Roldão 2026-06-17 — GATE-AGE-RT-WIRING FECHADO). Gate DURO de NC continua na emissão (D-AGE-6) |
| D-AGE-15 regime de jornada (override na agenda) | `regime_jornada` resolvido server-side (override humano→papel→indeterminado); IA nunca grava | INV-AG-REGIME-001 | `infrastructure/.../adapters.py` (`ColaboradorAgendaAdapter.regime_jornada`) · `application/.../enquadrar_regime.py` · `domain/.../value_objects.py` (`RegimeJornadaResolvido`) | ✅ (enquadramento OAB = GATE-AGE-JORNADA-TRABALHISTA) |
| `ColaboradorReferenciadoPort` (implementa p/ colaboradores) | técnico com agenda futura responde "referenciado" (não hard-deletar) | INV-AG-AUDIT-WORM-001 | `infrastructure/.../referenciado.py` (`AgendaColaboradorReferenciadoAdapter`) · `repositories.py` (`tem_agenda_futura`) · wiring `apps.py:ready()` | ✅ adapter pronto (consumo end-to-end = GATE-AGE-COLABORADOR-REFERENCIADO) |

## 2. INV ↔ enforcement real ↔ teste nomeado (TST-004)

> Cada INV-AG-* tem ≥1 teste de regressão cujo **nome cita o ID** em
> `tests/regressao/test_inv_ag_agenda.py` (29 casos — fecha TST-004), além dos testes
> comportamentais por fatia. Texto canônico + base normativa: `REGRAS-INEGOCIAVEIS.md §INV-AG-*`.

| INV | Enforcement real | Teste comportamental (fatia) | Teste-com-ID (regressão) |
|---|---|---|---|
| INV-AG-JORNADA-UMC-001 | `validar_jornada_umc` (domínio puro, **perfil-agnóstica**) chamada ANTES de gravar no `criar_evento.py`; hook `agenda-jornada-perfil-agnostica-check.sh` (bloqueia gate por A/B/C/D) | `test_agenda_dominio_fatia1a.py` (5 regras por regime) · `test_agenda_api_fatia2.py` (motorista viola→422) | `test_inv_ag_jornada_umc_001_*` (4: hook BLOCK/PASS + domínio sem-param-perfil + clt_geral-sem-R2) |
| INV-AG-REGIME-001 | `ColaboradorAgendaAdapter.regime_jornada` server-side (override→papel→indeterminado); hook `agenda-regime-server-side-check.sh` (bloqueia regime do payload + `create` fora de `enquadrar_regime`); WORM trigger (0004) | `test_agenda_crossmodulo_fatia3.py` (override vence + indeterminado→audit) | `test_inv_ag_regime_001_*` (5: hook BLOCK payload/BLOCK create/PASS server-side + papel_atribuido-não-cria + WORM-update-raise) |
| INV-AG-OVERLAP-001 | EXCLUDE GIST `(tenant_id WITH =, tecnico_id WITH =, tstzrange '[)' WITH &&) WHERE estado != cancelado` (migration 0003); hook `agenda-overlap-tenant-check.sh`; 1 mecanismo (sem advisory lock) | `test_agenda_schema_fatia1b.py` (overlap mesmo téc→rejeita; téc≠ ok; half-open; **drill concorrência real**) · `..._api_fatia2.py` (409) | `test_inv_ag_overlap_001_*` (2: hook BLOCK sem-tenant / PASS com-tenant) |
| INV-AG-ATIVIDADE-001 | `EventoAgenda.__post_init__` levanta `AtividadeObrigatoria`; CHECK `chk_agenda_evento_atividade_obrigatoria_quando_os` (0001) | `test_agenda_schema_fatia1b.py` (CHECK atividade_id) · `..._crossmodulo_fatia3.py` (2 atividades mesma OS téc≠ ok) | `test_inv_ag_atividade_001_*` (3: tipo=os sem→raise / com→ok / tipo=bloqueio sem→ok) |
| INV-AG-PERFIL-001 | **perfil server-side (nunca do payload) — ENFORCED** (serializers não aceitam perfil). **RT competence — ENFORCED:** `criar_evento` (passo 4.5) chama `rt_port` projetado à `data=slot`; perfil A determinístico → 412 `SemRTNoSlot`; B/C → aviso; D → off; grandeza vazia → fail-open | `criar_evento.py` passo 4.5 · `RTSubstitutoAdapter` · `views.py` except 412 | `test_inv_ag_perfil_001_*` (WORM: regime-delete + auditoria-update) + **`TestINVAGPerfil001RTSlot`** (4: A sem RT→412 / A com RT→cria / grandeza vazia→fail-open / C sem RT→aviso) |
| INV-AG-RECORRENCIA-001 | `UNIQUE(recorrencia_id, ocorrencia_dt)` parcial (0001); `materializar_janela` determinística (RFC 5545); job re-roda sem duplicar | `test_agenda_schema_fatia1b.py` (UNIQUE recorrência) · `..._api_fatia2.py` (replay sem duplicar) | `test_inv_ag_recorrencia_001_*` (6: janela inválida ×2 + rrule ok/inválida + duração + sobrepõe-half-open) |
| INV-AG-CNH-001 | `criar_evento.py` valida `pendencia_cnh` antes de gravar; `ColaboradorAgendaAdapter.pendencia_cnh` (zero extensão de colaboradores — D-AGE-12) | `test_agenda_crossmodulo_fatia3.py` (motorista com `pendencia_cnh=True`→422) | `test_inv_ag_cnh_001_*` (2: pendência→True / sem→False) |
| INV-AG-AUDIT-WORM-001 | triggers `*_block_update_trg` + `*_block_delete_trg` em `EventoAuditoriaAgenda`/`RegistroNoShow`/`RegimeJornadaColaborador` (0004); drill `validar_agenda` | `test_agenda_schema_fatia1b.py` (INSERT-only RAISE) | `test_inv_ag_audit_worm_001_*` (4: adapter-registrado-no-boot + esta_referenciado com/sem agenda + cancelado-não-bloqueia) |
| INV-AG-NOSHOW-AR-001 | `AReceberAdapter.criar_titulo_manual` chamado DENTRO do `atomic` do `registrar_no_show`; `perfil_no_evento` server-side; `cliente` `ReferenciaPIIAnonimizavel` | `test_agenda_crossmodulo_fatia3.py` (no-show cobrável cria título real em CR) | `test_inv_ag_noshow_ar001_consumer_sentinela_gate_aberto` (1: sentinela GATE-AGE-NO-SHOW-AGENDA) |

> **Reusadas (transversais):** INV-TENANT-001..003 + INV-008 (RLS v2 ENABLE+FORCE — migration 0002;
> cross-tenant `None`/404 anti-oráculo), INV-BUS-001 (`@consumer_idempotente` fan-out — `os.*`/
> `colaborador.*`/`tenant.rt.trocado`), INV-001/ADR-0031 Padrão B (WORM), INV-020 (jornada Lei
> 13.103 — incorporada por INV-AG-JORNADA-UMC-001), INV-ANON-* (`cliente`/PII via hash no `AReceberAdapter`).

## 3. Reconciliação PRD ↔ spec

| Conceito do PRD | Destino canônico (código) | Estado |
|---|---|---|
| `BloqueioAgenda` (entidade separada no PRD) | `EventoAgenda(tipo=bloqueio)` + `MotivoBloqueio` (não há tabela própria — D-AGE-3) | ✅ unificado |
| recorrência "12 ocorrências" (PRD) | **janela 90d idempotente** (`materializar_janela`); "12" = mínimo visível, não o limite (D-AGE-8/ADR-0033) | ✅ reconciliado |
| `AReceber.criar` (no-show cobrável, PRD) | `criar_titulo_manual` (use case público de CR) via porta `AReceberPort` — **agenda não cria consumer dentro de CR fechado** (D-AGE-9/TL-AGE-02) | ✅ via porta |
| jornada gateada por perfil A/B/C/D (PRD §4/AC-AG-002-2 — **ERRADO**) | jornada **perfil-AGNÓSTICA** (ordem pública trabalhista ≠ perfil metrológico); PRD corrigido na ação P3 | ✅ PRD corrigido (D-AGE-4) |
| `is_tecnico_campo` como campo de colaborador (implícito no PRD) | **DERIVADO do papel** (`TECNICO`/`MOTORISTA_UMC`) via porta — zero campo novo em colaboradores (D-AGE-12) | ✅ derivado |
| regime de jornada (não previsto no PRD) | `RegimeJornadaColaborador` na **própria agenda** (override humano INSERT-com-vigência) — colaboradores intacto (D-AGE-15) | ✅ sem ADR |

## 4. Migrations da frente (`src/infrastructure/agenda/migrations/`)

| # | O que faz |
|---|---|
| 0001 | CreateModel (7 tabelas) + CHECK `atividade_id` (tipo=os) + UNIQUE parcial recorrência + UNIQUE parcial feriado nacional + índices |
| 0002 | RLS ENABLE+FORCE + 4 policies v2 (todas as tabelas; SELECT inclui `tenant_id IS NULL` p/ feriado nacional) |
| 0003 | **EXCLUDE GIST** overlap por técnico (`tenant_id` 1ª coluna, `tstzrange '[)'`, `WHERE estado != cancelado`); `btree_gist` |
| 0004 | Triggers WORM INSERT-only: `EventoAuditoriaAgenda` + `RegistroNoShow` + `RegimeJornadaColaborador` (block-update/delete) |
| 0005 | GRANTs `app_user` (7 tabelas) |
| 0006 | Seed authz — 9 ações `agenda.*` × papéis (`enquadrar_regime` restrito a admin/gerente) |
| 0007 | Seed feriados nacionais (catálogo BR 2025–2030; `tenant=None`; ON CONFLICT DO NOTHING) |
| 0008 | `AlterField` só de `help_text`/defaults-Python (**NO-OP no banco** — Django não gera DDL); squash no 0001 = housekeeping diferido (greenfield) |

## 5. GATEs abertos e débitos rastreados (P9 / Wave B)

**GATEs de feature diferida (bloqueio de escopo, não de qualidade):**
- **GATE-AGE-JORNADA-TRABALHISTA** (🔴 advogado OAB humano pré-produção — enquadramento individual + tabela final + convenção coletiva MT).
- **GATE-AGE-RTSUBSTITUICAO-FORMAL** — modelo `RTSubstituicao` (ADR-0068 §2.2) não existe Wave A; `RTSubstitutoAdapter` projeta só competência do titular vigente à data; gate duro de NC vive na emissão.
- **GATE-AGE-RT-WIRING** — ✅ **FECHADO (Roldão decidiu wirar no Wave A — 2026-06-17).** `criar_evento` (passo 4.5) consome `rt_port` projetado à data do slot: perfil A determinístico → 412 `SemRTNoSlot` (fail-closed); B/C → aviso; D → off; grandeza vazia → fail-open. `validar_evento` teve o `rt_port` órfão removido (dry-run = overlap+jornada+CNH; RT é gate de criação). Cobertura: `TestINVAGPerfil001RTSlot` (4 testes).
- **GATE-AGE-OS-WIRING** — ✅ **FECHADO (Roldão decidiu wirar no Wave A — 2026-06-17).** `criar_evento` (passo 5.5) chama `os_port.atribuir_tecnico` para tipo=os → atividade PENDENTE→AGENDADA + OS RASCUNHO→AGENDADA (quando todas as atividades estão AGENDADA+). ACL: `OSSchedulingAdapter` traduz `ErroAtribuirTecnico` (estado incompatível / executor sem competência) → `ConflitoAgenda` (409), nunca vaza exceção da OS ao domínio da agenda. Tudo no `atomic` do caller → rollback total se falhar. Teste de integração real cobre OS→AGENDADA.
- **GATE-AGE-NO-SHOW-AGENDA** — `OrigemTitulo.NO_SHOW_AGENDA` não existe no CR fechado; `AReceberAdapter` usa `MANUAL` + metadata (Wave B adiciona a origem).
- **GATE-AGE-COLABORADOR-REFERENCIADO** — `_referenciado_agenda_port` registrado mas não consumido (destroy de colaboradores hoje é desligamento lógico, não hard-delete físico); conectar quando houver hard-delete físico (fail-open lazy ADR-0066).
- **GATE-AGE-OMNICHANNEL / PORTAL / MAPS / CAPACITY / FERIADO-API** — features Wave B (notificação real, contraproposta de cliente, rota real, capacity-planning, feriado por API externa).

**Débitos técnicos (refinamento — NÃO bloqueiam Wave A):**
- **R4 (DSR):** valida total ≥35h livres em 6 dias, não o BLOCO contínuo de 35h (mais permissivo) — refinar com OAB.
- **R1 (inter-jornada):** mede entre dias-calendário distintos; turnos cruzando meia-noite são aproximação (documentado).
- Consumers transicionam via `update` direto (espelham evento externo da OS — auditoria vive na OS); reconciliar com a máquina de estados D-AGE-3 quando a saga sair do stub.
- `ColaboradorAgendaAdapter` lê ORM de colaboradores direto (acoplamento de leitura — não estende; aceitável).
- Squash do `0008` no `0001` (housekeeping greenfield).

## 8. P9 — ritual de auditores roteados (INV-RITUAL-003)

> Esperados sempre: segurança · qualidade · llm-correctness · performance · observabilidade ·
> idempotência. Condicionais: conformidade-lgpd (toca PII via `AReceberAdapter` hash cliente —
> SIM); supplychain (não tocou pyproject/lock/Dockerfile — N/A). Produto no merge. MÉDIO+
> bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial (R5/R6).

| Passada | Resultado |
|---|---|
| **1ª** | **conformidade-lgpd PASS** (0 MÉDIO+; agenda referencia cliente por UUID opaco + hash no boundary). **6 MÉDIO** nos demais (bloqueiam — INV-RITUAL-001): (A) segurança — `registrar_no_show` `except Exception` engolia falha de cobrança → no-show cobrável commitava sem título; (B) qualidade — teste sentinela `noshow_ar001` com `return` precoce passava sem barreira (TST-002) + docstring mentindo; (C) llm-correctness — `recorrencia` WEEKLY `COUNT+INTERVAL` retornava menos ocorrências + `sugerir_slot` docstring/`rt_port` órfão; (D) performance — `list` unbounded (DoS F-C3); (E) observabilidade — tentativa de jornada bloqueada sem trilha WORM; (F) idempotência — TOCTOU no-show sem `UniqueConstraint(tenant, evento_id)` (cobrança dupla). CONCERN BAIXO diversos. **Verificação adversarial (R6) confirmou os 6 reais.** |
| **conserto causa-raiz** | (A) removido `except Exception` → falha de cobrança PROPAGA (atomicidade); + rejeita cobrança sem `cliente_id`/`custo>0` (eliminado cliente-fantasma `UUID(int=0)`). (B) sentinela substituído por `TestINVAGNoShowAR001` (3 testes que exercem a barreira real: 1 chamada / falha propaga / sem cliente_id→erro) + docstring honesta. (C) ramo WEEKLY reescrito (filtro INTERVAL antes de truncar COUNT) + teste `test_semanal_count_com_interval_2_*`; `_parse_rrule`→TypedDict (eliminou 5 `type: ignore`); `sugerir_slot` docstring corrigida + `rt_port` órfão removido. (D) `list` com janela default 31d + teto `LIMIT 2000` (`{resultados, truncado}`) + teste de teto. (E) helper `_auditar_jornada_bloqueada` grava `EventoAuditoriaAgenda(BLOQUEADO)` nos 3 excepts (fail-loud; sobrevive ao savepoint sob ATOMIC_REQUESTS) + teste. (F) `UniqueConstraint(tenant, evento_id)` (migration `0009`, aplicada dev+test_afere) + captura `IntegrityError`→`TransicaoEventoProibida` (409) + teste DB. **179 testes verdes** (era 173). ruff+mypy limpos nos arquivos tocados. |
| **2ª (escopada R5 + adversarial R6)** | **6 PASS** — todos os 6 MÉDIO RESOLVIDOS na causa-raiz, sem mascaramento, **sem novo MÉDIO+**. Qualidade provou por **mutação** que o teste falha se a barreira sair. Observabilidade confirmou tecnicamente que a trilha no `except` sobrevive ao rollback do savepoint (raise de jornada ocorre antes de qualquer SQL de escrita → transação-raiz limpa). Idempotência verificou a `UniqueConstraint` no banco de teste real. **CONCERN BAIXO rastreados (não bloqueiam):** falta teste HTTP end-to-end do `list` bounded e do 412→trilha (cobertura via repo/helper isolado); divergência `limite` adapter↔Protocol; `rt_port` órfão em `criar_evento.py`. **Módulo `agenda` FECHADO — Wave A.** |

> **Pós-fechamento (2026-06-17) — GATE-AGE-RT-WIRING resolvido + descoberta GATE-AGE-OS-WIRING:** investigando o `rt_port` órfão, confirmei que **tanto `rt_port` quanto `os_port` eram dead params** em `criar_evento` — o adapter de RT E o `atribuir_tecnico` (OS→AGENDADA) existiam mas não eram invocados. Roldão decidiu **wirar o RT 412 no Wave A**: implementado o passo 4.5 (perfil A det.→412/B-C→aviso/D→off/grandeza vazia→fail-open) + `OSSchedulingAdapter.obter_atividade` expõe grandeza + view `except SemRTNoSlot→412` + 4 testes (`TestINVAGPerfil001RTSlot`). `rt_port` órfão removido de `validar_evento`. **GATE-AGE-OS-WIRING também resolvido** (Roldão decidiu wirar): `criar_evento` passo 5.5 chama `os_port.atribuir_tecnico` (tipo=os → OS PENDENTE→AGENDADA), com ACL `ErroAtribuirTecnico→ConflitoAgenda` no adapter; teste de integração real prova OS→AGENDADA. **184 testes verdes.**
