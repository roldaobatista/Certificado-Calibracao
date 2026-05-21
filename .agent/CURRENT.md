# .agent/CURRENT.md

> ≤40 linhas. Atualizado a cada fechamento de Fase/Marco/US.

**Fase:** **FOUNDATION F-A + F-B FECHADA via ritual Spec Kit**
(2026-05-19). Próximo: backlog Wave-A (#7/#8) → Marco 1 `clientes`
definitivo → Marco 2 `equipamentos`. **Modo:** AUTÔNOMO.

## Virada de método (decisão Roldão 2026-05-19)

Remendo auditoria-a-auditoria não convergia — causa de fundo: o ritual
Spec Kit foi pulado em F-A/F-B. Decisão: recriar spec FORWARD do zero
(governa o código) + ritual completo + reconciliar código existente.
Programa P1..P9: F-A primeiro, F-B sobre F-A fechada (lição C1⇄C3).

Trabalho válido anterior NÃO descartado — foi validado pela spec
(FB-C1+C3 `32aa278`, FB-C2 `53e3cc2`, FB-C4+C5 `7924390` seguem de pé).

## F-A FECHADA via ritual (commits `4951389`..`f3711d7`)

- P1 spec forward `docs/faseamento/F-A/spec.md` (substitui stories-f-a).
- P2 plan + review 3 subagentes (tech-lead/advogado/RBC) → bloqueantes
  absorvidos (eliminação×imutabilidade LGPD, marco de corte CGCRE,
  grants test=prod, etc.).
- P3 matriz: núcleo OK; 8 GAPs → T-FA-01..08.
- P4: 7 fechados causa-raiz + T-FA-08→ADR-0020. Suite 280, hooks
  130/130, makemigrations limpo.
- P5: **3 auditores Família 5 = PASS, ZERO CRÍTICO/ALTO/MÉDIO.**
  Reparos MÉDIO/BAIXO resolvidos na causa-raiz (INV-RITUAL-001 —
  MÉDIO bloqueia fechamento). Consolidado:
  `docs/faseamento/F-A/auditoria-familia5.md`.

Gates Wave A rastreados (não bloqueiam F-A dogfooding): GATE-1..7
(B2/WORM, verificação periódica, NTP, ciclo chave PII, hash
AcessoDadosCliente, ADR-0020, higiene pattern `::uuid`).

## F-B FECHADA via ritual (P6..P9)

P6 spec forward → P7 plan + review tech-lead+advogado (bloqueantes
absorvidos: binding, vigência única, ip_hash HMAC contexto,
atomicidade≠commit, allowlist anti-PII, GATE-FB-2/3/4) → P8 matriz +
6 T-FB causa-raiz (T-FB-01..06) → P9 **3 auditores Família 5 = PASS,
ZERO CRÍTICO/ALTO/MÉDIO**. Suite 293, cobertura 85.60%, hooks 130/130,
drills verdes. Consolidado: `docs/faseamento/F-B/auditoria-familia5.md`.
Gate de fechamento de fase = INV-RITUAL-001 (MÉDIO bloqueia igual a
CRÍTICO/ALTO; hook `ritual-gate-check.sh`).

**FOUNDATION (F-A + F-B) FECHADA pelo ritual completo.** A virada de
método convergiu — o ritual fechou de forma coerente o que o remendo
não fechava.

## Feito nesta sessão (2026-05-19)

- **INV-RITUAL-001** (commit `ca8909e`, no servidor): MÉDIO bloqueia
  avanço de fase, igual a CRÍTICO/ALTO. Regra em REGRAS-INEGOCIAVEIS +
  hook `ritual-gate-check.sh` (PreToolUse Write|Edit) + 3 prompts de
  auditor + ritual. _test-runner 130/130. Pedido explícito do Roldão.
- **Lint sweep #7** (commit `3aeb3d4`, no servidor): ruff 193→0,
  format 100%, avisos de critério na causa-raiz. Suíte 293 verde em
  ordem fixa. NÃO reabre Foundation.
- **Expansão Família 5: 4 → 10 auditores** (commit `3fb9caa`, no
  servidor): Tier 1+2+3 completo motivado pelo bug `sanitizar_payload_audit`
  que passou em PASS dos auditores 1.0.0. Tier 1 endurece 3 prompts
  existentes (bump 1.1.0 stable) com TST-005..007 + SEC-SANITIZE-001.
  Tier 2 cria `auditor-llm-correctness` (LLM-001..003, Opus 4.7). Tier 3
  cria 5 auditores novos: performance (PERF-001..003), observabilidade
  (OBS-001..003), idempotência (IDEMP-001..002), supply chain
  (DEP-001..003), conformidade-LGPD mecânico (LGPD-MEC-001..003).
  Severidade consistente com INV-RITUAL-001 — MÉDIO+ bloqueia fechamento.
  AGENTS §5 + catálogo + memória `project_no_human_consultants` alinhados.
  130/130 hooks verdes. Pendências rastreadas (não bloqueiam): hook
  pre-commit orquestrador, 10 GitHub Actions, métricas/trilha de operação.
- **Flake visão-360 RESOLVIDO na causa-raiz** (commit `6c3e7b8`, no
  servidor): bug de PRODUÇÃO, não artefato de teste. `sanitizar_payload_audit`
  redigia `cliente_id` quando o UUID coincidia com regex de CPF/telefone
  (~8,4% dos uuid4). `registrar_auditoria` grava `payload_jsonb` cru; o
  endpoint sanitizava só na leitura → filtro do banco acerta evento, mas
  resposta volta com `cliente_id='[REDACTED]'`, quebrando correlação
  evento↔cliente na timeline da visão-360. Pista "depende de
  `pytest-randomly` seed" era ruído amostral (uuid4 vem de `os.urandom`).
  Fix: guard de UUID no ramo string do sanitizador antes das regexes —
  UUID é identificador surrogate, nunca PII (CPF/CNPJ/telefone/e-mail real
  jamais parseia como UUID). Cobre `cliente_id`, `usuario_id`,
  `causation_id`, qualquer chave UUID-valued. Regressão
  `tests/test_sanitizar_payload_audit.py` varre 5000 uuid4. Suíte
  **299 passed** (293→299), cobertura **85.85%** (85.60→85.85), hooks
  130/130. **MÉDIO sob INV-RITUAL-001 destravado.**
- **#8 médios rodada 2 F-A RESOLVIDOS** (commit `5aa1882`): R2-M1 +
  R2-M2 fechados na causa-raiz. R2-M1 (drill acumula lixo): drill é
  destrutivo-acumulativo por design (Auditoria INSERT-only + Tenant FK
  PROTECT), única limpeza é dropar+recriar banco; conserto = guard
  `--em-banco-descartavel` (aborta exit 2 se NAME ≠ test*) + contagem
  antes/depois honesta (Auditoria iterada por contexto, sem burlar RLS).
  R2-M2 (premissa Tenant globalmente legível): `isolamento-multi-tenant.md`
  §2.3.1 nova subseção explica galinha-e-ovo do middleware multi-tenant +
  segurança preservada (só metadados, sem PII); docstring de
  `verificar_integridade_cadeia` aponta pra §2.3.1. Validado: ruff +
  format + mypy 0 issues, pytest 299/85.85%, hooks 130/130, drill 5/5
  verde com contagem honesta (35T/21U/15093A operacional). Foundation
  intacta — não reabre auditoria.

## Marco 1 `clientes` via ritual Spec Kit — P1+P2+P3 (2026-05-19)

- **P1 spec forward** (commit `065161b`, no servidor): autoritativa
  em `docs/faseamento/M1-clientes/spec.md`. 5 US originais (cadastro,
  visão 360°, importação, bloqueio, dedup) + 12 non-goals + 4 INVs
  novos (INV-CLI-001 identidade canônica, INV-CLI-002 política LGPD
  única, SEC-CSV-001 anti-injection, INV-013-A contagem diária).
- **P2 plan + 4 reviews em paralelo** (commit `7c79295`): tech-lead +
  advogado + RBC + corretora. 10 pontos P-CLI-XN decididos
  (3 AJUSTADOS, 7 ACEITES). 18 bloqueantes adicionais absorvidos
  como AC novos. US-CLI-006 NOVA (direitos do titular, revogação,
  matriz eliminação vs anonimização, incidente ANPD, registro
  operações). Outbox transacional como padrão único Wave A
  cravado. Helper único `audit/event_helpers.py` cravado (SANEA-08).
- **P3 matriz spec↔código** (commit `f0249f0`): 24 OK, 20 GAP →
  T-CLI-101..120, 6 TRACK → GATE-CLI-1..6 (+2 modulares futuros).
  Correção do relatório do Explore: AC-CLI-001-4 e 003-7 estavam
  marcados OK; verificação direta no `lgpd.py:65-68` mostrou enum
  com 2 valores (spec exige 5) — GAP confirmado.

## Marco 1 P4 — execução T-CLI causa-raiz (em andamento)

- **T-CLI-103 ✅ FECHADO** (commit `4124a81`, no servidor):
  identidade canônica via `cliente_canonico_id`. Migration 0017 cria
  coluna NOT NULL com backfill `GENERATED ALWAYS AS (id) STORED` +
  `DROP EXPRESSION` (PG 12+) — preenche sem precisar UPDATE sob RLS.
  Trigger BEFORE INSERT defesa em profundidade. Model `save()` atribui
  `cliente_canonico_id=self.id` se None. Novo módulo `canonico.py`
  com `resolver_cliente_canonico` (cap=10, path compression em UPDATE
  quando hops>1, fail-loud `IdentidadeCanonicaCircular` em ciclo).
  6 testes (default, 1 mesclagem, 2 mesclagens com path compression,
  ciclo, cap excedido, property-based 100 cadeias).
- **T-CLI-101 ✅ FECHADO** (commit `234d0dd`): enum LGPD 5 bases + 3
  origens + `aceite_lgpd_lia_id`. Migration 0018 com `atomic=False` +
  `SET CONSTRAINTS ALL IMMEDIATE` (resolve "pending trigger events");
  ALTER COLUMN varchar(20→30) → DISABLE RLS → UPDATE remap → ENABLE+
  FORCE RLS → 2 CHECK constraints + LIA obrigatório quando
  LEGITIMO_INTERESSE. `lgpd.py` reescrito (`CONSENTIMENTO`,
  `EXECUCAO_CONTRATO`, `OBRIG_LEGAL`, `LEGITIMO_INTERESSE`,
  `PROTECAO_CREDITO` + `CADASTRO_DIRETO`/`IMPORTACAO_LEGADA`/
  `MIGRACAO_SISTEMA_ANTERIOR`). Mapeamentos PF_ORIGEM_PARA_BASE_LEGAL +
  PF_ORIGEM_PARA_ORIGEM_CADASTRO ajustados. serializers.py default
  `CADASTRO_DIRETO`. importar_clientes.py delega ao mapa canônico. 5
  testes novos cobrindo cada base + LIA + valores antigos rejeitados.
- **T-CLI-113 ✅ FECHADO** (commit `ae28fb7`): trigger PG runtime
  `cliente_canonico_imutavel_trg` BEFORE UPDATE valida transição (NULL
  bloqueado, self só se OLD=self, NEW=outro deve ser vivo do mesmo
  tenant). Hook `cliente-canonico-imutavel.sh` cobre tempo de CI
  (DROP TRIGGER/FUNCTION/COLUMN/ALTER + UPDATE SQL cru bloqueados;
  auto-allow pra migration de criação + override). 7 testes da
  trigger; ajuste em testes existentes pra separar UPDATE de
  cliente_canonico_id do UPDATE de deletado_em.
- **T-CLI-102 ✅ FECHADO** (commit `763efc8`): ClienteIdentidadeHistorico
  INSERT-only — rastreabilidade ISO 17025 §7.8.2.1 (b) + §8.4 pra
  alteração de razão social PJ (mesmo CNPJ) ou nome PF. Modelo + migration
  0020 com policies RLS SELECT/INSERT (sem UPDATE/DELETE policy por
  design); trigger AFTER UPDATE em `clientes` grava linha quando
  `nome`/`nome_fantasia` muda (lê `app.usuario_id` do contexto pra
  criado_por_id); trigger anti-mutation BEFORE UPDATE/DELETE como defesa
  em profundidade. FK `cliente` com `db_constraint=False` — Django
  validação da FK passaria por RLS na criação; integridade real garantida
  pela trigger AFTER UPDATE. 8 testes (UPDATE nome/nome_fantasia/outros
  campos; .update()/.delete() zero rows via RLS; trigger anti-mutation
  estrutural via pg_trigger; RLS isolado; criado_por_id do contexto).

- **T-CLI-105 ✅ FECHADO** (commit `3cb5194` WIP da sessão anterior +
  validação completa nesta sessão 2026-05-20): `event_helpers.py` com
  `publicar_evento()` aplicando garantias 1-4 (sanitize escrita, validação
  tenant, atomic do caller, causation_id idempotência) — `outbox=True` e
  `escopo=authz` levantam `NotImplementedError` até T-CLI-107.
  `job_contagem_diaria_acesso_pii` (INV-013-A) itera tenants ativos +
  grava cadeia sistema; default D-1 com `--data-referencia` override.
  Hook `event-helper-unico.sh` bloqueia `registrar_em_cadeia`/
  `registrar_auditoria` fora de paths permitidos (9 casos novos).
  10 cenários testados.
- **Validação T-CLI-105 + bootstrapping `test_afere`** (commit `ab142a3`,
  no servidor): suíte 335 passed, cobertura 87%, hooks 150/150. Novo
  script `docker/postgres/init/03-test-db.sh` automatiza criação de
  `test_afere` (OWNER=app_migrator, extensões, grants).

- **T-CLI-107 + T-CLI-110 ✅ FECHADOS via ritual completo** (2026-05-20):
  outbox transacional + worker em F-A. **Ritual:** design endurecido
  (`docs/faseamento/M1-clientes/T-CLI-107-110/design.md`) → review
  paralelo `tech-lead-saas-regulado` + `advogado-saas-regulado` (11
  bloqueantes absorvidos: T4 2-tx, BLOQ-A divergência RLS justificada,
  BLOQ-B poison limit, BLOQ-C contrato at-least-once, BLOQ-D non-goal
  ordering, BLOQ-A1..A7 advogado) → implementação causa-raiz → 10
  auditores Família 5 = **PASS, ZERO CRÍTICO/ALTO/MÉDIO** (segurança,
  qualidade, llm-correctness, performance, idempotência, observabilidade,
  conformidade-lgpd, supplychain, drift-docs; auditor-produto fica
  pra US completa). Entrega: tabela `bus_outbox` (UNIQUE
  causation_id+acao, CHECK anti-PII em acao, CHECK envelope ≤64KiB,
  RLS FORCE com divergência justificada cross-tenant em modo_sistema),
  `event_helpers.publicar_evento(outbox=True)` (INSERT idempotente),
  `outbox_worker.processar_outbox_em_contexto_tenant` em 3 transações
  (Tx-1 tentativas, Tx-2 dispatch+processado_em, Tx-3 ultimo_erro
  sanitizado inline), `drenar_outbox(limit)`, registry de consumers,
  2 management commands (`drenar_outbox_uma_vez`,
  `listar_outbox_envenenado`), `acoes_canonicas.py` (enum fechado),
  `politicas_lgpd.POLITICA_BUS_OUTBOX`. Matriz de retenção §2 ganhou
  linha `bus_outbox` + DRILL-RET-11 mensal.
  Suíte **353 passed** (era 335 → +18), cobertura **85.26%**, hooks
  **150/150**, ruff+format+mypy zero issues.

- **T-CLI-104 ✅ FECHADO via ritual completo** (2026-05-20): circuit
  breaker observado pra `AcessoDadosCliente`. **Ritual:** design
  (`docs/faseamento/M1-clientes/T-CLI-104/design.md`) → review
  paralelo `tech-lead-saas-regulado` + `corretora-seguros-saas` (5
  bloqueantes absorvidos: CRÍTICO T2 contagem sobrevive a rollback +
  ALTO T3 sliding window vs bucket fixo + ALTO C2 threshold absoluto
  OR + MÉDIO T4 idempotência on-chain + MÉDIO T5 nomes slug-compat) →
  implementação → 9 auditores Família 5 = **PASS, ZERO CRÍTICO/ALTO/
  MÉDIO** (1ª rodada segurança disparou 2 CRÍTICOS — forja
  cross-tenant + vazamento session-level — corrigidos via migration
  0013 + transação explícita BEGIN/SET LOCAL; 1ª rodada qualidade
  disparou MÉDIO `pytest.raises(Exception)` muito permissivo —
  apertado pra `ProgrammingError` + match RLS). Entrega: tabela
  `breaker_acesso_pii_evento` + alias DB `breaker_writer` autocommit
  (ATOMIC_REQUESTS=False, CONN_MAX_AGE=60), wrapper
  `registrar_acesso_dados_cliente_com_breaker` (fail-loud preservado;
  `BEGIN; SET LOCAL app.active_tenant_id; INSERT; COMMIT` em conexão
  paralela — SET LOCAL morre na transação, mata vetor pool-reuse),
  command `avaliar_circuit_breaker_acesso_pii` (threshold OR `(pct≥0.1%
  AND total≥1000) OR (falhas≥3 em 5min)`; idempotência on-chain via
  `causation_id=uuid5(NS, breaker:tenant:janela)` + SELECT prévio na
  auditoria), 2 ações canônicas (`sistema.breaker_acesso_pii.disparado/
  .normalizado`), migration 0012 (tabela + RLS) + 0013 (endurecimento
  policy INSERT WITH CHECK estrito tenant_id=active_tenant_id),
  visão 360 atualizada pra usar wrapper. 8 testes (golden CRÍTICO T2
  sobrevive a rollback + golden anti-forja cross-tenant + happy ok +
  fail-loud + ramo absoluto 3 falhas + ramo percentual + idempotência
  janela + threshold abaixo + isolamento por tenant).
  Suíte **361 passed** (era 353 → +8), cobertura **85.32%**, hooks
  **150/150**, ruff+format+mypy zero issues.

**Estado pós-P5 reauditado (2026-05-21)**: suíte **450+ passed**
(+13 testes Marco 1 close + 22 testes regressão `tests/regressao/inv_cli_*`
+ 3 testes HMAC trigger), cobertura ≥85% global e ≥89% agregado
`clientes/`, hooks **168/168** verdes, makemigrations limpo, drill
`validar_f_a`/`validar_f_b`/`validar_m1_clientes` verdes. ALTO-1 SEC
(SHA256 cru no trigger PG) e MÉDIO-1 SEC (filter por tenant em 5 rotas)
resolvidos causa-raiz via migration `audit/0015` (função
`pii_hash_hmac` + GUC `app.pii_hash_key_ativa`) e `Cliente.objects.filter(tenant_id=active,id=...)` em todas as 6 rotas.

- **US-CLI-006 PARCIAL ✅ (T-CLI-115/117/118/119/120) + GATE Wave A
  (T-CLI-114/116 + ADR-0021)** (commits `db281d7`, `3e96159`,
  `a4df08e`, 2026-05-20): direitos do titular LGPD em 3 commits
  atômicos pós review paralelo `advogado-saas-regulado` (PRIMÁRIO) +
  `tech-lead-saas-regulado` + `consultor-rbc-iso17025` (**16
  bloqueantes absorvidos** — 7 advogado + 6 tech-lead + 3 RBC).
  Pareceres em `docs/faseamento/M1-clientes/T-CLI-114-120/`.

  - **3a** (commit `db281d7`): T-CLI-117 validador anti-PII sensível
    (denylist taxativa art. 5º II, word-boundary `\b`, ≥5 chars,
    normalização unicode, sem falsos positivos `pt/vot/trans/gen`) +
    T-CLI-118 idade ≥18 CREATE+UPDATE (BLOQ-A6/TL-1) + CHECK
    constraint `ck_cliente_idade_minima_18`.
  - **3b** (commit `3e96159`): T-CLI-120 `OperacaoTratamentoCliente`
    INSERT-only + trigger PG `AFTER INSERT/UPDATE ON clientes`
    (BLOQ-TL-T4 — cobre `.update()`/bulk_update/raw SQL que signal
    Django não pega). Payload registra `base_legal +
    finalidade_negocial + documento_hash` SHA-256 (BLOQ-A7).
  - **3c** (commit `a4df08e`): T-CLI-115 revogação consentimento
    imediata (campo `consentimento_revogado_em` + endpoint
    `direitos-titular/revogacao_consentimento` + use case +
    `MAPA_FINALIDADE_BASE_LEGAL_ACEITA` BLOQ-A2) + T-CLI-119
    helper `emitir_incidente_pii` 3 modos (cliente_ids, escopo,
    default conservador — BLOQ-A5).
  - **3d** (GATE-CLI-US006-3d Wave A + commit ADR-0021): T-CLI-114
    (8 endpoints completos) + T-CLI-116 (matriz eliminação×anonimização
    real) ficam pra Wave A — escopo demanda integração com módulos
    NF/certificados ISO que ainda não existem em Marco 1.
    ADR-0021 (Anonimização vs retenção regulatória — 3 zonas A/B/C)
    fecha a decisão arquitetural; implementação real Wave A.

- **T-CLI-111 + T-CLI-112 ✅ FECHADO via fast-track** (commit
  `9c1ee21`, 2026-05-20): dedup compare GET + tipo_mesclagem + evidencia
  obrigatória M&A. Migração débito técnico: `mesclar()` agora usa
  `publicar_evento` (helper único — SANEA-08). 9 testes. Spec clara
  → fast-track sem reviews paralelos.

- **T-CLI-106 ✅ FECHADO via fast-track** (commit pendente, 2026-05-20):
  importação legada — campo `pii_regularizacao_em` + helpers
  `cliente_em_estado_restrito` + `regularizar_aceite_legado`. Enum
  origens já alinhado em T-CLI-101 (CADASTRO_DIRETO/IMPORTACAO_LEGADA/
  MIGRACAO_SISTEMA_ANTERIOR). 7 testes. Dashboard regularização =
  GATE-CLI-4 Wave A.

## P4 concluído — T-CLI-108 + T-CLI-109 fechados via fast-track (2026-05-20)

Decisão: implementar AGORA dentro do módulo `clientes` o que cabe ao
PRODUTOR (payload + predicate); CONSUMERS Wave A continuam como
GATE-CLI-7/8 rastreado (módulos `operacao/agenda` e `operacao/certificados`
ainda não existem). Spec cristalina pós-P2 → fast-track sem reviews
paralelos (mesmo critério T-CLI-106/111/112).

- **T-CLI-109 ✅ FECHADO**: predicate `cliente_bloqueado_para_entrega(resource)`
  em `predicates_authz.py` — função-consulta de domínio (não ABAC, consumer
  Wave A chama direto). Fail-safe: ID ausente/inválido → retém. 7 testes
  (manual + inadimplência + desbloqueado + sem ID + ID inválido +
  isolamento RLS + ponto puro). Consumer `operacao/certificados` =
  GATE-CLI-8 Wave A.

- **T-CLI-108 ✅ FECHADO**: `montar_payload_cliente_bloqueado` +
  `consultar_agendamentos_futuros_do_cliente` em `clientes/bloqueio.py`.
  Slot `agendamentos_futuros: list[str]` acordado no contrato pro
  consumer Wave A `operacao/agenda` (GATE-CLI-7) — Marco 1 retorna
  lista vazia (módulo agenda inexistente). `views.bloquear` +
  `job_inadimplencia_alertas` MIGRADOS de `registrar_auditoria` direto
  pra `publicar_evento(outbox=True)` (saldando débito de T-CLI-107: bloqueio
  agora entra no `bus_outbox` transacional). 6 testes (helper puro +
  E2E via endpoint).

- **Drill `validar_m1_clientes` criado** (`src/infrastructure/clientes/management/commands/validar_m1_clientes.py`):
  3 tenants intercalados executando cadastro/importação/dedup/bloqueio;
  verifica isolamento cross-tenant (Cliente / bus_outbox / OperacaoTratamentoCliente),
  cadeia auditoria por tenant, resolução canônica pós-mescla, slot
  agendamentos_futuros no payload. Drill PASS em test_afere; cobertura
  via `tests/test_drill_validar_m1_clientes.py`.

- **Reconciliação acessória — débito pré-existente do use case
  `mesclar_clientes`**: spec AC-CLI-005-3 exige
  `perdedor.cliente_canonico_id = vencedor.id`; use case não fazia.
  Drill descobriu (resolver_cliente_canonico voltava o perdedor).
  Fix causa-raiz: `repository.apontar_canonico_para(perdedor, vencedor)`
  ANTES do `soft_delete` no use case. Trigger PG T-CLI-113 valida
  transição self → vencedor_vivo_mesmo_tenant.

- **Migração débito T-CLI-112 em testes legados US-CLI-005**: 10 testes
  legados em `tests/test_clientes_us_cli_005_mesclar.py` não tinham sido
  atualizados pra novo campo obrigatório `tipo_mesclagem` (introduzido
  em commit 9c1ee21). Causa-raiz: adicionar `tipo_mesclagem: "DUPLICATA_OPERACIONAL"`
  nos payloads. 13/13 testes verdes pós-fix.

## Fila

#6 flake visão-360 ✅ + #7 lint sweep ✅ + #8 médios rodada 2 F-A ✅ +
Marco 1 P1+P2+P3+P4 ✅ + **18 T-CLI fechados produtor** (101/102/103/
104/105/106/107/108/109/110/111/112/113/115/117/118/119/120) + 2 GATE
Wave A (114/116 US-CLI-006-3d) + 8 GATE Wave A rastreados
(GATE-CLI-1..8). Próxima: **P5 — 10 auditores Família 5 sobre Marco 1
inteiro**, loop até PASS zero CRÍTICO/ALTO/MÉDIO. Consolidado em
`docs/faseamento/M1-clientes/auditoria-familia5.md`.
