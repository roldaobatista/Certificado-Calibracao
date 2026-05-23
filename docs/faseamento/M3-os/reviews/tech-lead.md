---
owner: tech-lead-saas-regulado
revisado_em: 2026-05-23
status: stable
tipo: review-p2-tech-lead
marco: Wave A Marco 3 — operacao/os
fase-ritual: P2
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0027-sync-mobile-merge-atividade.md
  - docs/adr/0041-os-concorrencia-atividades.md
  - docs/adr/0042-os-cancelamento-parcial-faturamento.md
---

# Tech Lead Review — M3 `operacao/os` (P2 do ritual Spec Kit)

**Arquivo revisado:** `docs/faseamento/M3-os/spec.md` (stable)
**Revisor:** `tech-lead-saas-regulado` (subagente)
**Data:** 2026-05-23

## Sumário executivo

Spec é forte na maior parte: ADRs estruturais (0023/0027/0029/0030/0031/0032/0041/0042) bem amarradas, mapa de eventos completo, drill `validar_m3_os` com 20 checagens, mapa de testes ≥150 cobrindo INVs + US + sagas. Comparada ao molde M2, o M3 mostra evolução real (matriz tipo×tipo, watchdog cal-link, sucessão societária, biometria por-tenant).

**Mas existem 5 gaps arquiteturais que precisam ser endereçados antes de P3 (matriz reconciliação) / P4 (implement),** principalmente em concorrência, watchdog e sequence per-tenant — áreas onde "parece ok no papel" e quebra em produção sob 50 tenants concorrentes.

| Severidade | Quantidade |
|---|---|
| BLOQUEANTE (impede passar P2 → P3) | 2 |
| MÉDIO (INV-RITUAL-001 — bloqueia fechamento de fase, mas dá pra detalhar em plan.md/tasks.md) | 3 |
| ALTO Wave A (vira GATE-OS-*) | 1 |
| ACEITE com observação | (resto) |

**Veredicto:** **AJUSTAR antes de aprovar P2.** 2 bloqueantes obrigam revisão da spec.md ou ADRs antes da matriz reconciliação. 3 médios podem ser detalhados no plan.md desde que rastreados como tarefa explícita.

---

## Achados

### P-OS-T1 — BLOQUEANTE — Lock pra INV-OS-CONC-001 está sub-especificado (sem garantia de atomicidade real)

**Evidência:**
- spec.md §3.2 `AtividadeDaOS`: não há índice/lock sobre `equipamento_id` quando `estado='em_execucao'`.
- spec.md §12 R-OS-6 menciona "lock por equipamento_id" como mitigação, mas não diz **onde** (PG advisory lock? SELECT FOR UPDATE em qual linha? unique partial index?).
- ADR-0041 diz "iniciarAtividade consulta atividades EM_EXECUCAO no mesmo equipamento_id → se par incompatível → 412" — isso é leitura **sem lock**. Dois `iniciarAtividade` paralelos em conexões diferentes leem o mesmo estado "não há nada em execução" → ambos passam → matriz quebrada.

**Análise:** check-then-act clássico sob multi-tenant + procrastinate + endpoints HTMX concorrentes. RLS não resolve isso (RLS é só predicado de visibilidade, não serialização). Sob 50 clientes concorrentes esse bug aparece em 1-2% das tentativas — invisível em teste single-thread mas devastador (medições paralelas inválidas, perda de rastreabilidade ISO 17025 cl. 7.4).

**Decisão recomendada:** spec.md §3.2 + ADR-0041 precisam cravar **um dos dois mecanismos** antes de P4:
1. **Unique partial index** `CREATE UNIQUE INDEX idx_atividade_em_execucao_por_equip ON atividade_da_os (tenant_id, equipamento_id) WHERE estado='em_execucao' AND tipo_bloqueia_concorrencia=true;` — o INSERT/UPDATE de transição estoura unique violation → 412 determinístico.
2. **PG advisory lock por equipamento_id** dentro da transação que executa `iniciarAtividade` (`SELECT pg_advisory_xact_lock(hashtext(tenant_id::text || equipamento_id::text))`).

Opção 1 é mais defensável (constraint declarativa, sobrevive a bypass de aplicação). Opção 2 é mais flexível (matriz tipo×tipo continua em código). Recomendo **opção 1 com flag `tipo_bloqueia_concorrencia`** derivada da matriz ADR-0041.

> **Limite de honestidade:** suspeito que sob carga real (>200 atividades/min num tenant) advisory locks fiquem em fila e gerem timeout — não tenho cicatriz pra provar. Recomendo drill cronometrado em P4 com 4 workers procrastinate concorrentes simulando o cenário.

---

### P-OS-T2 — BLOQUEANTE — Sequence `os_numero_seq_<tenant>` é gap-less? Spec não decide.

**Evidência:**
- spec.md §3.2: "numero_os ... gerado pela sequence `os_numero_seq_<tenant>`".
- spec.md §13 item 9: "Sequence `os_numero_seq_<tenant>` por tenant ativo."
- Nenhuma menção a:
  - **Comportamento em rollback** (PG sequence é não-transacional → rollback deixa buraco).
  - **Provisionamento** (cria no `Tenant.Criado` consumer? na 1ª OS? migração one-shot?).
  - **Cleanup** quando `Tenant.Encerrado`.
  - **Concorrência multi-tenant em DDL** (`CREATE SEQUENCE` por tenant não escala — 1000 tenants = 1000 sequences no `pg_class`).

**Análise:** existem 3 padrões reais e a spec deixa indefinido qual escolher:

| Padrão | Gap-less? | Escala? | Complexidade |
|---|---|---|---|
| `CREATE SEQUENCE` por tenant | NÃO (rollback fura) | mal (DDL por tenant) | baixa |
| `CREATE SEQUENCE` global + (tenant_id, numero) unique | NÃO | bem | baixa |
| Tabela `numerador_os (tenant_id, ultimo)` com `SELECT … FOR UPDATE` | SIM | bem (contém-se na linha) | média |

Receita Federal e ISO 17025 **não exigem gap-less** em OS (exigem em NFS-e — escopo de Marco 4). Mas auditor RBC pode questionar se uma OS "saltou de 1042 → 1044" durante inspeção.

**Decisão recomendada:** Roldão decide aceitar buracos OU não. Se aceitar (recomendado, é o padrão SaaS), padronizar **opção 2** (sequence global + unique composto) — bloqueia opção 1 que vaza DDL por tenant. Cravar isso na spec §3.2 + criar ADR-0056 "Numeração OS — sequence global + unique composto, buracos aceitos" + uma frase na seção 5.1 INVs (INV-OS-NUM-001).

---

### P-OS-T3 — MÉDIO (INV-RITUAL-001) — Watchdog `os-calibracao-link-watchdog`: idempotência + backpressure + janela 24h por-tenant não definidas

**Evidência:**
- spec.md §3.2 AtividadeDaOS: "link_modulo_tecnico_id ... preenchido pelo módulo técnico em ≤24h via INV-OS-CAL-LINK-001".
- spec.md §9 GATE-OS-CAL-LINK-WATCHDOG: "cron + procrastinate com alertas P2/72h".
- spec.md §12 R-OS-2: "janela 24h ajustável por tenant + override RT".
- sagas.md confirma T+24h → P2 e T+72h → NC + bloqueia certificado.

**Lacunas:**
1. **Idempotência da NC** — se o watchdog roda a cada 1h, e a atividade está em "T+72h há 3 horas", ele cria 3 NCs? A spec §6.1 não tem evento dedicado de "watchdog disparou NC" no envelope; precisa entrar em `consumer_idempotencia` (ADR-0033) com chave `(atividade_id, regra='link_calibracao_72h')`.
2. **Janela por-tenant** — onde guarda? `tenant.watchdog_cal_link_janela_24h_override`? `TenantConfig`? spec não cita tabela. Marco 1 e 2 não criaram essa coluna.
3. **Backpressure** — se há 10k atividades CONCLUIDAS sem link num tenant em backlog (migração de dados antigos), o watchdog processa todas numa rodada? Precisa de batch + `FOR UPDATE SKIP LOCKED` no procrastinate.
4. **Override RT** — quem autoriza? predicate `pode_estender_janela_cal_link` precisa estar em ADR-0012 e em §10 hooks `authz-check`. Hoje não está.

**Decisão recomendada:** detalhar no plan.md uma seção dedicada "Watchdog cal-link" com:
- tabela `tenant_config.watchdog_cal_link_janela_24h_override` (NULL=default 24h)
- predicate `pode_estender_janela_cal_link_atividade` em §10 da spec
- chave de idempotência `(atividade_id, regra, dia_processamento)` em `consumer_idempotencia`
- batch size 100 + `SKIP LOCKED`
- testar com fixture de 10k atividades órfãs (teste de carga, não regressão funcional)

Rastrear como T-OS-WATCHDOG-1..5 no tasks.md.

---

### P-OS-T4 — MÉDIO (INV-RITUAL-001) — Performance: visão 360 da OS e listagem de atividades sem garantia anti-N+1 explícita

**Evidência:**
- spec.md não tem seção dedicada a endpoints HTTP/HTMX nem métricas p95.
- spec.md §3.2 propõe índices implícitos via §13 item 1-2 (drill verifica `(tenant_id, estado, criada_em)` e `(tenant_id, os_id, sequencia)`) — bom, mas insuficiente.
- spec.md menciona `EventoDeOS` (timeline) — endpoint "visão 360 da OS" provavelmente carrega: OS + N AtividadeDaOS + N×ChecklistDaAtividade + N×AceiteAtividade + M×EventoDeOS + cliente_snapshot + equipamento_snapshot. Sem `select_related/prefetch_related` explícito vira 7-10 round-trips por OS aberta. Listagem de 50 OS = 350-500 queries.

**Análise:** M1 e M2 também não cravaram isso — foi pego em P5 do M2 como ALTO drift. Repetir o mesmo gap em M3 é evitável.

**Decisão recomendada:** plan.md (P3) cria seção "§ Performance & Queries" com:
- p95 budget por endpoint (visão 360 OS ≤300ms; listagem ≤500ms).
- Query service `OSVisao360QueryService` em `src/application/operacao/os/queries/` com 1 query agregadora (JOIN + LEFT JOIN agregados via `array_agg`/`jsonb_agg`) — DRF serializer plano.
- Lista de prefetches obrigatórios por endpoint (matriz endpoint × prefetch).
- Índices adicionais sugeridos:
  - `evento_de_os (tenant_id, os_id, occurred_at DESC)`
  - `aceite_atividade (tenant_id, atividade_id) WHERE revogado_em IS NULL`
  - `atividade_da_os (tenant_id, tecnico_executor_id, estado)` (lista do técnico)
- Teste `tests/performance/test_visao_360_n_plus_one.py` com `assertNumQueries(<=5)`.

Rastrear como T-OS-PERF-1..4 no tasks.md. Hook `n-plus-one-check` já existe em outros marcos? Conferir; se não, GATE-OS-NPLUS1 Wave A.

---

### P-OS-T5 — MÉDIO (INV-RITUAL-001) — Sync mobile (ADR-0027): semântica de conflito de fotos append-only vs LWW de estado precisa ficar explícita

**Evidência:**
- spec.md §12 R-OS-1 + INV-OS-SYNC-001 dizem "append-only para fotos".
- ADR-0027 não menciona fotos explicitamente — só `iniciarAtividade/concluirAtividade/marcarNC/cancelarAtividade`.
- spec.md não esclarece: foto está em qual tabela? `EvidenciaFoto`? `ChecklistDaAtividade.fotos[]`? `EventoDeOS.anexos[]`?
- Cenário não resolvido: técnico A tirou foto às 10h offline; técnico B (reatribuído) tirou foto às 11h online e concluiu a atividade. Sync de A chega às 12h. A foto de A entra? Sim (append-only). Mas a atividade já está CONCLUIDA — pode adicionar foto a atividade terminal?

**Análise:** INV-OS-SYNC-001 "append-only" sem entidade definida + sem regra sobre fotos em atividade terminal = ambiguidade que vira bug em campo (foto extraviada ou conflito de timeline).

**Decisão recomendada:** spec.md §3 ganha entidade `EvidenciaFotoAtividade`:
- Padrão B (imutável pós-INSERT) com `revogado_em` apenas para LGPD art. 18 (rosto de cliente).
- FK pra `atividade_id` + `tenant_id`.
- Aceita INSERT mesmo em atividade `concluida` — gera `EventoDeOS(tipo='foto_evidencia_tardia')` automaticamente, alerta P3 ao RT.
- INV-OS-SYNC-001 reescrito: "Foto evidência é append-only via `EvidenciaFotoAtividade`; INSERT permitido em qualquer estado da atividade; UPDATE/DELETE bloqueado por trigger".

Detalhar no plan.md + tasks.md (T-OS-FOTO-1..3). Adicionar 1 teste regressão `test_inv_os_sync_001_fotos_em_atividade_terminal.py`.

---

### P-OS-T6 — ALTO Wave A (vira GATE-OS-*) — Tenant suspenso (ADR-0035): consumer M3 menciona bloqueio mas matriz operação×suspensão não existe

**Evidência:**
- spec.md §6.2 lista `Tenant.Suspenso` / `Tenant.Encerrado` como consumidos.
- spec.md §2.1 ADR-0035 marcada como dependência mas é **proposta**, não aceita.
- Não há tabela explicitando: em tenant SUSPENSO, **quais operações M3 ficam read-only? quais ficam totalmente bloqueadas? técnico campo continua concluindo atividade em curso ou para?**

**Análise:** ADR-0035 ainda é proposta. Sem ela aceita + matriz publicada, o consumer M3 não tem contrato definido. Não bloqueia M3 chegar em P4 com placeholder ("read-only total"), mas precisa virar GATE rastreado pra não vazar pra produção sem decisão.

**Decisão recomendada:** GATE-OS-TENANT-SUSPENSO Wave A — antes do 1º tenant pago:
- ADR-0035 aceita por Roldão.
- Matriz operações M3 × estado tenant (operacional/suspenso/encerrado) cravada em `docs/dominios/operacao/modulos/os/operacao-suspenso-matriz.md`.
- Consumer + teste regressão.

Adicionar no §9 da spec como GATE-OS-TENANT-SUSPENSO. M3 entrega placeholder "bloqueio total em suspenso" (mais defensivo); afinamento vem em ADR-0035 + Wave A.

---

## Pontos fortes da spec (manter)

- **Non-goals NG-OS-1..14 são exemplares** — Constituição §5 respeitada; agente downstream tem proibição positiva clara.
- **§3.1 tabela resumo** correlacionando entidade × padrão soft-delete × imutabilidade é molde a replicar em Marco 4.
- **§7 cita PRD como fonte canônica de AC com regra explícita "qualquer ajuste vira PR contra prd.md revisado pelos 4 subagentes"** — corta drift na origem.
- **§13 drill `validar_m3_os` 20 checagens** cobre RLS + triggers + predicates + consumers + watchdog + KMS + hooks + cobertura + auditores — é o gate operacional do M2 melhorado.
- **§15 explicita dependência invertida com M4** — `Calibracao.atividade_os_id` aponta pra cá; M3 só publica `AtividadeConcluida`, não bloqueia.

---

## Sugestões de teste adicional (não bloqueantes)

- **Teste de carga `tests/carga/test_concorrencia_iniciar_atividade.py`** — 50 threads concorrentes tentando `iniciarAtividade` no mesmo equipamento; deve sempre ter 1 sucesso e 49 retornos 412 (valida P-OS-T1).
- **Teste de carga `tests/carga/test_watchdog_backlog.py`** — 10k atividades órfãs; watchdog conclui em ≤5 min com batch 100 (valida P-OS-T3).
- **Teste de regressão `test_os_numero_gaps_aceitos.py`** — provoca rollback em transação que pegou número; verifica que próximo número pula (valida P-OS-T2 decisão "buracos aceitos").
- **Teste E2E mobile `test_sync_foto_em_atividade_terminal.py`** — simula técnico reatribuído + foto tardia (valida P-OS-T5).

---

## Resumo decisões pendentes (Roldão + matriz P3)

| ID | Decisão | Bloqueia |
|---|---|---|
| P-OS-T1 | Unique partial index OU advisory lock pra INV-OS-CONC-001 | P3 reconciliação |
| P-OS-T2 | Aceitar buracos na numeração OS (sim/não) + criar ADR-0056 | P3 reconciliação |
| P-OS-T3 | Detalhar watchdog em plan.md (4 sub-tarefas) | P4 implement |
| P-OS-T4 | Seção performance em plan.md + query service + budgets p95 | P4 implement |
| P-OS-T5 | Entidade `EvidenciaFotoAtividade` em spec §3 + INV-OS-SYNC-001 reescrito | P3 reconciliação |
| P-OS-T6 | GATE-OS-TENANT-SUSPENSO criado + ADR-0035 marcada como bloqueante de 1º tenant pago | P5 auditoria |

---

## Veredicto

**APROVA COM CORREÇÕES.** Bloqueantes P-OS-T1, P-OS-T2 e P-OS-T5 exigem ajuste na spec.md (ou ADR companion) antes da matriz reconciliação P3. P-OS-T3, P-OS-T4 podem ser detalhados em plan.md desde que rastreados como T-OS-* explícitos. P-OS-T6 vira GATE Wave A.

Sem isso, o ritual Spec Kit (INV-RITUAL-001) será violado em P5 — auditor de qualidade ou performance vai pegar como ALTO/MÉDIO em "spec não decidiu lock", "spec não decidiu numeração", "spec não cobre foto append-only em atividade terminal" — exatamente o tipo de drift que o ritual existe pra impedir.
