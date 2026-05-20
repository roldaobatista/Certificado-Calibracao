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
  10 cenários testados (sanitize/tenant_mismatch/modo_sistema/outbox/
  authz/inválido + job por tenant + default D-1).
- **Validação T-CLI-105 e bootstrapping de `test_afere`** (2026-05-20):
  suíte completa **335 passed** (era 325 → +10 testes T-CLI-105),
  cobertura **87%** (era 85.85% → +1.15pp), hooks **150/150** verdes
  (era 141 → +9 do `event-helper-unico`), lint+format zero issues.
  Banco `afere` (dogfooding) e `test_afere` foram recriados — estavam
  em estado inconsistente (migration 0012 marcada como aplicada mas
  coluna `aceite_lgpd_base_legal` ausente, sequela de ciclo
  pré-reformatamento Marco 1). Causa-raiz consertada com novo script
  `docker/postgres/init/03-test-db.sh` (cria `test_afere`
  `OWNER=app_migrator`, extensões `pgcrypto`/`citext`/`pg_trgm`,
  `GRANT USAGE,CREATE` pro `app_user` no schema public **apenas no
  banco de teste** — runtime `afere` mantém `app_user` com só USAGE
  conforme ADR-0002). Procedimento manual documentado em
  `docs/faseamento/drill-f-b-saida.md` #3 agora é automatizado pelo
  init script (rodado uma vez quando volume `afere_db_data` nasce).

**Estado final desta sessão**: suíte **335 passed**, cobertura **87%**,
hooks **150/150** verdes, makemigrations limpo, drill `validar_f_a`
não-regredido (F-A intacta).

## Próximo passo (retomar) — tarefa ativa

**P4 continua — 15 T-CLI restantes**. Sequência sugerida da próxima
sessão:

1. T-CLI-107 (bus_outbox) + T-CLI-110 (worker em F-A) — completam
   `publicar_evento(outbox=True)` do helper (T-CLI-105 já levanta
   `OutboxNaoImplementado` aguardando esses dois)
2. T-CLI-104 (circuit breaker AcessoDadosCliente)
3. T-CLI-114..120 (US-CLI-006 inteira — pré-condição dogfooding PII real)
4. T-CLI-111 + T-CLI-112 (GET dedup compare + tipo_mesclagem +
   evidencia_documental_id)
5. T-CLI-106 (importação legada — alinhamento de origens completo no
   fluxo do use case)
6. T-CLI-108 + T-CLI-109 (payload Cliente.Bloqueado + predicate
   bloqueado_para_entrega) — gates de módulos futuros

P5 (10 auditores Família 5, loop até PASS zero CRÍTICO/ALTO/MÉDIO) só
quando P4 concluído e drill `validar_m1_clientes` (T-CLI a desenhar)
verde.

## Fila

#6 flake visão-360 ✅ + #7 lint sweep ✅ + #8 médios rodada 2 F-A ✅ +
Marco 1 P1+P2+P3 ✅ + T-CLI-103/101/113/102/105 ✅. Próxima:
T-CLI-107/110 (outbox+worker) → restantes (15 tarefas) → P5.
