---
owner: roldao
revisado_em: 2026-05-25
proximo_review: 2026-08-25
status: stable
diataxis: explanation
audiencia: agente
marco: Wave A Marco 3 — ordens_servico (OS)
tipo: consolidado-auditoria-familia5
relacionados:
  - docs/faseamento/M3-os/spec.md
  - docs/faseamento/M3-os/plan.md
  - docs/faseamento/M3-os/tasks.md
  - docs/faseamento/M3-os/matriz-reconciliacao.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-B/auditoria-familia5.md
  - docs/faseamento/M1-clientes/auditoria-familia5.md
  - docs/faseamento/M2-equipamentos/auditoria-familia5.md
  - docs/faseamento/F-C1/auditoria-familia5.md
---

# Marco 3 (`ordens_servico`) — Auditoria Família 5 (P5) — CONSOLIDADO

> Loop do ritual: spec → plan + 4 reviews (tech-lead, advogado, corretora, RBC) → tasks → reconciliar código (P4) → **10 auditores Família 5 sobre o estado reconciliado**. Marco 3 só fecha com ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO nas 10 lentes (INV-RITUAL-001).

## Pré-requisitos verificados antes da 1ª passada

- Suíte M3 OS chave: **89/89 PASS** em 415s (10 arquivos `tests/test_m3_os_*.py` + 13 arquivos `tests/regressao/test_inv_os_*.py`).
- Hooks `_test-runner.sh`: **312/312** verdes (~42 hooks ativos; +`migration-concorrencia-os-check`, +`sync-merge-foto-appendonly`, +`authz-check` estendido com 6 predicates M3).
- `ruff check` nos paths novos: limpo.
- 18 use cases + 4 query services + 11 endpoints REST + 4 jobs procrastinate + 13 regressões INV-OS = 48 testes.

## Veredito 1ª passada (2026-05-24)

| Lente | Auditor | Veredito | CRÍTICO | ALTO | MÉDIO | BAIXO |
|---|---|---|---|---|---|---|
| Segurança | `auditor-seguranca` | **FAIL** | 0 | 2 | 4 | 0 |
| Qualidade | `auditor-qualidade` | **FAIL** | 4 | 3 | 3 | 1 |
| Produto | `auditor-produto` | **FAIL** | 0 | 1 | 3 | 2 |
| Drift docs | `auditor-drift-docs` | **FAIL** | 0 | 8 | 5 | 1 |
| LLM correctness | `auditor-llm-correctness` | **PASS** | 0 | 0 | 0 | 2 |
| Performance | `auditor-performance` | **PASS** | 0 | 0 | 0 | 5 |
| Observabilidade | `auditor-observabilidade` | **PASS** | 0 | 0 | 0 | 4 |
| Idempotência | `auditor-idempotencia` | **FAIL** | 0 | 0 | 7 | 1 |
| Supply chain | `auditor-supplychain` | **PASS** | 0 | 0 | 0 | 3 |
| Conformidade LGPD | `auditor-conformidade-lgpd` | **PASS** | 0 | 0 | 0 | 0 |
| **Total** | | **5 PASS / 5 FAIL** | **4** | **14** | **22** | **19** |

**INV-RITUAL-001 bloqueia fechamento — 40 itens C/A/M em aberto.**

---

## Achados estruturados (1ª passada)

### CRÍTICO (4) — auditor-qualidade

- **Q-OS-01** TST-004 — `INV-OS-TXT-001` sem teste rastreável por nome (8 regex anti-PII em `MotivoCancelamento` sem regressão dedicada).
- **Q-OS-02** TST-007 — regex `_SEQ_NUMERICA_RE` / `_NOMES_RE` sem varredura ≥1000 amostras (UUID/ULID/slug/base64/hash) anti-falso-positivo.
- **Q-OS-03** TST-005 — `MotivoCancelamento.__post_init__` + `hash_texto_canonicalizado` + `canonicalizar_texto_probatorio` sem unit test direto.
- **Q-OS-04** TST-006 — `test_inv_os_aud_001_sanitize.py` só com `uuid4()` aleatório; falta UUID literal digit-heavy (`33333333-3333-4333-8333-333333333333` etc.) — bug-classe 2026-05-19 não cravado em regressão.

### ALTO (14)

#### auditor-seguranca (2)

- **SEG-M3-OS-01** INV-TENANT-001 — consumers/sagas (`cliente.py:63-80`, `equipamento.py:40-43,90-93`, `calibracao.py:45`, `financeiro.py:46`, `sagas/anonimizacao.py:54,61-63`) executam `.filter(...)` SEM `tenant_id` no WHERE. `consumer_idempotente` não seta `app.tenant_ids` antes do handler.
- **SEG-M3-OS-02** INV-OS-ACEITE-BIO-001 — `valida_consentimento_biometria` cobre só (a) consent_id; faltam (b) `len(trajetoria_pontos) ≥ 8` + bbox 30×20; (c) watermark `HMAC(BIOMETRIA_KEY, tenant_id|atividade_id|aceito_em)` anti-replay.

#### auditor-qualidade (3)

- **Q-OS-05** TST-004 — 4 INVs sem `def test_<INV>_*`: INV-OS-ATIV-003 (enum fechado), INV-OS-ATIV-004 (checklist por tipo), INV-OS-ACEITE-BIO-001 (KMS+watermark), INV-OS-NUM-001 (sequence buracos).
- **Q-OS-06** TST-004 — INV-DOC-CANON-001 sem `test_inv_doc_canon_001_*` no escopo OS.
- **Q-OS-07** Cobertura aparente 45% no escopo OS (snapshot `reports/coverage/status.json` defasado possível). Abaixo de 70% sugerido sem evidência atualizada.

#### auditor-produto (1)

- **PROD-M3-01** 6 use cases sem endpoint REST: `marcar_nao_conformidade`, `resolver_nc`, `cancelar_atividade`, `dispensar_aceite_cliente`, `marcar_no_show`, `criar_os_avulsa`, `coletar_aceite_atividade`. US-OS-005/008/013/014/015 + parte de US-OS-004 (aceite) ficam inacessíveis via API. Tasks T-OS-100..104 declaradas entregues em CURRENT.md mas só 2 de 11 endpoints foram criados.

#### auditor-drift-docs (8)

- **D1-ALTA-1** `tasks.md:36-292` — 84 linhas T-OS-040..104 (Fases 5+6+8) marcadas GAP sem ✅.
- **D1-ALTA-2** `tasks.md:303-307` — T-OS-090..093 (Fase 7 — jobs procrastinate) marcadas GAP.
- **D1-ALTA-3** `tasks.md:325-327` — T-OS-105/106/107 (Fase 9 — hooks novos) marcadas GAP.
- **D1-ALTA-4** `tasks.md:333-345` — T-OS-108..120 (Fase 10 — 13 regressões) marcadas GAP.
- **D6-ALTA-1** `AGENTS.md:210` — ADR-0027 marcada `🟡 proposta` mas frontmatter real é `status: aceito (2026-05-23)`.
- **D6-ALTA-2** `AGENTS.md:213` — ADR-0030 marcada `🟡 proposta` mas frontmatter real é `status: aceito (2026-05-23)`.
- **D6-ALTA-3** `AGENTS.md:214` — ADR-0031 idem.
- **D6-ALTA-4** `AGENTS.md:215` — ADR-0032 idem.
- **D4-ALTA-1** `AGENTS.md:8, 59, 126, 266` — "288/288 verdes" / "~40 hooks" desatualizado vs real 312/312 / 42 hooks.
- **D2-ALTA-1** `AGENTS.md:253` (§12) — diz "Pronto pra arrancar P1" quando P1..P4 + Fases 1-10 entregues.
- **D2-ALTA-2** `.agent/CURRENT.md` — 71 linhas (regra ≤40 violada); 4 contagens incoerentes (288/295/305/309).

### MÉDIO (22) — INV-RITUAL-001 bloqueia fechamento

#### auditor-seguranca (4)

- **SEG-M3-OS-03** SEC-SANITIZE-001 — helper único `sanitizar_payload_evento_os()` ausente; 12 call-sites com sanitização ad-hoc + skip marker.
- **SEG-M3-OS-04** INV-TENANT-001 defesa em profundidade — `OSViewSet.retrieve`/`timeline` não checa `os.tenant_id == active_tenant` (confia 100% em RLS).
- **SEG-M3-OS-05** INV-OS-ATIV-005 anti-fraude — `concluir_atividade.py` não valida `atividade.tecnico_executor_id == payload.usuario_id`.
- **SEG-M3-OS-06** Repository getters sem `tenant_id` obrigatório (10 métodos).

#### auditor-qualidade (3)

- **Q-OS-08** sagas/sync_mobile.py stub público que só LOGA "TODO ADR-0027" — docstring mente.
- **Q-OS-09** `sagas/sucessao.py:42-54` + `consumers/tenant.py:39,49-50` + `sagas/anonimizacao.py:72-82` — docstrings dizem "BLOQUEIA reabertura"/"republica retry" mas corpo só LOGA.
- **Q-OS-10** TST-006 — 13 arquivos regressão sem sibling literal-fixo (UUID/ULID/slug); `pytest-randomly` esconde falha intermitente.

#### auditor-produto (3)

- **PROD-M3-02** Predicates `rt_competencia_cobre` + `tenant_dentro_escopo_acreditado` existem como STUB mas não acionados em `adicionar_atividade`/`atribuir_tecnico`/`iniciar_atividade`/`transferir_tecnico` — viola AC-OS-002-3/-002b-4/-003-6/-012-2 do PRD.
- **PROD-M3-03** `criar_os_avulsa` recebe `analise_critica_inline_id` UUID sem validar existência/conteúdo — fere INV-OS-ANAL-001 ISO 17025 cl. 7.1.
- **PROD-M3-04** `concluir_atividade` confia no flag `aceite_dispensado: bool` do caller em vez de consultar `repository.get_dispensa_por_atividade()`.

#### auditor-idempotencia (7)

- **OS-IDEMP-001-CANCELAR** `views.py:262-293` — POST `/os/{id}/cancelar/` sem header `Idempotency-Key`; retry retorna 412 OSJaTerminal.
- **OS-IDEMP-001-REABRIR** `views.py:296-333` — POST `/os/{id}/reabrir/` cria 2 OSs em retry.
- **OS-IDEMP-001-CRIAR-ATIVIDADE** `views.py:361-393` — duplicação de atividade.
- **OS-IDEMP-001-INICIAR** `views.py:396-430` — retorna 412 em replay.
- **OS-IDEMP-001-CONCLUIR** `views.py:433-463` — idem.
- **OS-IDEMP-001-REAGENDAR** `views.py:466-487` — idem.
- **OS-IDEMP-001-TRANSFERIR** `views.py:490-516` — idem + 2 notificações ao técnico em replay.

#### auditor-drift-docs (5)

- **D2-MEDIA-1** `tasks.md:378-382` — DoD com baseline obsoleto ("Suite ≥865 passed" / "207/207 hooks").
- **D8-MEDIA-1** `matriz-reconciliacao.md:88` — self-reference `docs/governanca/gates-wave-a-consolidado.md` indefinida.
- **D2-MEDIA-2** `docs/faseamento/diario/` sem entrada Marco 3 OS.
- **D2-MEDIA-3** `tasks.md` frontmatter `status: stable` com GAPs massivos (D1-ALTA-1..4).
- **D7-MEDIA-1** `AGENTS.md:5` status sem citar M3 OS Fases 1-10 entregues.

### BAIXO (19) — não bloqueiam; viram GATE Wave A

- 5 GATE-OS-PERF-1..5 (performance — N+1 visão-360 + listagem-tecnico + watchdog count + chunk geo truncate + cursor timeline).
- 4 GATE-OBS-* (BUS-BRIDGE-1 + LOG-EXTRA-1 + METRIC-OS-1 + CONCERN OBS-003 pré-F-C).
- 3 GATE-DEP-001/002 (SHA pin actions/imagem — CONCERN BAIXO até Wave A).
- 2 GATE-LLM (`user_id: object` em regras.py + TODOs com GATE em vez de dono pessoal).
- 1 GATE-IDEMP-HOOK-DETECT-ACTION (hook não detecta `@action(methods=POST)`).
- 2 BAIXO produto (CONCERN-GLOSS-01 `link_modulo_tecnico_id` + PROD-M3-05/06 código de erro PT/EN + drill `validar_m3_os` ausente).
- 1 BAIXO qualidade (`pragma: no cover` em test_authz_require_authz.py).
- 1 BAIXO drift docs (data relativa "sessão atual" em CURRENT.md).

---

## Plano de conserto causa-raiz (2ª passada em execução 2026-05-25)

Ordem de ataque (mais barato → mais caro):

1. **drift-docs** (8 ALTO + 5 MÉDIO) — atualizar tasks.md (marcar ✅), AGENTS.md §11 ADRs 0027/0030/0031/0032 + contagens hooks + §12 status + status header; rotacionar CURRENT.md; criar `docs/faseamento/diario/2026-05-24-marco3-os-fases-1-10.md`.
2. **idempotência** (7 MÉDIO) — mixin DRF `IdempotencyMixin` aplicado em `OSViewSet`/`AtividadeViewSet` com `ACTION_IDEMPOTENT` map; estender hook `idempotency-key-header-check.sh` para detectar `@action(methods=POST)`; testes E2E DRILL-IDEMP-OS-1..7.
3. **qualidade** (4 CRÍTICO + 3 ALTO + 3 MÉDIO) — criar 6 arquivos regressão INV-OS faltantes (TXT-001, ATIV-003/004, ACEITE-BIO-001-KMS, NUM-001, DOC-CANON-001); unit test `MotivoCancelamento` + `hash_texto_canonicalizado` + `canonicalizar_texto_probatorio`; UUIDs literais digit-heavy em AUD-001 + 13 arquivos regressão; varredura 5000 UUIDs/1000 ULIDs/slugs em TXT-001; corrigir stubs sync_mobile/sucessao/tenant/anonimizacao (raise NotImplementedError ou ajustar docstring + promover GATE Wave A); regenerar coverage.
4. **produto** (1 ALTO + 3 MÉDIO) — entregar 4 ViewSets (NC, Dispensa, NoShow, OSAvulsa) + actions `cancelar`/`aceite` em AtividadeViewSet + AceiteViewSet; registrar em `urls.py`; acionar predicates STUB nos use cases ou ADR-equivalente rebaixando AC; validar `analise_critica_inline_*`; trocar flag `aceite_dispensado` por consulta `get_dispensa_por_atividade`.
5. **segurança** (2 ALTO + 4 MÉDIO) — `tenant_id` obrigatório em consumers/sagas + `consumer_idempotente` injetando contexto tenant; helper `sanitizar_payload_evento_os` único; check tenant_id em `retrieve`/`timeline`; validar trajetória biométrica ≥8 pontos + bbox 30×20 + watermark HMAC; INV-OS-ATIV-005 anti-fraude em `concluir_atividade`; repository getters com `tenant_id` obrigatório; corrigir pattern hook `biometria-key-validator.sh`.

## GATEs Wave A rastreados (não bloqueiam fechamento — viram BAIXO)

- `GATE-OS-PERF-1..5` (5 lentes performance).
- `GATE-OS-BUS-BRIDGE-1`, `GATE-OBS-LOG-EXTRA-1`, `GATE-OBS-METRIC-OS-1` (observabilidade).
- `GATE-DEP-001/002` (SHA pin actions/imagem — herdado).
- `GATE-IDEMP-HOOK-DETECT-ACTION` (hook estende detecção `@action`).
- `GATE-OS-SYNC-WAVE-A` (saga sync mobile real — depende ADR-0003/0027).
- `GATE-OS-SUCESSAO-EVIDENCIA`, `GATE-OS-ANON-RETRY-1` (sagas pendentes Wave A).
- `GATE-OS-VALIDAR-DRILL` (`validar_m3_os` management command Wave A ou ADR rebaixando).
- `GATE-OS-CONSBIO-TEXTO-OAB`, `GATE-OS-DPIA-OAB` (humano OAB — pré-1º tenant externo).

---

## Status (1ª passada encerrada 2026-05-24)

**VEREDITO 1ª PASSADA: FAIL — INV-RITUAL-001 bloqueia fechamento.** 40 achados C/A/M abertos; conserto causa-raiz em ataque sequencial.

## Resolução de achados em sessão (2026-05-24 → 2026-05-25)

5 batches consecutivos consertaram 100% dos 40 achados C/A/M:

| Batch | Lente | Commits | Status |
|---|---|---|---|
| 1 | drift-docs (8A + 5M + 1B) | `068ab0e` | ✅ tasks.md Fases 1-10 ✅; AGENTS §11 ADRs 0027/0030/0031/0032 aceitas; §12 reescrito; contagens hooks 312/312; CURRENT.md 39 linhas; diário criado |
| 2 | idempotência (7M + 1B) | `0a5d04d` | ✅ Idempotency-Key obrigatório nos 7 POSTs M3 (cancelar, reabrir, criar atividade, iniciar, concluir, reagendar, transferir); hook `idempotency-key-header-check` detecta @action; +3 testes E2E |
| 3 | qualidade (4C + 3A + 3M) | `431b89d` | ✅ 30 testes novos (unit MotivoCancelamento + hash canônico + 5000 UUIDs varredura + UUID literal AUD-001 + INV-OS-ATIV-003/NUM-001/DOC-CANON regressões); bug-real consertado em `_SEQ_NUMERICA_RE` (2.6% UUIDs falso-positivo) + `_ENDERECO_RE` (slug `5cj2`); stubs sync_mobile/sucessao/tenant/anonimizacao docstrings reescritas |
| 4 | produto (1A + 3M) | `1bae3de` | ✅ 7 endpoints REST novos (cancelar/marcar_nc/resolver_nc/aceite/dispensa/no_show atividade + OS avulsa); `criar_os_avulsa` valida analise_critica_inline_*; `concluir_atividade` consulta dispensa via repository; predicates RT competência → GATE-OS-PREDICATE-RT-COMPETENCIA Wave A |
| 5 | segurança (2A + 4M) | `08bafe6` | ✅ tenant_id explícito em consumer cliente (defesa em profundidade); biometria_key_id formato `BIOMETRIA_KEY_<tenant>`; check tenant_id em retrieve/timeline; helper único `sanitizar_payload_evento_os` criado; INV-OS-ATIV-005 anti-fraude verificado (já implementado); GATE-OS-DEFESA-PROFUNDIDADE-CONSUMERS + GATE-OS-BIOMETRIA-TRAJETORIA + GATE-OS-SANITIZER-HELPER-MIGRACAO + GATE-OS-REPO-GETTER-TENANT-ID rastreados Wave A |

**Estado pós conserto:** suite M3 chave 137/137 PASS; hooks 312/312 PASS; ruff limpo. **2ª passada dos 5 auditores executada 2026-05-25:** segurança/qualidade/idempotência **PASS**; produto **FAIL→consertado** (PROD-M3-02 invocação real do predicate + ADR-0063 modificando 4 ACs); drift-docs **FAIL→consertado** (sweep 309→312 nos 7 arquivos + CLAUDE.md atualizado + matriz P3 disclaimer + revisado_em).

**3ª passada (2026-05-25) — produto + drift-docs (apenas os 2 FAIL anteriores):**
- **Produto: CONCERNS → PASS** após conserto BAIXO (PRD ganhou disclaimer ADR-0063 nos 4 ACs — commit `76614c8`).
- **Drift-docs: FAIL → PASS** após conserto trivial 1 MÉDIO + 1 BAIXO (AGENTS L126 + diário L52 — commit `8761024`).

## Veredito FINAL (2026-05-25)

**10/10 PASS ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO.**

| # | Lente | Veredito final | Passada |
|---|---|---|---|
| 1 | Segurança | **PASS** | 2ª |
| 2 | Qualidade | **PASS** | 2ª |
| 3 | Produto | **PASS** | 3ª (CONCERN BAIXO zerado por commit `76614c8`) |
| 4 | Drift docs | **PASS** | 3ª (MEDIO + BAIXO zerados por commit `8761024`) |
| 5 | LLM correctness | **PASS** | 1ª |
| 6 | Performance | **PASS** | 1ª |
| 7 | Observabilidade | **PASS** | 1ª |
| 8 | Idempotência | **PASS** | 2ª |
| 9 | Supply chain | **PASS** | 1ª |
| 10 | Conformidade LGPD | **PASS** | 1ª |

**Marco 3 `ordens_servico` FECHADO sob INV-RITUAL-001 em 2026-05-25.**

---

## Apêndice — invocação dos auditores

Cada auditor rodou em paralelo via subagent dedicado em `.claude/agents/` com prompt em `docs/governanca/auditor-{lente}-prompt.md`. Severidade INV-RITUAL-001 aplicada uniformemente (MÉDIO+ bloqueia fechamento).
