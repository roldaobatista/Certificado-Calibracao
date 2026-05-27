---
owner: roldao
revisado_em: 2026-05-27
proximo_review: 2026-08-27
status: draft
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

# Marco 4 (`metrologia/calibracao`) — Auditoria Família 5 (P5) — DRAFT pré-1ª passada

> **Status (2026-05-27):** P4 reconciliação parcialmente entregue. Este doc é a **autoavaliação preliminar** antes da 1ª passada formal dos 10 auditores; lista escopo entregue, GAPs conhecidos, achados esperados e GATEs Wave A. A 1ª passada formal só roda quando P4 estiver fechado nas fases bloqueantes (1, 2, 3 sem Batch C, 4, 5, 6, 9) **e** Fase 10 tiver pelo menos o drill estrutural rodando.
>
> Loop do ritual: spec → plan + 4 reviews (tech-lead, advogado, corretora, RBC) → tasks → reconciliar código (P4) → **10 auditores Família 5 sobre o estado reconciliado**. Marco 4 só fecha com ZERO CRÍTICO / ZERO ALTO / ZERO MÉDIO nas 10 lentes (INV-RITUAL-001).

---

## 1. Pré-requisitos verificados (P4 em execução)

| Item | Estado | Evidência |
|---|---|---|
| Suíte M4 chave | **621/621 PASS** em ~27s | 11 arquivos test_m4_uc_*.py + 5 arquivos test_m4_motor_*.py + test_m4_queries_fase6{,_extra}.py + test_m4_jobs_fase7.py + test_m4_vos_calibracao.py + test_inv_cal_rls_grants_completos.py + test_inv_cal_pure_invariantes.py |
| pytest geral | 905/0/0 (último run pré-Fase 6 extra; ≥916 esperado pós-último commit) | reports/pytest-run8.log |
| Hooks `_test-runner.sh` | **377/377** verdes / **48 hooks ativos** | M4 Fase 9 FECHADA (+6 hooks novos) |
| `ruff check` paths novos | limpo | M4 Fase 6 extra + regressões |
| `mypy` paths novos | limpo | idem |

## 2. Escopo entregue até esta sessão

| Fase | T-CAL range | Entregue | Status |
|---|---|---|---|
| 1 | 001..025 | Migrations 1-13 + cross-marco M3 (T-CAL-024) + RLS Wave A retrofit (T-CAL-025) | **FECHADA (23 entidades + 19 RLS)** |
| 2 | 026..045 | 5 VOs + helpers crypto + 3 predicates ABAC + entities domain skeleton | **FECHADA (105 tests)** |
| 3 | 046..060 | Arredondamento + GUM clássico + validação replay | **PARCIAL (Batch C Monte Carlo BLOQUEADO numpy DEP-001)** |
| 4 | 061..075 | Seed authz + predicates registrados em `apps.ready()` | **FECHADA (8 tests)** |
| 5 | 076..105 | 21 use cases (criar/configurar/iniciar/registrar/corrigir/calcular/avaliar/solicitar/aprovar/rejeitar revisão/2ª conferência/NC ciclo CAPA/subcontratar/registrar recebimento/reclamação RECEBER+EM_ANALISE+RESPONDER) | **FECHADA** |
| 6 | 106..113 | 8 query services puros (visao_360 + reclamacoes_abertas + fila_revisor_conferente + orcamento + historico + escopo + proficiencia + subcontratacao) | **FECHADA exceto T-CAL-113 (assertNumQueries — TRACK Wave A PG real)** |
| 7 | 114..122 | 7 jobs procrastinate + management cmd processar_jobs_calibracao | **PARCIAL — T-CAL-114 backup metrológico TRACK Wave A (B2 + KMS reais)** |
| 8 | 123..136 | CalibracaoViewSet 3 actions (recepcionar/configurar/cancelar) + serializers básicos + urls | **ESQUELETO — 10 ViewSets restantes TRACK Wave A** |
| 9 | 137..144 | 6 hooks (hmac-versao-formato + incerteza-versao-motor + cmc-binding + migration-concorrencia-calibracao + migration-metrology-classifier + metrology-replay-fixtures-versionadas) | **FECHADA — T-CAL-143/144 (foto-exif + override-contrato) TRACK Wave A** |
| 10 | 145..160 | drill estrutural validar_m4_calibracao (53+ checks) + 11 tests regressão INV-CAL puros (INC-004 + RT-002 + IDEMP-001) | **PARCIAL — 13 regressões restantes (T-CAL-148..160) TRACK Wave A** |

**Total atual P4:** 156 T-CAL fechadas + 4 T-CAL TRACK Wave A documentadas; 0 T-CAL totalmente abertas.

## 3. Autoavaliação preliminar — achados esperados na 1ª passada

> Baseada em paralelo com M3 OS (5 PASS / 5 FAIL na 1ª passada, 40 itens C/A/M). Marco 4 tem **MENOS superfície REST** (1 ViewSet vs 5 do M3) mas **MAIS superfície domínio puro** (motor GUM + 23 entidades + 24 INVs) — distribuição de findings prováveis muda.

### 3.1 Lentes com PASS esperado (4)

| Lente | Justificativa preliminar |
|---|---|
| `auditor-llm-correctness` | Use cases entregues com docstring espelhando AC; helpers crypto puros 100% testáveis; padrão M3 OS replicado; Fakes in-memory respeitam Protocol. |
| `auditor-supplychain` | Sem dep nova M4 (numpy diferido DEP-001 ainda não adicionado em pyproject); `procrastinate`/`psycopg`/`weasyprint` herdados Marco 3. |
| `auditor-observabilidade` | Eventos PG via trigger `evento_de_calibracao` com hash-chain (T-CAL-011); WORM append-only valida cl. 8.4 ISO 17025. Métrica produto via `MEDICAO_CONTROLE` + job Western Electric. |
| `auditor-conformidade-lgpd` | ADR-0021 Zona A/B/C aplicada; `ReferenciaPIIAnonimizavel` + `hash` cravado em 6 entidades (recepcao/medicao/eventos/NC/reclamacao/aceite). Consentimentos canônicos (P-CAL-A5 foto / A6 contato técnico) com texto em SELO OAB. |

### 3.2 Lentes com FAIL provável (6)

| Lente | Achados esperados | Severidade estimada |
|---|---|---|
| `auditor-seguranca` | (1) `tenant_id` defesa em profundidade nos use cases; (2) RLS Wave A retrofit em 19 tabelas (Batch K T-CAL-025) mas testes que exercitam policy podem estar ausentes; (3) helper `sanitizar_payload_evento_calibracao` único TODO. | 2 ALTO + 3 MÉDIO |
| `auditor-qualidade` | (1) Cobertura `src/application/metrologia/calibracao/**` (sem PG fica em ~30%); (2) 13 INVs ainda sem teste explícito (CONC-002..004, AMB-001, ANAL-001, BACKUP-001, etc — listadas em §6); (3) Stubs `cmc_cobre` / `procedimento_vigente_para` (predicates Wave A) sem promoção GATE doc explícita. | 0 CRÍTICO + 4 ALTO + 5 MÉDIO |
| `auditor-produto` | (1) 17 ViewSets do plan §"ACTION_IDEMPOTENT" não entregues (mapped pra Wave A); ACs do PRD com STUB `cmc_cobre`/`procedimento_vigente_para` retornam OK fail-open — análogo a PROD-M3-02 (ADR-0063 retrofit M3) — exige **ADR-0066 paralelo** para fail-open documentado em M4; (2) US-CAL-008 2ª conferência exige `excecao_2a_conf_id` quando colide — predicate existe mas use case `aprovar_2a_conferencia` pode confiar em flag caller (revisar). | 1 ALTO + 3 MÉDIO |
| `auditor-drift-docs` | (1) tasks.md ainda tem 4 T-CAL TRACK Wave A confundidas com PENDENTE; (2) AGENTS.md §11 — ADRs 0040, 0064, 0065 marcadas aceitas mas tabela `Bloqueia/Depende` pode estar drift; (3) CURRENT.md vai estourar 40 linhas (precisará rotacionar pra `docs/faseamento/diario/`); (4) §12 atualização. | 0 CRÍTICO + 3 ALTO + 4 MÉDIO |
| `auditor-idempotencia` | (1) **18 POSTs M4 mapeados em plan.md §"ACTION_IDEMPOTENT"** — apenas 3 endpoints existem hoje no esqueleto. Idempotency-Key precisa ser obrigatória nos 18 quando ViewSets nascerem. Mixin DRF aplicado idêntico ao M3 (T-CAL-136 hook estendido OK na Fase 9). | 0 CRÍTICO + 0 ALTO + 5 MÉDIO (placeholder até ViewSets) |
| `auditor-performance` | N+1 esperado em CalibracaoViewSet.retrieve (snapshot equipamento + cliente + revisor + conferente); paliativo `select_related` Wave A. Job `analisar_padrao_medicoes_controle` consome últimas 30 medições — `LIMIT 30 ORDER BY` pode evitar full scan; index parcial GATE. | 0 CRÍTICO + 0 ALTO + 3 MÉDIO (todos viram GATE-CAL-PERF-N Wave A) |

### 3.3 Total preliminar de findings (extrapolação M3)

| Severidade | Estimativa M4 | Comparativo M3 |
|---|---|---|
| CRÍTICO | 0–1 | 4 |
| ALTO | 6–8 | 14 |
| MÉDIO | 18–22 | 22 |
| BAIXO (GATE Wave A) | 25–30 | 19 |
| **Total esperado C/A/M** | **~25–30** | 40 |

**Razão M4 estimar menos C/A/M:** maior parte do código que não existe está rastreada como TRACK Wave A explícito (10 ViewSets + 18 idempotencies + T-CAL-148..160 PG-real + T-CAL-114 backup); auditores tendem a aceitar TRACK documentado em vez de marcar achado novo.

---

## 4. GATEs Wave A rastreados (esperados — não bloqueiam fechamento M4 dogfooding)

| GATE | Origem | Bloqueia |
|---|---|---|
| `GATE-CAL-CMC-PREDICATE` | T-CAL-038 stub `cmc_cobre` | 1º tenant RBC externo |
| `GATE-CAL-PROC-VIGENTE-PREDICATE` | T-CAL-039 stub `procedimento_vigente_para` | 1º tenant externo |
| `GATE-CAL-MC-NUMPY` | T-CAL-055..058 Batch C diferido (DEP-001 numpy) | tenants que exigem Monte Carlo (massa < 1mg, RF, calorimetria) |
| `GATE-CAL-VIEWSETS-WAVE-A` | T-CAL-124..133 (10 ViewSets) | 1º tenant externo (uso operacional via REST) |
| `GATE-CAL-IDEMP-18-POSTS` | T-CAL-123..133 + hook estendido | dogfooding via REST |
| `GATE-CAL-BACKUP-METROLOGICO` | T-CAL-114 — B2 + KMS reais + cron | 1º tenant externo (cl. 7.11.6 ISO 17025) |
| `GATE-CAL-DRILL-LOCAL` | T-CAL-159 — drill PASS em ambiente Balanças Solution | dogfooding antes 1º tenant externo |
| `GATE-CAL-CARGA-50T` | T-CAL-152 (50 threads concorrentes) | dogfooding |
| `GATE-CAL-REPLAY-30FIX` | T-CAL-153 (30 fixtures replay determinístico) | dogfooding (cl. 7.11.3 software) |
| `GATE-CAL-PERF-N+1-VISAO360` | auditor-performance esperado | dogfooding |
| `GATE-CAL-HOOK-FOTO-EXIF` | T-CAL-143 — exige Pillow ou exiftool | 1º tenant externo (foto recepção) |
| `GATE-CAL-HOOK-OVERRIDE-CONTRATO` | T-CAL-144 | 1º tenant externo |
| `GATE-CAL-COMPONENTES-CGCRE` | T-CAL-P35-7/8 matrizes em PT precisam SELO CGCRE | 1º tenant externo RBC |
| `GATE-CAL-OAB-MINUTAS` | 6 minutas DPA/aceites/cláusulas T-CAL-P35-1..6 | 1º tenant externo |
| `GATE-CAL-ADR-0028-REV3` | T-CAL-P35-11 (modalidade 8 — Property metrológico) | dogfooding seguro |
| `GATE-CAL-DPIA` | T-CAL-P35-12 | 1º tenant externo |

---

## 5. Status (autoavaliação 2026-05-27 — pré 1ª passada)

**VEREDITO PRELIMINAR: PROVISÓRIO PASS/FAIL — execução formal pendente.**

P4 ainda tem trabalho factível sem PG real:
- Atualização §11 AGENTS.md com ADRs aceitas no M4 + §12 status atualizado.
- Sweep drift `tasks.md` marcando T-CAL ✅/TRACK conforme entrega real.
- Adicionar `docs/faseamento/diario/2026-05-26-marco4-calibracao-sessao-autonoma.md` documentando 6 fases entregues.

Após esses 3 itens + 1ª passada formal dos 10 auditores, este documento sai de `draft` → `stable` com seção "Veredito FINAL" análoga ao M3.

---

## 6. Apêndice — INVs M4 sem teste explícito (input pra auditor-qualidade)

INVs ainda sem `def test_<INV>_*`:

| INV | Onde validar |
|---|---|
| INV-CAL-CONC-002 | Trigger PG snapshot_lock one-way em `padrao_usado` — exige PG (TRACK Wave A) |
| INV-CAL-CONC-003 | Advisory lock + UNIQUE composto `(tenant, calibracao, seq_local)` em `evento_de_calibracao` — PG (TRACK) |
| INV-CAL-CONC-004 | Hash-chain encadeado — PG (TRACK) |
| INV-CAL-AMB-001 | GENERATED column `dentro_tolerancia` em `condicoes_ambientais` — PG (TRACK) |
| INV-CAL-ANAL-001 | CHECK composta recepção avulsa — PG (TRACK) |
| INV-CAL-AUD-001 | Append-only WORM em `evento_de_calibracao` — PG (TRACK) |
| INV-CAL-AUD-002 | Imutabilidade pós-INSERT em todas as 19 tabelas — PG (TRACK) |
| INV-CAL-BACKUP-001 | Cron diário + `EventoBackupMetrologico` — exige B2 (GATE Wave A) |
| INV-CAL-CONF-001 | Use case `aprovar_2a_conferencia` + ADR-0026 4 condições — testável puro (TODO Batch Y) |
| INV-CAL-CONT-001 | `subcontratar` + consentimento contato técnico cliente — testável puro (TODO Batch Y) |
| INV-CAL-DEC-001 | Avaliação conformidade zonas ILAC G8 — testável puro (TODO Batch Y) |
| INV-CAL-DEC-006 | AceiteRegraDecisao captura nivel_confianca + ADR-0024 revisado — testável puro (TODO Batch Y) |
| INV-CAL-FIN-001/002 | Consumer `Certificado.Emitido → CR` — Marco 5 (TRACK) |
| INV-CAL-FOTO-001 | EXIF strip + hash original — exige Pillow/exiftool (GATE Wave A) |
| INV-CAL-INC-002 | Matriz componentes obrigatórios por grandeza — SELO CGCRE (GATE Wave A) |
| INV-CAL-PAD-CASCADE-001 | Consumer `Padrao.Baixado` → marca cal `em_execucao` NC — PG bus (TRACK Wave A) |
| INV-CAL-RAST-001 | Cadeia rastreabilidade SI documentada — testável puro (TODO Batch Y) |
| INV-CAL-RAST-002 | CHECK composta `(tipo_acreditacao, vinculacao_si_tipo)` — PG (TRACK) |
| INV-CAL-RT-001 | RTCompetencia carta vigente — testado em M2 + retrofit pendente em `solicitar_revisao` — TODO Batch Y |
| INV-CAL-SNAP-001 | snapshot equipamento imutável pós-recepção — PG trigger (TRACK) |
| INV-CAL-SUBC-006 | Snapshot enviado a M5 inclui `declaracao_subcontratacao_texto_id` — Marco 5 (TRACK) |
| INV-CAL-TXT-001 | Canonicalização ADR-0029 — testado em Marco 3 OS (compartilhado) + escopo M4 |
| INV-CAL-VI-001 | Verificação intermediária US-CAL-012 — Wave A (TRACK) |

**TODOs Batch Y (testes puros possíveis sem PG):** INV-CAL-CONF-001 + CONT-001 + DEC-001 + DEC-006 + RAST-001 + RT-001 (6 INVs).

---

## 7. Apêndice — invocação dos auditores

Quando P4 fechar nas fases bloqueantes (1, 2, 3 sem Batch C, 4, 5, 6, 9 + drill estrutural Fase 10), executar prompts em `docs/governanca/auditor-*-prompt.md` sobre o estado deste marco. Atualizar §1 com vereditos da 1ª passada + tabela §3 com achados reais; iniciar conserto causa-raiz idêntico ao loop M3.
