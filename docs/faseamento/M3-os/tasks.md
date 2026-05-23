---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 3 — operacao/os
tipo: matriz-spec-codigo + tarefas-causa-raiz
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M3-os/plan.md
  - docs/faseamento/M3-os/matriz-reconciliacao.md
  - docs/faseamento/M2-equipamentos/tasks.md
---

# Marco 3 (operacao/os) — Tarefas P4 (causa-raiz)

> **P4 do ritual Spec Kit (2026-05-23):** Marco 3 é **greenfield** —
> zero código no módulo `os`. Todos os AC do PRD viram T-OS-NNN aqui.
> Cada tarefa **resolve causa-raiz** (Constituição §6, nunca mascara).
> Severidade MÉDIO+ no fechamento bloqueia (INV-RITUAL-001).

## Convenções

- **GAP** → vira `T-OS-NNN` em P4 (bloqueia fechamento).
- **TRACK** → GATE Wave A (não bloqueia Marco 3 dogfooding).
- **OK** → herdado de F-A/F-B/M1/M2 (sem código novo).

---

## Matriz P3 — AC binários × T-OS-NNN

Mapeamento US ↔ tasks pra rastreabilidade. PRD `docs/dominios/operacao/modulos/os/prd.md` §6 é fonte canônica.

### US-OS-001 — Abrir OS via Orçamento aprovado

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-001-1 | GAP | T-OS-040 (consumer `Orcamento.Aprovado`) + T-OS-041 (use case `abrir_os_via_orcamento`) + T-OS-001/002 (migrations) |
| AC-OS-001-2 | GAP | T-OS-041 (validação `orcamento.itens` vazio → 400) |
| AC-OS-001-3 | GAP | T-OS-042 (idempotência POST com `Idempotency-Key` — herdado horizontal M2) |
| AC-OS-001-4 | GAP | T-OS-043 (validação cross-tenant — RLS + middleware) |
| AC-OS-001-5 | GAP | T-OS-044 (consumer consulta `equipamento.status` — INV-OS-EQP-001) |
| AC-OS-001-6 | GAP | T-OS-045 (predicate `cliente_tem_os_aberta` consumido por Clientes — INV-OS-ANON-001) |
| AC-OS-001-7 (P-OS-R2) | GAP | T-OS-046 (copia `analise_critica_id` + snapshot — INV-OS-ANAL-001) |
| AC-OS-001-8 (P-OS-R4) | GAP | T-OS-047 (FK `equipamento_recebimento_id` opcional + validação OS bancada vs campo) |

### US-OS-002 — Adicionar atividade a OS

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-002-1 | GAP | T-OS-048 (use case `adicionar_atividade`) |
| AC-OS-002-2 | GAP | T-OS-049 (estado OS terminal → 412) |
| AC-OS-002-3 (revisado P-OS-R3) | GAP | T-OS-050 (predicate `tenant_dentro_escopo_acreditado` + `tenant_tem_rt_ativo_competencia`) |
| AC-OS-002-4 | GAP | T-OS-051 (gate sequência pós-terminal) |

### US-OS-002b — Atribuir técnico + executor

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-002b-1 | GAP | T-OS-052 (use case `atribuir_tecnico_geral` + UMC INV-020) |
| AC-OS-002b-2 | GAP | T-OS-052 (validação UMC Lei 13.103) |
| AC-OS-002b-3 | GAP | T-OS-053 (RBAC executor designado — INV-OS-ATIV-005) |
| AC-OS-002b-4 (P-OS-R1) | GAP | T-OS-054 (predicate `rt_competencia_cobre` na atribuição — INV-OS-ATIV-005-EXEC-COMP) |

### US-OS-003 — Iniciar atividade no mobile

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-003-1 | GAP | T-OS-055 (use case `iniciar_atividade` + sequence) |
| AC-OS-003-2 | GAP | T-OS-056 (Idempotency-Key obrigatório) |
| AC-OS-003-3 | GAP | T-OS-056 (replay determinístico — IDEMP-001) |
| AC-OS-003-4 | GAP | T-OS-057 (gate sequência N-1 não terminal → 412) |
| AC-OS-003-5 | GAP | T-OS-058 (geo opt-in + precisão limitada INV-OS-GEO-001) |
| AC-OS-003-6 (P-OS-R1) | GAP | T-OS-054 (re-validação competência no início) |

### US-OS-004 — Concluir atividade

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-004-1 | GAP | T-OS-059 (use case `concluir_atividade` + valida checklist + aceite) |
| AC-OS-004-2 | GAP | T-OS-059 (checklist incompleto → 412 com lista de campos) |
| AC-OS-004-3 | GAP | T-OS-060 (cálculo `tipo_predominante` + transição OS → CONCLUIDA — INV-OS-ATIV-001) |
| AC-OS-004-4 | GAP | T-OS-053 (executor ≠ usuário → 403) |
| AC-OS-004-5 | GAP | T-OS-061 (watchdog `os-calibracao-link-watchdog` + janela parametrizável) |
| AC-OS-004-6 | GAP | T-OS-062 (publica `AtividadeConcluida` + portal-cliente + OmniChannel opt-in) |
| AC-OS-004-7 (P-OS-A1) | GAP | T-OS-063 (use case `coletar_aceite_atividade` + `ConsentimentoBiometriaTouch` FK 1:1) |

### US-OS-005 — NC em atividade calibração

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-005-1 | GAP | T-OS-064 (use case `marcar_nao_conformidade` + INV-OS-TXT-001) |
| AC-OS-005-2 | GAP | T-OS-064 (`nao_conformidade_global` calculado) |
| AC-OS-005-3 | GAP | T-OS-065 (use case `resolver_nc` ciclo CAPA) |
| AC-OS-005-4 | GAP | T-OS-064 (regex anti-PII estendida) |
| AC-OS-005-5 (P-OS-R5) | GAP | T-OS-065 (campos CAPA obrigatórios + AC-OS-005-5) |

### US-OS-006 — Reabrir OS

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-006-1 | GAP | T-OS-066 (use case `reabrir_os` + cria OS-filha + clone atividades) |
| AC-OS-006-2 | GAP | T-OS-066 (validação cross-tenant) |
| AC-OS-006-3 | GAP | T-OS-067 (consumer caixa-tecnico reconcilia despesas) |
| AC-OS-006-4 | GAP | T-OS-068 (consumer chamados reabre original) |
| AC-OS-006-5 | GAP | T-OS-062 (portal-cliente notifica reabertura) |
| AC-OS-006-6 | GAP | T-OS-069 (sucessão societária preserva audit — INV-OS-SUC-001) |
| AC-OS-006-7 | GAP | T-OS-069 (sem `sucessao_societaria_id` em cliente anonimizado → 412) |

### US-OS-007 — Cancelar OS

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-007-1 | GAP | T-OS-070 (use case `cancelar_os` + cascateia atividades) |
| AC-OS-007-2 | GAP | T-OS-070 (estado terminal → 412) |
| AC-OS-007-3 | GAP | T-OS-070 (atividades CONCLUIDA permanecem) |
| AC-OS-007-4 | GAP | T-OS-071 (consumer comercial/sla-breach + notificação opt-in) |

### US-OS-008 — Cancelar atividade individual

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-008-1 | GAP | T-OS-072 (use case `cancelar_atividade`) |
| AC-OS-008-2 | GAP | T-OS-060 (recalcular estado OS — última não-terminal cancela → OS terminal) |
| AC-OS-008-3 | GAP | T-OS-072 (OS sem nenhuma atividade ativa → CANCELADA não CONCLUIDA) |
| AC-OS-008-4 (P-OS-R5 + ADR-0042) | GAP | T-OS-073 (publica `OS.EscopoAlterado` + consumer financeiro/CR — INV-OS-FAT-001) |

### US-OS-009 — OS combinada (manutenção + calibração)

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-009-1 | GAP | T-OS-041 (caso especial — orçamento com 2 itens) |
| AC-OS-009-2 | GAP | T-OS-057 (gate sequência ativo) |
| AC-OS-009-3 | GAP | T-OS-057 (libera quando atividade 1 terminal) |
| AC-OS-009-4 | GAP | T-OS-074 (atividade 1 NAO_CONFORME bloqueia atividade 2 até resolver) |
| AC-OS-009-5 | GAP | T-OS-075 (visão 360 portal-cliente exibe 2 etapas + 2 aceites + 1 fatura) |

### US-OS-010 — Adicionar atividade em andamento

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-010-1 | GAP | T-OS-048 (mesmo use case `adicionar_atividade`) |
| AC-OS-010-2 | GAP | T-OS-049 (estado terminal → 412) |
| AC-OS-010-3 | GAP | T-OS-076 (perfil sem competência → 403 — INV-AUTHZ-001) |
| AC-OS-010-4 | GAP | T-OS-051 (gate sequência pos-terminal) |

### US-OS-011 — Reagendar atividade

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-011-1 | GAP | T-OS-077 (use case `reagendar_atividade`) |
| AC-OS-011-2 | GAP | T-OS-077 (estado EM_EXECUCAO → 412) |
| AC-OS-011-3 | GAP | T-OS-062 (portal-cliente notifica reagendamento) |

### US-OS-012 — Transferir técnico

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-012-1 | GAP | T-OS-078 (use case `transferir_tecnico`) |
| AC-OS-012-2 | GAP | T-OS-054 (predicate `rt_competencia_cobre` no novo técnico) |
| AC-OS-012-3 | GAP | T-OS-062 (portal-cliente notifica) |

### US-OS-013 — Dispensar aceite

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-013-1 | GAP | T-OS-079 (use case `dispensar_aceite_cliente` + entidade `DispensaAceiteAtividade`) |
| AC-OS-013-2 | GAP | T-OS-059 (`concluir_atividade` consulta dispensa ativa) |
| AC-OS-013-3 | GAP | T-OS-079 (RBAC papel gerente — 403) |
| AC-OS-013-4 (estendido) | GAP | T-OS-080 (marca certificado/fatura + link QR público) |
| AC-OS-013-5 (P-OS-A4) | GAP | T-OS-081 (`TermoDispensaAceite` canonicalizado + A3 gerente + precedente no-show/recusa) |

### US-OS-014 — No-show

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-014-1 | GAP | T-OS-082 (use case `marcar_no_show` + foto + EventoDeOS) |
| AC-OS-014-2 | GAP | T-OS-062 (portal-cliente notifica) |
| AC-OS-014-3 (P-OS-A5) | GAP | T-OS-082 (campo `foto_no_show_avisos_terceiros_acknowledged` + UX) |

### US-OS-015 — OS avulsa balcão

| AC | Estado | T-OS / nota |
|----|--------|-------------|
| AC-OS-015-1 | GAP | T-OS-083 (use case `criar_os_avulsa` + valor_unitario_snapshot — INV-CLI-PRICE-001) |
| AC-OS-015-2 | GAP | T-OS-083 (tabela preços ausente → 422) |
| AC-OS-015-3 | GAP | T-OS-084 (portal-cliente gera link `os/avulsa/{id}` com QR) |

---

## Lista de tarefas T-OS-NNN (12 fases ordenadas por dependência)

### Fase 1 — Schema + Migrations (T-OS-001..012)

- **T-OS-001** Migration `0001_initial_os.py`: tabela `os` (todos campos §3.2 spec) + RLS + index `(tenant_id, estado, criada_em)` + sequence global `os_numero_seq_global` + `UNIQUE(tenant_id, numero_os)` (INV-OS-NUM-001 + ADR-0056).
- **T-OS-002** Migration `0002_atividade_da_os.py`: tabela `atividade_da_os` + RLS + index `(tenant_id, os_id, sequencia)` + index `(tenant_id, tecnico_executor_id, estado)`.
- **T-OS-003** Migration `0003_unique_partial_index_concorrencia.py`: `CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip ON atividade_da_os (tenant_id, equipamento_id) WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true` (INV-OS-CONC-001 + ADR-0041).
- **T-OS-004** Migration `0004_aceite_atividade.py`: tabela `aceite_atividade` + RLS + trigger `aceite_atividade_anti_mutation` (audit-immutability).
- **T-OS-005** Migration `0005_consentimento_biometria_touch.py`: tabela `consentimento_biometria_touch` + RLS + trigger imutabilidade (INV-OS-CONSBIO-001).
- **T-OS-006** Migration `0006_evidencia_foto_atividade.py`: tabela `evidencia_foto_atividade` + RLS + trigger `foto_anti_mutation` (UPDATE/DELETE bloqueado; INSERT permitido em qualquer estado + gera `EventoDeOS` se atividade terminal — INV-OS-SYNC-001).
- **T-OS-007** Migration `0007_dispensa_aceite_atividade.py`: tabela `dispensa_aceite_atividade` + RLS + trigger imutabilidade.
- **T-OS-008** Migration `0008_evento_de_os.py`: tabela `evento_de_os` + RLS + trigger `evento_de_os_append_only`.
- **T-OS-009** Migration `0009_checklist_da_atividade.py`: tabela `checklist_da_atividade` + RLS.
- **T-OS-010** Migration `0010_tipo_atividade_config.py`: tabela `tipo_atividade_config` + RLS + coluna `tipo_bloqueia_concorrencia BOOLEAN` (matriz ADR-0041) + `prazo_link_calibracao_alerta_h INTEGER` + `prazo_link_calibracao_nc_dias_uteis INTEGER`.
- **T-OS-011** Migration `0011_sla_contrato_e_nao_conformidade.py`: tabelas `sla_contrato` + `nao_conformidade_atividade` (com 5 campos CAPA) + RLS.
- **T-OS-012** Migration `0012_seeds_tipo_atividade_config.py`: seed 6 tipos (calibracao, manutencao_corretiva, manutencao_preventiva, instalacao, verificacao_inmetro, vistoria) com flags `requer_competencia_rt` + `tipo_bloqueia_concorrencia` + `executa_em_campo` + matriz tipo×tipo (ADR-0041).

### Fase 2 — Domain entities + VOs (T-OS-013..022)

- **T-OS-013** `src/domain/operacao/os/__init__.py` + estrutura.
- **T-OS-014** `src/domain/operacao/os/entities.py` — entidade `OS` (sem persistência).
- **T-OS-015** entidade `AtividadeDaOS` + máquina de estados explícita.
- **T-OS-016** entidade `AceiteAtividade` + canonicalização texto (INV-DOC-CANON-001).
- **T-OS-017** entidade `ConsentimentoBiometriaTouch`.
- **T-OS-018** entidade `EvidenciaFotoAtividade`.
- **T-OS-019** entidade `DispensaAceiteAtividade` + `TermoDispensaAceite` value object.
- **T-OS-020** entidades `EventoDeOS`, `ChecklistDaAtividade`, `NaoConformidadeAtividade`.
- **T-OS-021** `src/domain/operacao/os/value_objects.py` — `EstadoOS`, `EstadoAtividade`, `TipoAtividade` enums + `NumeroOSFormatado` VO + `MotivoCancelamento` VO (≥30 chars anti-PII).
- **T-OS-022** `src/domain/operacao/os/regras.py` — regras de transição estado-máquina + validação INVs (INV-OS-ATIV-001..005).

### Fase 3 — Predicates authz + seeds (T-OS-023..028)

- **T-OS-023** `src/infrastructure/authz/predicates_os.py` — `rt_competencia_cobre(user_id, grandeza, data)`.
- **T-OS-024** predicate `tenant_dentro_escopo_acreditado(tenant_id, grandeza, faixa, data)`.
- **T-OS-025** predicate `pode_estender_janela_cal_link_atividade(user_id, atividade_id)`.
- **T-OS-026** predicate `pode_dispensar_aceite(user_id, atividade_id)` — valida precedente (no-show OU recusa).
- **T-OS-027** predicate `pode_criar_os_produtiva_balancas(user_id, tenant_id)` — consulta feature flag `OS_PRODUTIVO_DOGFOODING_BS`.
- **T-OS-028** Migration `0013_seed_authz_os.py` — 8 ações canônicas (`os.abrir`, `os.adicionar_atividade`, `os.atribuir`, `os.iniciar`, `os.concluir`, `os.marcar_nc`, `os.reabrir`, `os.cancelar`) × 5 perfis (admin_tenant, gerente_operacional, atendente, metrologista, tecnico_campo) — matriz papel × ação.

### Fase 4 — Consumers + sagas (T-OS-029..039)

- **T-OS-029** Consumer `Orcamento.Aprovado` — `src/infrastructure/operacao/os/consumers/orcamento_aprovado.py` + idempotência via `consumer_idempotencia` (ADR-0033).
- **T-OS-030** Consumer `Cliente.Anonimizado` — propaga `cliente_id=NULL` + preserva `cliente_referencia_hash`.
- **T-OS-031** Consumer `Calibracao.Iniciada` / `Calibracao.Concluida` — atualiza `link_modulo_tecnico_id`.
- **T-OS-032** Consumer `OS.Faturada` / `OS.Paga` — transição estado.
- **T-OS-033** Consumer `Tenant.Suspenso` / `Tenant.Encerrado` — bloqueia operação (ADR-0035 placeholder: read-only total).
- **T-OS-034** Consumer `Equipamento.Baixado` / `Equipamento.Descartado` — bloqueia abrir OS (INV-OS-EQP-001).
- **T-OS-035** Consumer `Acreditacao.Vencida` / `Acreditacao.Suspensa` — bloqueia novas atividades calibração/INMETRO (P-OS-R3 + GATE-RBC-ESCOPO-1).
- **T-OS-036** Consumer `EquipamentoRecebimento.Registrado` — usado pra preencher `OS.equipamento_recebimento_id`.
- **T-OS-037** Saga "Anonimização bloqueada por OS aberta" — predicate `cliente_tem_os_aberta` + watchdog retentivo quando OS conclui.
- **T-OS-038** Saga "Reabertura cross-cliente M&A" — INV-OS-SUC-001.
- **T-OS-039** Saga "Sync mobile" — LWW por atividade + append-only fotos via `EvidenciaFotoAtividade` (ADR-0027 + INV-OS-SYNC-001).

### Fase 5 — Services + use cases (T-OS-040..084)

- **T-OS-040** `services_os.py` infraestrutura — repositórios + UoW.
- **T-OS-041** Use case `abrir_os_via_orcamento` (AC-OS-001-1 ao 5).
- **T-OS-042** Idempotency-Key plug-in horizontal (reuso M2 `infrastructure/idempotencia/`).
- **T-OS-043** Validação cross-tenant + middleware RLS.
- **T-OS-044** Validação equipamento baixado/descartado.
- **T-OS-045** Predicate `cliente_tem_os_aberta` exposto pra módulo Clientes.
- **T-OS-046** Snapshot `analise_critica_id` na abertura (cl. 7.1).
- **T-OS-047** FK `equipamento_recebimento_id` + validação OS bancada vs campo (cl. 7.5).
- **T-OS-048** Use case `adicionar_atividade`.
- **T-OS-049** Validação estado OS terminal.
- **T-OS-050** Predicates `tenant_dentro_escopo_acreditado` + `tenant_tem_rt_ativo_competencia` integrados em `adicionarAtividade`.
- **T-OS-051** Gate sequência pós-terminal.
- **T-OS-052** Use case `atribuir_tecnico_geral` + agenda UMC.
- **T-OS-053** RBAC executor designado.
- **T-OS-054** Predicate `rt_competencia_cobre` na atribuição + início + transferência (INV-OS-ATIV-005-EXEC-COMP).
- **T-OS-055** Use case `iniciar_atividade`.
- **T-OS-056** Idempotência iniciar + replay determinístico.
- **T-OS-057** Gate sequência N-1.
- **T-OS-058** Captura geo opt-in com precisão limitada.
- **T-OS-059** Use case `concluir_atividade` + checklist + aceite + dispensa.
- **T-OS-060** Cálculo `tipo_predominante` + transição OS → CONCLUIDA (INV-OS-ATIV-001).
- **T-OS-061** Watchdog `os-calibracao-link-watchdog` + janela parametrizável (Roldão D-M3-2).
- **T-OS-062** Publicar eventos + portal-cliente + OmniChannel opt-in.
- **T-OS-063** Use case `coletar_aceite_atividade` + `ConsentimentoBiometriaTouch` FK 1:1 (P-OS-A1).
- **T-OS-064** Use case `marcar_nao_conformidade` + regex anti-PII estendida.
- **T-OS-065** Use case `resolver_nc` + ciclo CAPA completo (AC-OS-005-5).
- **T-OS-066** Use case `reabrir_os` + clone atividades.
- **T-OS-067** Consumer caixa-tecnico reconcilia.
- **T-OS-068** Consumer chamados reabre.
- **T-OS-069** Validação sucessão societária (INV-OS-SUC-001).
- **T-OS-070** Use case `cancelar_os` + cascateia atividades.
- **T-OS-071** Consumer `comercial/sla-breach`.
- **T-OS-072** Use case `cancelar_atividade`.
- **T-OS-073** Publica `OS.EscopoAlterado` + consumer financeiro/CR (INV-OS-FAT-001).
- **T-OS-074** Atividade NAO_CONFORME bloqueia próxima (OS combinada).
- **T-OS-075** Visão 360 OS exibe N etapas + N aceites + 1 fatura.
- **T-OS-076** Perfil sem competência ao adicionar atividade → 403.
- **T-OS-077** Use case `reagendar_atividade`.
- **T-OS-078** Use case `transferir_tecnico`.
- **T-OS-079** Use case `dispensar_aceite_cliente` + entidade `DispensaAceiteAtividade`.
- **T-OS-080** Marca certificado/fatura "aceite dispensado" + link QR público.
- **T-OS-081** `TermoDispensaAceite` canonicalizado + A3 gerente + precedente (P-OS-A4).
- **T-OS-082** Use case `marcar_no_show` + foto + ack terceiros (P-OS-A5).
- **T-OS-083** Use case `criar_os_avulsa` + valor_unitario_snapshot.
- **T-OS-084** Portal-cliente link `os/avulsa/{id}` com QR.

### Fase 6 — Query services (T-OS-085..089)

- **T-OS-085** `OSVisao360QueryService` em `src/application/operacao/os/queries/` — 1 query agregadora (JOIN + LEFT JOIN agregados via `array_agg`/`jsonb_agg`) — p95 ≤300ms (P-OS-T4).
- **T-OS-086** `OSListagemQueryService` — listagem com paginação + filtros — p95 ≤500ms.
- **T-OS-087** `OSDoTecnicoQueryService` — lista do técnico (pelo `tecnico_executor_id`).
- **T-OS-088** `OSTimelineQueryService` — eventos da OS pra portal-cliente (sanitizado INV-OS-AUD-001).
- **T-OS-089** Índices adicionais: `evento_de_os(tenant_id, os_id, occurred_at DESC)` + `aceite_atividade(tenant_id, atividade_id) WHERE revogado_em IS NULL`.

### Fase 7 — Jobs procrastinate (T-OS-090..093)

- **T-OS-090** Job periódico `os-calibracao-link-watchdog` — janela parametrizável por-tenant + idempotência via `consumer_idempotencia` + batch 100 `FOR UPDATE SKIP LOCKED` (P-OS-T3).
- **T-OS-091** Job periódico `os-geo-truncamento` — após 5a pós-conclusão, UPDATE geo_lat/long → NULL + audit `GeoTruncadoLGPD` (P-OS-A2).
- **T-OS-092** Job periódico `os-anonimizacao-retry` — retentativa quando OS aberta conclui (INV-OS-ANON-001).
- **T-OS-093** Job periódico `os-sla-breach-watcher` — detecta OS com SLA estourado (US-OS-007 saga 4).

### Fase 8 — Views/Serializers DRF (T-OS-094..104)

- **T-OS-094** `OSViewSet` POST /v1/os/ (abrirOS) + idempotency-key.
- **T-OS-095** `OSViewSet` GET /v1/os/{id}/ (visão 360).
- **T-OS-096** `OSViewSet` GET /v1/os/ (listagem com filtros).
- **T-OS-097** `OSViewSet` action `cancelar` + `reabrir`.
- **T-OS-098** `AtividadeViewSet` POST /v1/os/{os_id}/atividades/ (adicionar).
- **T-OS-099** `AtividadeViewSet` action `iniciar` + `concluir` + `cancelar` + `reagendar` + `transferir`.
- **T-OS-100** `AtividadeViewSet` action `marcarNaoConformidade` + `resolverNC`.
- **T-OS-101** `AceiteViewSet` POST /v1/atividades/{id}/aceite/ + `ConsentimentoBiometriaTouch` antes.
- **T-OS-102** `DispensaAceiteViewSet` POST /v1/atividades/{id}/dispensa-aceite/ (gerente + A3).
- **T-OS-103** `NoShowViewSet` POST /v1/atividades/{id}/no-show/ + foto + ack terceiros.
- **T-OS-104** `OSAvulsaViewSet` POST /v1/os/avulsa/ + portal-cliente link.

### Fase 9 — Hooks pré-commit novos (T-OS-105..107)

- **T-OS-105** Hook `migration-concorrencia-os-check.sh` — bloqueia migration que cria tabela `atividade_da_os` sem unique partial index pro INV-OS-CONC-001.
- **T-OS-106** Hook `sync-merge-foto-appendonly.sh` — valida que código de sync respeita INV-OS-SYNC-001 (foto via `EvidenciaFotoAtividade.objects.create`).
- **T-OS-107** Hook `authz-check.sh` estendido — predicates novos M3 registrados.

### Fase 10 — Testes regressão INV (T-OS-108..120)

13 arquivos, 1 por INV-OS, com 3 testes cada (happy + unhappy + cross-tenant):

- **T-OS-108** `tests/regressao/test_inv_os_ativ_001_terminal.py`
- **T-OS-109** `tests/regressao/test_inv_os_ativ_002_cross_tenant.py`
- **T-OS-110** `tests/regressao/test_inv_os_ativ_005_executor.py`
- **T-OS-111** `tests/regressao/test_inv_os_eqp_001_baixado.py`
- **T-OS-112** `tests/regressao/test_inv_os_anon_001_anonimizacao.py`
- **T-OS-113** `tests/regressao/test_inv_os_cal_link_001_watchdog.py`
- **T-OS-114** `tests/regressao/test_inv_os_fat_001_cancelamento_parcial.py`
- **T-OS-115** `tests/regressao/test_inv_os_conc_001_concorrencia_matriz.py`
- **T-OS-116** `tests/regressao/test_inv_os_num_001_buracos_aceitos.py`
- **T-OS-117** `tests/regressao/test_inv_os_anal_001_analise_critica.py`
- **T-OS-118** `tests/regressao/test_inv_os_consbio_001_consentimento.py`
- **T-OS-119** `tests/regressao/test_inv_os_exec_comp_001.py`
- **T-OS-120** `tests/regressao/test_inv_os_sync_001_fotos.py` + `test_inv_os_aceite_bio_001_kms.py` + `test_inv_os_geo_001_truncamento.py` + `test_inv_doc_canon_001_aceite.py`.

### Fase 11 — Testes integração US (T-OS-121..135)

15 arquivos, 1 por US (happy path + unhappy crítico):

- **T-OS-121..135** `tests/integracao/test_us_os_NNN_*.py` para US-OS-001..015.

### Fase 12 — Testes sagas + carga + drill (T-OS-136..147)

- **T-OS-136** `tests/sagas/test_saga_abrir_via_orcamento.py`.
- **T-OS-137** `tests/sagas/test_saga_cancelamento_parcial_cr.py`.
- **T-OS-138** `tests/sagas/test_saga_atividade_calibracao_link.py`.
- **T-OS-139** `tests/sagas/test_saga_anonimizacao_bloqueada.py`.
- **T-OS-140** `tests/sagas/test_saga_reabertura_sucessao.py`.
- **T-OS-141** `tests/sagas/test_saga_sync_mobile_fotos.py`.
- **T-OS-142** `tests/sagas/test_saga_vicio_concorrencia_cascateia_cert.py` (P-OS-S4 — evidência probatória pra apólice).
- **T-OS-143** `tests/carga/test_concorrencia_iniciar_atividade.py` — 50 threads.
- **T-OS-144** `tests/carga/test_watchdog_backlog.py` — 10k atividades órfãs.
- **T-OS-145** `tests/performance/test_visao_360_n_plus_one.py` — assertNumQueries ≤5.
- **T-OS-146** Drill `python manage.py validar_m3_os` — 24 verificações (§13 spec).
- **T-OS-147** Smoke E2E `tests/e2e/test_fluxo_completo_os_combinada.py` — US-OS-009 do começo ao fim.

---

## Total

- **147 tarefas** distribuídas em 12 fases.
- **Cobertura:** 100% AC binários do PRD + 17 INVs próprios + 10 sagas + drill operacional.
- **Estimativa de esforço:** Marco 2 entregou 65 T-EQP em ~2 semanas; M3 com 147 T-OS estima ~3-4 semanas em ritmo similar (com fases 1-7 paralelizáveis em até 3 frentes).

## Critério de fechamento (DoD §14 spec)

- Suite ≥865 passed.
- Drill `validar_m3_os` 24/24 PASS.
- `_test-runner.sh` 207/207 (+3 hooks novos = 210/210).
- 10 auditores Família 5 PASS ZERO C/A/M.
- **GATE-SEG-BPT-1** emitido ANTES de entrada em produção dogfooding (feature flag).

## Próximo passo (P4 implementação)

Arrancar **Fase 1 (Migrations)** após validação humana do tasks.md.
Ordem: T-OS-001 → T-OS-012 (12 migrations sequenciais).
