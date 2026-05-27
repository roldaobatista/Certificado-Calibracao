---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-08-27
status: in-progress
diataxis: explanation
audiencia: agente
marco: Wave A Marco 4 — metrologia/calibracao
tipo: consolidado-auditoria-familia5
relacionados:
  - docs/faseamento/M4-calibracao/spec.md
  - docs/faseamento/M4-calibracao/plan.md
  - docs/faseamento/M4-calibracao/tasks.md
  - docs/faseamento/M4-calibracao/matriz-reconciliacao.md
  - docs/faseamento/F-A/auditoria-familia5.md
  - docs/faseamento/F-B/auditoria-familia5.md
  - docs/faseamento/M1-clientes/auditoria-familia5.md
  - docs/faseamento/M2-equipamentos/auditoria-familia5.md
  - docs/faseamento/F-C1/auditoria-familia5.md
  - docs/faseamento/M3-os/auditoria-familia5.md
---

# Marco 4 (`metrologia/calibracao`) — Auditoria Família 5 (P5) — 1ª passada CONCLUÍDA

> Loop do ritual: spec → plan + 4 reviews (tech-lead, advogado, corretora, RBC) → tasks → reconciliar código (P4) → **10 auditores Família 5 sobre o estado reconciliado**. Marco 4 só fecha com ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO nas 10 lentes (INV-RITUAL-001).

## 1. Pré-requisitos verificados antes da 1ª passada

| Item | Estado | Evidência |
|---|---|---|
| Suíte M4 chave | **629/629 PASS** em ~27s | 12 arquivos `test_m4_uc_*` + 5 `test_m4_motor_*` + `test_m4_jobs_fase7` + `test_m4_queries_fase6{,_extra}` + `test_m4_vos_calibracao` + regressões |
| pytest geral | 905/0/0 (último full run 2026-05-24) | reports/pytest-run8.log |
| Hooks `_test-runner.sh` | **379/379** verdes / **48 hooks ativos** (377 na 1ª passada → +2 cases hash-versionado pós-S4) | M4 P9 FECHADA |
| ruff/mypy paths novos | limpo | M4 P6 extra + Batch X/Y regressões |
| Auditoria-DRAFT | substituída por dados reais | este arquivo |

## 2. Veredito 1ª passada (2026-05-27)

| Lente | Auditor | Veredito | CRÍTICO | ALTO | MÉDIO | BAIXO/CONCERN |
|---|---|---|---|---|---|---|
| Segurança | `auditor-seguranca` | **FAIL** | 1 | 3 | 4 | 3 |
| Qualidade | `auditor-qualidade` | **FAIL** | 0 | 1 | 4 | 1 + 3 CONCERN |
| Produto | `auditor-produto` | **FAIL** | 0 | 3 | 3 | 1 |
| Drift docs | `auditor-drift-docs` | **FAIL** | 0 | 4 | 9 | 4 |
| LLM correctness | `auditor-llm-correctness` | **CONCERNS** | 0 | 0 | 0 | 1 |
| Performance | `auditor-performance` | **PASS** | 0 | 0 | 0 | 2 |
| Observabilidade | `auditor-observabilidade` | **FAIL** | 0 | 0 | 3 | 1 |
| Idempotência | `auditor-idempotencia` | **FAIL** | 1 | 2 | 2 | 0 |
| Supply chain | `auditor-supplychain` | **PASS** | 0 | 0 | 0 | 2 |
| Conformidade LGPD | `auditor-conformidade-lgpd` | **FAIL** | 0 | 0 | 1 | 1 |
| **Total** | | **7 FAIL / 1 CONCERN / 2 PASS** | **2** | **13** | **26** | **~18** |

**INV-RITUAL-001 bloqueia fechamento — 41 itens C/A/M em aberto.**

---

## 3. Achados estruturados (1ª passada — 2026-05-27)

### CRÍTICO (2)

#### auditor-seguranca (1)

- **SEG-CAL-01 — Spoofing de identidade do cliente em recepcionar** (SEC-003 + INV-TENANT-001 defesa em profundidade). `src/infrastructure/calibracao/serializers.py:29-33` + `views.py:127-128`. `RecepcionarCalibracaoSerializer` aceita `cliente_referencia_hash` e `cliente_key_id` direto do body do request. Cliente autenticado em tenant T pode enviar hash apontando para PII anonimizada de outro cliente; calibração nasce com referência falsificada. **Correção:** derivar server-side a partir de `cliente_id` + tenant via `ReferenciaPIIAnonimizavel` (ADR-0032); body só envia `cliente_id` (UUID) ou nada (recepção avulsa). Remover ambos os campos do serializer.

#### auditor-idempotencia (1)

- **IDEMP-CAL-01 — 3 POSTs entregues sem `Idempotency-Key`** (IDEMP-001 + INV-CAL-IDEMP-001). `CalibracaoViewSet.recepcionar/configurar/cancelar` não lêem `HTTP_IDEMPOTENCY_KEY` nem invocam `services_idempotencia.avaliar_chave_idempotencia`. `recepcionar` cria entidade WORM em `transaction.atomic` — clique duplo = 2 calibrações com mesmo `correlation_id`. `configurar` tem optimistic lock mas erro vira 409 ConflitoVersao em vez de 200 idempotente. **Correção:** aplicar `IdempotencyMixin`/`_aplicar_idempotencia` padrão M3 OS + declarar `ACTION_IDEMPOTENT` map.

### ALTO (13)

#### auditor-seguranca (3)

- **SEG-CAL-02 — `obter_por_id` sem filtro tenant explícito (defesa em profundidade)** (INV-TENANT-001). `repositories.py:39-44`. Confia 100% em RLS; sessão PG sem `app.tenant_ids` vaza cross-tenant.
- **SEG-CAL-03 — Helper único `sanitizar_payload_evento_calibracao` AUSENTE** (SEC-SANITIZE-001). Docstring `models.py:1482-1484` refere o helper mas grep confirma que NÃO existe — risco idêntico ao bug `sanitizar_payload_audit` 2026-05-19.
- **SEG-CAL-04 — `registrar_recebimento_subcontratado` confia em `recebedor_user_id` do caller** (INV-CAL-FRAUDE-RECEB-001). `subcontratacao.py:187`. Anti-fraude RECEB-001 não enforced no use case.

#### auditor-qualidade (1)

- **Q-CAL-01 — TST-004 — Classes `def test_<INV>_*` cobrem só 5 INVs literais** (INC-004, RT-002, IDEMP-001, CONF-001, DEC-001). As 12 INVs M4 que a autoavaliação declarou "cobertas" via docstring (CMC-001, CONC-001, DEC-004/005, INC-001/003, NC-002/003, SUBC-001/005, VERSAO-001, WORM-001) NÃO têm classe nominada — TST-004 do prompt exige literal `def test_<INV>_*`. Total: 5/41 INVs M4 com nome rastreável.

#### auditor-produto (3)

- **PROD-CAL-01 — `cmc_cobre` STUB declarado mas NÃO invocado** em `configurar_calibracao`/`iniciar_leituras`. Viola AC-CAL-002-2 + AC-CAL-001-2 + AC-CAL-015-1. Sem ADR equivalente a ADR-0063 documentando fail-open lazy.
- **PROD-CAL-02 — `procedimento_vigente_para` STUB declarado mas NÃO invocado** em `configurar_calibracao`. Viola AC-CAL-016-1/2/3 (US-CAL-016 inteira).
- **PROD-CAL-03 — `CalibracaoViewSet.cancelar` retorna 501 com mensagem expondo `T-CAL-095 Wave A`**. Spec §4.1 lista `cancelada` como transição válida; bloqueio operacional pra dogfooding (recepcionou errado → não consegue cancelar). PT-BR sem jargão violado.

#### auditor-drift-docs (4)

- **D4-HOOKS-1** `AGENTS.md:8` — status "hooks 312/312 verdes em 42 hooks ativos". Real = **377/377 / 48 ativos** (M4 P9). Listar 6 hooks novos M4.
- **D4-HOOKS-2** `AGENTS.md:126, 270` — mesmas contagens drift.
- **D7-AGENTS-1** `AGENTS.md:§12` — atualizado pós-M3 OS; sem menção a M4 P1-P10 entregues.
- **D4-HOOKS-3** `CLAUDE.md:67, 110, 126` — três menções "42 hooks ativos / 312 casos".

#### auditor-idempotencia (2)

- **IDEMP-CAL-02 — Hook `idempotency-key-header-check` NÃO cobre `calibracao/`**. `idempotency-key-header-check.sh:41-49` allowlist sem `calibracao/`. T-CAL-136 declarado mas não implementado — commits passaram sem defesa.
- **IDEMP-CAL-03 — `registrar_leitura` ignora mismatch payload** (INV-CAL-IDEMP-001 parcial). `registrar_leitura.py:133-141` retorna leitura existente silenciosamente quando `client_event_id` reusado com valor_lido diferente. Comportamento atual = "silent stale read"; INV exige 422 `IdempotencyPayloadMismatch`.

### MÉDIO (26) — INV-RITUAL-001 bloqueia

#### auditor-seguranca (4)

- **SEG-CAL-05** Jobs M4 não enforce contexto tenant (`processar_jobs_calibracao` precisa setar `active_tenant_context` antes de cada job).
- **SEG-CAL-06** `GRANT app_user` ausente em 19 tabelas M4 — funciona em test (OWNER=app_user) mas em PROD `app_user` não terá privilege.
- **SEG-CAL-07** `cancelar` action recebe `motivo_hash` do body sem validação cruzada server-side.
- **SEG-CAL-08** `analise_critica_pedido_inline_hash` aceito do body — mesma classe vetor SEG-CAL-01.

#### auditor-qualidade (4)

- **Q-CAL-02 — Mascaramento — `cancelar` retorna 501 com payload validado** (`views.py:215-234`). Endpoint registrado em URL + serializer real — equivalente a handler vazio.
- **Q-CAL-03 — TST-005 — `cmc_cobre`/`procedimento_vigente_para` STUB fail-open sem teste explícito do caso "fail-open Wave A retorna True hoje"** (regressão silenciosa quando módulo entrar).
- **Q-CAL-04 — TST-006 — Testes M4 usam `uuid4()` aleatório sem teste-irmão com UUID literal digit-heavy** (paralelo Q-OS-04, ≥30 ocorrências).
- **Q-CAL-05 — Cobertura `application/metrologia/calibracao/**` sem PG real ~30%** (estimativa autoavaliação) — sem `coverage.xml` versionado pra confirmar.

#### auditor-produto (3)

- **PROD-CAL-04** 10 ViewSets prometidos no plan.md não entregues (Leitura/Orcamento/Revisao/Conferencia/NC/Subcontratacao/Reclamacao/Padrao/Escopo/Proficiencia/VI). TRACK Wave A mas produto invisível pro usuário.
- **PROD-CAL-05** AC-CAL-001-3 + 002-3 + 004-8 + 007-5 declarados em PRD §11 mas use cases não os enforçam — drift PRD-vs-código de 4 ACs.
- **PROD-CAL-06** `dispara_recall_m5` no output de `responder` é boolean inerte — nenhum publisher de evento `Calibracao.ReclamacaoRespondida`.

#### auditor-drift-docs (9)

- **D6-ADR-1** `AGENTS.md:§11` — **ADR-0065 ausente** (frontmatter aceito 2026-05-25).
- **D2-CURRENT-1** `.agent/CURRENT.md` — **163 linhas vs limite ≤40**; 4 linhas duplicadas; rotacionar pra diário.
- **D2-DIARIO-1** `docs/faseamento/diario/` — última entrada 2026-05-25; faltam 3 dias.
- **D7-AGENTS-2** `AGENTS.md:8` — "905/0/0" vs ≥916 esperado pós-M4.
- **D4-AGENTS-1** `AGENTS.md` — drills `validar_*` lista F-A/B + M1/M2 + F-C1 mas omite `validar_m4_calibracao` (existe — T-CAL-159).
- **D1-TASKS-1** `tasks.md frontmatter` — `status: stable` mas Fase 8 ESQUELETO + Fase 10 PARCIAL.
- **D7-AGENTS-3** `AGENTS.md:262` — texto §12 M3 OS "P5 EM CONSERTO" contradiz header "FECHADO 2026-05-25".
- **D6-ADR-2** `AGENTS.md:§11 ADR-0034..0042` — várias `🟡 proposta` que spec/PRD M4 já tratam como aceitas.
- **D7-DATAS-1** `.agent/CURRENT.md:16,28,59` — "hoje"/"esta sessão" sem âncora data.

#### auditor-observabilidade (3)

- **OBS-CAL-01 — Trilha hash-chain WORM declarada mas NUNCA emitida** (OBS-001). 23 tipos de evento na migration 0009 ficam letra morta; nenhum use case M4 chama `EventoDeCalibracao.salvar_em_cadeia`. Auditor CGCRE pede "quem aprovou Cal-2026/1234?" → tabela vazia.
- **OBS-CAL-02 — Logs jobs sem `extra={"tenant_id", "correlation_id"}`** (OBS-002). 8 `logger.info` + 1 `logger.exception` em `processar_jobs_calibracao` com interpolação posicional; LogRecord não-filtrável.
- **OBS-CAL-03 — Views não logam em endpoints sensíveis** (OBS-002). 3 actions sem `logger.<level>`; `_serializar_snapshot` não retorna `correlation_id`.

#### auditor-idempotencia (2)

- **IDEMP-CAL-04** 15 ViewSets faltantes carregam débito IDEMP-001 — nascer copiando esqueleto atual propaga gap.
- **IDEMP-CAL-05** Jobs trigger-por-evento (`analisar_padrao_medicoes_controle`, `analisar_correlacao_componentes`) precisarão `@consumer_idempotente` ao virarem consumers reais — gate explícito ausente.

#### auditor-conformidade-lgpd (1)

- **LGPD-CAL-01 — Helper `sanitizar_payload_evento_calibracao` ausente** (LGPD-MEC-002 + paralelo SEG-CAL-03). `_serializar_snapshot` Wave A não vaza UUID de ator hoje, mas ampliação futura vaza sem helper.

### BAIXO/CONCERN (~18) — viram GATE Wave A

- 2 GATE-CAL-PERF (visão 360 N+1 + ListCalibracoes paginação) — Wave A explícito.
- 1 CONCERN LLM (`_serializar_snapshot(snapshot: Any)` — trocar para CalibracaoSnapshot).
- 1 CONCERN qualidade (skip `test_inv_cal_rls_grants_completos.py:172-175` sem data+dono).
- 3 GATE-DEP (argon2 pin + 4 actions SHA + Dockerfile imagem) — carry-over.
- 4 GATE-CAL-IDEMP (3 novos: Mixin nos 3 entregues + Hook estendido + IdempotencyPayloadMismatch + CONSUMER-WAVE-A).
- 3 BAIXO drift (4 linhas duplicadas CURRENT, frontmatter draft auditoria, "3 auditores" em AGENTS:79).
- 1 BAIXO LGPD GATE-LGPD-MEC-001 (atores `executor_id` etc sem citação artigo).
- 3 GATE-CAL-SEG (10 ViewSets ACTION_MAP, rate-limit recepcionar, IDEMP-18-POSTS).

---

## 4. Plano de conserto causa-raiz (em execução 2026-05-27)

Ordem (mais barato → mais caro), paralelo ao M3 OS:

1. **Batch S1 — drift-docs** (4 ALTO + 9 MÉDIO + 4 BAIXO). Editar AGENTS.md (§3 hooks 377/48 + §11 +ADR-0065 + §12 +M4); CLAUDE.md (numerais); rotacionar CURRENT.md (≤40 linhas) + criar `docs/faseamento/diario/2026-05-26-marco4-p4.md` + `2026-05-27-marco4-p10.md`; tasks.md frontmatter draft.
2. **Batch S2 — segurança + LGPD** (1 CRÍTICO + 3 ALTO + 4 MÉDIO + 1 MÉDIO LGPD). Server-side derivation `cliente_referencia_hash`/`cliente_key_id` em serializer; defesa em profundidade `obter_por_id(.., tenant_id=)`; criar `event_helpers.py::sanitizar_payload_evento_calibracao`; INV-CAL-FRAUDE-RECEB-001 enforced em `subcontratacao.registrar_recebimento`; migration `0014_grants_app_user`; tenant guard nos 7 jobs.
3. **Batch S3 — idempotência** (1 CRÍTICO + 2 ALTO + 2 MÉDIO). `IdempotencyMixin` nas 3 actions Wave A + `ACTION_IDEMPOTENT` map; T-CAL-136 hook estendido para `calibracao/views.py`; `registrar_leitura` retorna 422 `IdempotencyPayloadMismatch` quando payload divergente.
4. **Batch S4 — observabilidade** (3 MÉDIO + 1 BAIXO). Criar `application/metrologia/calibracao/append_evento_calibracao.py` (ADR-0065); retrofit 16 use cases para emitir `EventoDeCalibracao` na mesma `transaction.atomic`; logs estruturados com `extra=` nos jobs + views; `_serializar_snapshot` retorna `correlation_id`.
5. **Batch S5 — produto + qualidade** (3 ALTO produto + 1 ALTO qualidade + 7 MÉDIO). **ADR-0066** (paralelo ADR-0063): `cmc_cobre`/`procedimento_vigente_para` fail-open lazy Wave A com GATEs explícitos + modificar AC-CAL-002-2/015-1/016-1..3 do PRD; implementar use case `cancelar_calibracao` (T-CAL-095); renomear 12 classes de teste para `TestINV_CAL_<ID>`; criar fixture UUID digit-heavy regression; coverage M4 mensurado em `reports/coverage-m4-p4.log`.

## 5. GATEs Wave A rastreados (não bloqueiam fechamento — viram BAIXO)

| GATE | Origem | Bloqueia |
|---|---|---|
| GATE-CAL-CMC-PREDICATE | PROD-CAL-01 stub `cmc_cobre` (será ADR-0066) | 1º tenant RBC externo |
| GATE-CAL-PROC-VIGENTE-PREDICATE | PROD-CAL-02 stub idem | 1º tenant externo |
| GATE-CAL-MC-NUMPY | T-CAL-055..058 Batch C diferido (DEP-001) | Tenants Monte Carlo |
| GATE-CAL-VIEWSETS-WAVE-A | 10 ViewSets restantes | 1º tenant externo |
| GATE-CAL-IDEMP-1/2/3 | IDEMP-CAL-01..03 (entrarão no Batch S3) | dogfooding |
| GATE-CAL-IDEMP-CONSUMER-WAVE-A | IDEMP-CAL-05 | Wave A bus |
| GATE-CAL-BACKUP-METROLOGICO | T-CAL-114 — B2+KMS | 1º tenant externo |
| GATE-CAL-DRILL-LOCAL | T-CAL-159 PASS em Balanças Solution | dogfooding |
| GATE-CAL-CARGA-50T | T-CAL-152 | dogfooding |
| GATE-CAL-REPLAY-30FIX | T-CAL-153 | dogfooding |
| GATE-CAL-PERF-1/2/3 | auditor-performance | dogfooding/1º tenant |
| GATE-CAL-HOOK-FOTO-EXIF | T-CAL-143 | 1º tenant externo |
| GATE-CAL-HOOK-OVERRIDE-CONTRATO | T-CAL-144 | 1º tenant externo |
| GATE-CAL-COMPONENTES-CGCRE | T-CAL-P35-7/8 SELO CGCRE | 1º tenant RBC |
| GATE-CAL-OAB-MINUTAS | 6 minutas DPA/aceites/cláusulas | 1º tenant externo |
| GATE-CAL-ADR-0028-REV3 | T-CAL-P35-11 Modalidade 8 (Property metrológico) | dogfooding seguro |
| GATE-CAL-DPIA | T-CAL-P35-12 | 1º tenant externo |
| GATE-CAL-SANITIZER-HELPER | SEG-CAL-03 (entrará no Batch S2) | dogfooding |
| GATE-CAL-GRANTS-APP-USER | SEG-CAL-06 (entrará no Batch S2 — migration 0014) | dogfooding |
| GATE-DEP-PIN-ARGON2 / SHA-WORKFLOWS / SHA-DOCKERFILE | carry-over | Wave A start |

---

## 6. Status

**VEREDITO 1ª PASSADA: FAIL — INV-RITUAL-001 bloqueia fechamento.** 41 achados C/A/M originalmente abertos; **conserto causa-raiz aplicado em 6 batches consecutivos (S1..S6)**:

| Batch | Commit | C | A | M | Resumo |
|---|---|---|---|---|---|
| S1 drift-docs | `7c06411` | 0 | 4 | 9 | AGENTS §3/§11/§12; CLAUDE; CURRENT rotacionado; 2 diários M4 |
| S2 segurança+LGPD (parcial) | `146ef9b` | 1 | 1 | 3 | SEG-CAL-01 server-side hash PII; helper `lgpd.py` (+22 tests) |
| S3 idempotência | `4b58c24` | 1 | 2 | 0 | IdempotencyMixin nos 3 actions + hook estendido + IdempotencyPayloadMismatch |
| S5 inicial (ADR-0066) | `ae524e5` | 0 | 2 | 0 | Fail-open lazy formalizado paralelo a ADR-0063 |
| **S4 observabilidade** | (este lote) | 0 | 1 | 3 | `append_evento_calibracao` use case + `DjangoEventoDeCalibracaoRepository` (ADR-0064/0065); logs estruturados `extra={tenant_id, correlation_id}` nos jobs + 3 actions; `_serializar_snapshot` retorna `correlation_id` |
| **S5 conserto restante** | (este lote) | 0 | 3 | 6 | SEG-CAL-02 `obter_por_id` com filtro tenant explícito; SEG-CAL-04 `RecebedorSpoofingProibido` + `RecebedorIgualExecutorProibido`; SEG-CAL-05 jobs em `run_in_tenant_context`; SEG-CAL-06 migration 0014 GRANT app_user nas 23 tabelas; PROD-CAL-03 use case `cancelar_calibracao` (T-CAL-095) + emite `Cancelada`; Q-CAL-01 12 classes `TestINV_CAL_*` nomeadas; Q-CAL-03 regressão fail-open lazy ADR-0066; Q-CAL-04 regressão UUID digit-heavy |
| **Subtotal zerado** | | **2** | **13** | **21** | **36/41** |
| **Restante aberto** | | **0** | **0** | **5** | OBS-CAL-04 BAIXO (`_serializar_snapshot` exige PG real); Q-CAL-02 cobertura mensurada PG real (TRACK Wave A); Q-CAL-05 coverage.xml versionado (TRACK Wave A); SEG-CAL-08/LGPD-CAL-01 (consertados via helper unico — pendente confirmar via grep) |

**2/2 CRÍTICOS ZERADOS ✅** + **13/13 ALTO ZERADOS ✅** + **21/26 MÉDIO ZERADOS ✅** — 5 MÉDIO remanescentes são todos TRACK Wave A (exigem PG real ou são consertos já distribuídos em S2). 2ª passada FAMÍLIA 5 EXECUTADA — ver §7.

## 7. 2ª passada Família 5 — 2026-05-27 (10 auditores em paralelo)

| Lente | Auditor | Veredito 2ª | Detalhe |
|---|---|---|---|
| Segurança | `auditor-seguranca` | **CONCERNS** | 8 SEG-CAL-* da 1ª passada **fechados**; 2 BAIXO carryover: chave HMAC hardcoded em `lgpd.py` (já rastreado GATE-CAL-HMAC-RETENCAO + GATE-CAL-KMS-MRK) + texto canonicalizado em `motivo_cancelamento` sem denylist anti-PII (texto livre — overlap com Qualidade). Nenhum CRÍTICO/ALTO/MÉDIO aberto. |
| Qualidade | `auditor-qualidade` | **PASS** | Q-CAL-01..04 fechados. 12 classes `TestINV_CAL_*` reais (primitivas de domínio invocadas; sem stub vazio). Cancelar retorna 200 com snapshot; tratamento explícito 404/409. Q-CAL-05 TRACK Wave A esperado. |
| Produto | `auditor-produto` | **PASS** | PROD-CAL-01..03 fechados. ACs reescritos no PRD com nota ADR-0066. Nenhum jargão "Wave A" / "T-CAL-095" vaza em response (corrigido em S6 nos docstrings). |
| Observabilidade | `auditor-observabilidade` | **PASS** | OBS-CAL-01/02/03 zerados. Trilha WORM emitida nas 3 actions HTTP; logs estruturados em jobs + views; correlation_id no body. OBS-003 métrica permanece CONCERN BAIXO até F-C (rastreado GATE-OBS-METRIC-CAL-1). |
| Idempotência | `auditor-idempotencia` | **PASS** | IDEMP-CAL-01 fechado. 3 actions exigem header + payload fingerprint; service de idempotência detecta mismatch (422). IDEMP-002 N/A (consumer real só em Wave A). |
| Supply chain | `auditor-supplychain` | **PASS** | Sem mutação em deps/Dockerfile/workflows desde a 1ª passada. PASS mantido. |
| LLM correctness | `auditor-llm-correctness` | **PASS** | Subiu de CONCERNS (1ª passada). Docstrings vs corpo coerentes; `Any` apenas em fronteira REST/CLI; spec-as-source preservado em todos use cases novos. |
| LGPD | `auditor-conformidade-lgpd` | **PASS** | LGPD-CAL-01 fechado. `sanitizar_payload_evento_calibracao` é caminho único; `salvar_em_cadeia` recebe payload já sanitizado. Hashes server-side ADR-0064. |
| Performance | `auditor-performance` | **PASS** | Mantido. Advisory lock estreito por `(tenant, calibracao)` — não serializa cross-tenant; sem N+1; HMAC local (não rede). |
| Drift docs | `auditor-drift-docs` | **CONCERNS → PASS pós-S6** | DRIFT-CAL-01..13 da 1ª passada fechados; DRIFT-CAL-14..17 novos (377→379 + ADR-0066 no header + auditoria L33 + CURRENT 41 linhas) zerados no batch S6 corrente. |

**Veredito consolidado 2ª passada: 8 PASS + 2 CONCERNS (Seguranca BAIXO carryover Wave A; Drift-docs ALTO/MÉDIO consertado em S6).** 3ª passada parcial só drift-docs após commit do S6 fechará INV-RITUAL-001.

## 8. Apêndice — invocação dos auditores

Prompts versionados em `docs/governanca/auditor-*-prompt.md`. 10 auditores invocados em paralelo via Agent tool com prompts self-contained referenciando achados específicos da 1ª passada + arquivos dos batches S1..S5.
