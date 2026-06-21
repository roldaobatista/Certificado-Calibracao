---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: caixa-tecnico
tipo: tasks
relacionados:
  - docs/faseamento/caixa-tecnico/plan.md
  - docs/faseamento/caixa-tecnico/spec.md
---

# Tasks — frente `caixa-tecnico` (T-CT-NNN, derivado do plan)

> Status em tempo real: `[ ]` pendente · `[x]` feito (com data/onda/testes) · `[~]` parcial. Numeração em dezenas
> por fatia, com saltos para inserir tarefas intermediárias (molde `agenda`). Refs apontam para D-CT-N / INV-CT-* / AC-CT-* / R.
> **Pré-condição de início (T-CT-010+):** este plan (plan.md) como referência; T-CT-000 confirmou greenfield total.

## Fatia 1a — domínio puro (`src/domain/caixa_tecnico/`)

> ✅ **DONE (2026-06-17)** — 11 arquivos de domínio + teste; **79 testes verdes**, `ruff check`/`format`/`mypy` limpos.

- [x] **T-CT-010** `enums.py` — `CategoriaDespesa`(6 valores) / `TipoDespesa`(normal|estorno) / `EstadoDespesa`(4) /
  `EstadoAdiantamento`(5) / `MeioEntrega`(3) / `DirecaoPrestacao`(3). Todos `str, Enum`.
  **Criar:** `src/domain/caixa_tecnico/enums.py`.
  **AC:** `from src.domain.caixa_tecnico.enums import EstadoDespesa; EstadoDespesa('validada')` funciona.
  Ref: D-CT-2/3/7/8; spec §4.

- [x] **T-CT-011** `entities.py` — `CaixaTecnico`(raiz por técnico; campo `desligado_em: datetime|None` —
  fail-closed do consumer `colaborador.desligado`, D-CT-11/T-CT-050) / `Adiantamento` / `Despesa`(raiz) /
  `PrestacaoContas`(WORM) / `Politica`(por tenant) / `ConsentimentoGpsColaborador`(opt-in GPS colaborador-scoped,
  INSERT-com-vigência). Todos `@dataclass(frozen=True, slots=True)`. `Despesa.__post_init__`: `foto_hash is None`
  → levanta `FotoComprovanteObrigatoria` (INV-CT-FOTO-001).
  **Criar:** `src/domain/caixa_tecnico/entities.py`.
  **AC:** instanciar `Despesa` sem `foto_hash` → `FotoComprovanteObrigatoria`; com `foto_hash` → OK.
  Ref: D-CT-2/3/4/6/7/8; INV-CT-FOTO-001; spec §4.

- [x] **T-CT-012** `value_objects.py` — `Periodo(de, ate)` (valida `de<ate`); `Coordenada(lat, lng)` (opcional, valida
  limites geográficos); `ResultadoSaldo(total_adiantado, total_despesas, saldo_final, direcao)`. Reusa `Dinheiro`
  e `ReferenciaPIIAnonimizavel` de `src/domain/shared/value_objects.py`.
  **Criar:** `src/domain/caixa_tecnico/value_objects.py`.
  **AC:** `Periodo(ate=d1, de=d2)` com `d1 < d2` → `ValueError`; `Coordenada` com lat >90 → `ValueError`.
  Ref: D-CT-2/6; spec §4.

- [x] **T-CT-013** `regras/calcular_saldo.py` — `calcular_saldo(adiantamentos, despesas) -> ResultadoSaldo`
  (determinístico; Σ `entregues` − Σ `validadas`; `direcao` derivada automaticamente). `regras/deslocamento.py` —
  `valor_deslocamento(km_percorridos, tarifa_km) -> Dinheiro`.
  **Criar:** `src/domain/caixa_tecnico/regras/calcular_saldo.py` e `src/domain/caixa_tecnico/regras/deslocamento.py`.
  **AC:** `calcular_saldo([adiant_500], [despesa_300]) -> saldo=200, direcao=tenant_deve`; `valor_deslocamento(10, Dinheiro(150)) -> Dinheiro(1500)`.
  Ref: D-CT-2/9; INV-CT-SALDO-001; AC-CT-006-1.

- [x] **T-CT-014** `transicoes_despesa.py` — `_TRANSICOES: Mapping[EstadoDespesa, frozenset]` + `validar_transicao`
  (`pendente→validada`, `pendente→rejeitada`, `rejeitada→pendente`, `pendente→cancelada`; `validada` e
  `cancelada` são terminais). `transicoes_adiantamento.py` — idem para `EstadoAdiantamento` (`entregue`,
  `recusado`, `cancelado` são terminais; `entregue` levanta `AdiantamentoNaoCancelavel` se tentativa de cancelar
  — AC específico). Padrão A (molde `agenda/transicoes.py`).
  **Criar:** `src/domain/caixa_tecnico/transicoes_despesa.py` e `src/domain/caixa_tecnico/transicoes_adiantamento.py`.
  **AC:** `validar_transicao(EstadoDespesa.validada, EstadoDespesa.pendente)` → `TransicaoInvalida`;
  `rejeitada→pendente` → OK (reapresentação permitida); `entregue→cancelado` → `AdiantamentoNaoCancelavel`.
  Ref: D-CT-3/7; INV-CT-ADIAN-001; AC-CT-007-2.

- [x] **T-CT-015** `portas.py` — 5 Protocols `@runtime_checkable`: `FotoComprovanteStoragePort`,
  `OSReferenciaPort`, `ConsentimentoGpsPort`, `ColaboradorCaixaPort`, `ColaboradorReferenciadoPort`. `erros.py` —
  hierarquia completa (7 erros com HTTP status; ver plan §2).
  **Criar:** `src/domain/caixa_tecnico/portas.py` e `src/domain/caixa_tecnico/erros.py`.
  **AC:** `issubclass(FotoComprovanteStorageFake, FotoComprovanteStoragePort)` (runtime_checkable); todos os
  erros têm `http_status` correto.
  Ref: D-CT-4/5/6/12; spec §4.

- [x] **T-CT-016** `tests/test_caixa_tecnico_dominio_fatia1a.py` — cobre:
  (a) máquina estados despesa: happy `pendente→validada`; unhappy `validada→rejeitada` → `TransicaoInvalida`;
  reapresentação `rejeitada→pendente` → OK; `pendente→cancelada` → OK; todas transições proibidas parametrize;
  (b) máquina estados adiantamento: happy `solicitado→aprovado→entregue`; unhappy `entregue→cancelado` →
  `AdiantamentoNaoCancelavel`; `solicitado→recusado` OK; todas proibidas parametrize;
  (c) `calcular_saldo` com N operações mistas → consistência (`Σ entregues − Σ validadas`);
  (d) `valor_deslocamento` bordas (km=0, tarifa=0);
  (e) `Despesa` sem `foto_hash` → `FotoComprovanteObrigatoria` (INV-CT-FOTO-001);
  (f) `Periodo(de=d, ate=d)` → `ValueError` (mesma data inválida);
  (g) Protocols `runtime_checkable`;
  (h) `ResultadoSaldo` derivação automática de `direcao` (todos os 3 casos).
  **Criar:** `tests/test_caixa_tecnico_dominio_fatia1a.py`.
  **AC:** `pytest tests/test_caixa_tecnico_dominio_fatia1a.py --no-cov` verde, zero skips.
  Ref: INV-CT-FOTO-001 / INV-CT-ADIAN-001 / INV-CT-SALDO-001; **Verificação 1a**.

## Fatia 1b — schema PG (`src/infrastructure/caixa_tecnico/`)

> ✅ **DONE (2026-06-17)** — 6 models + 7 migrations (RLS v2 + WORM triggers + constraints) + repos + drill + `ACOES_CAIXA_TECNICO` na união. **16 testes verdes**; ruff/format/mypy + hooks de invariante (vigência/soft-delete/fk-pii/migration-rls) limpos. Tabelas: `caixa_tecnico`, `adiantamento_caixa`, `despesa_caixa`, `prestacao_contas_caixa`, `politica_caixa`, `consentimento_gps_colaborador`. **Débito menor (P9):** `0007_alter` só com help_text/blank — consolidar no `0001` numa limpeza futura.

- [x] **T-CT-020** `apps.py` (`app_label="caixa_tecnico"`; `ready()` com `# TODO Fatia 3b: registrar consumers`) +
  `models.py` (6 models achatados; `_choices(enum)`; `revision`; `foto_hash` NOT NULL em `Despesa`; `gps_lat`/
  `gps_lng` `DecimalField(null=True)` em `Despesa`; `desligado_em DateTimeField(null=True)` em `CaixaTecnico`
  (fail-closed do consumer — T-CT-050); `UNIQUE(tenant_id, tecnico_id)` em `CaixaTecnico`).
  **Criar:** `src/infrastructure/caixa_tecnico/apps.py` e `src/infrastructure/caixa_tecnico/models.py`.
  **AC:** `python manage.py check caixa_tecnico` sem erros; `foto_hash` NOT NULL no model.
  Ref: D-CT-1/2/3/6; spec §4.

- [x] **T-CT-021** `mappers.py` + `repositories.py` — `DjangoCaixaTecnicoRepository` + `DjangoDespesaRepository`
  + `DjangoAdiantamentoRepository` + `DjangoPrestacaoContasRepository` implementam Protocols de domínio.
  **Criar:** `src/infrastructure/caixa_tecnico/mappers.py` e `src/infrastructure/caixa_tecnico/repositories.py`.
  **AC:** instanciar `DjangoDespesaRepository()` sem erro; `isinstance(r, TituloRepository)` não aplicável — verificar
  que Protocol de domínio está implementado corretamente (duck-typing, sem falha de import).
  Ref: D-CT-1.

- [x] **T-CT-022** Migration `0001_initial` — CreateModel para as 6 tabelas + índices `(tenant_id, tecnico_id)` em
  `CaixaTecnico`, `(tenant_id, data)` em `Despesa`, `(tenant_id, colaborador_id, vigencia_inicio)` em
  `ConsentimentoGpsColaborador`. `UNIQUE(tenant_id, tecnico_id)` em `CaixaTecnico`.
  **Criar:** `src/infrastructure/caixa_tecnico/migrations/0001_initial.py`.
  **AC:** `docker compose exec app poetry run python manage.py migrate caixa_tecnico 0001 --database=migrator` sem erro;
  tabela `despesa` tem coluna `foto_hash NOT NULL`.
  Ref: D-CT-1/2; plan §3.

- [x] **T-CT-023** Migration `0002_rls_policies` — ENABLE ROW LEVEL SECURITY + FORCE ROW LEVEL SECURITY + 4 policies
  (`app.tenant_ids`/`app.active_tenant_id`) em **todas** as 6 tabelas (molde `contas_receber/migrations/0002_rls_policies.py`).
  **Criar:** `src/infrastructure/caixa_tecnico/migrations/0002_rls_policies.py`.
  **AC:** migration aplica; drill `validar_caixa_tecnico` confirma FORCE em todas as tabelas.
  Ref: D-CT-10; INV-TENANT-*.

- [x] **T-CT-024** Migration `0003_triggers_worm` — (a) trigger `caixa_tecnico_despesa_anti_mutacao` `BEFORE UPDATE OR
  DELETE ON caixa_tecnico_despesa FOR EACH ROW WHEN (OLD.status = 'validada')` → RAISE (molde
  `orcamentos/migrations/0003_triggers_worm.py`); (b) block-delete `despesa` **sempre** (nunca DELETE físico — molde
  `contas_receber titulo_receber_block_delete`); (c) `PrestacaoContas` WORM: INSERT-only nos campos financeiros
  (`total_adiantado`, `total_despesas_validadas`, `saldo_final`, `direcao`, `fechada_em`) — trigger bloqueia UPDATE nesses campos.
  **Criar:** `src/infrastructure/caixa_tecnico/migrations/0003_triggers_worm.py`.
  **AC:** migration aplica; `UPDATE caixa_tecnico_despesa SET status='pendente' WHERE status='validada'` via SQL direto →
  RAISE; UPDATE em `rejeitada` → OK (trigger não dispara — R3); DELETE em qualquer `despesa` → RAISE; UPDATE
  `total_adiantado` em `prestacao_contas` → RAISE.
  Ref: D-CT-3; INV-CT-IMUT-001; AC-CT-005-3.

- [x] **T-CT-025** Migration `0004_constraints` — (a) `UNIQUE(tenant_id, foto_hash) WHERE status NOT IN ('rejeitada',
  'cancelada')` — `tenant_id` **primeira coluna** (R1); (b) `UNIQUE(tenant_id, client_offline_id)` em `Despesa`
  (dedup batch per-item — D-CT-5).
  **Criar:** `src/infrastructure/caixa_tecnico/migrations/0004_constraints.py`.
  **AC:** migration aplica; INSERT de `foto_hash` repetida no mesmo tenant (status=pendente) → IntegrityError; INSERT
  de mesma `foto_hash` em tenant diferente → OK (R12); INSERT de `client_offline_id` repetido no mesmo tenant → IntegrityError.
  Ref: D-CT-4/5; INV-CT-FOTO-DEDUP-001 / INV-CT-IDEMP-001.

- [x] **T-CT-026** Migrations `0005_grants_app_user` + `0006_seed_authz` (ações `caixa_tecnico.*` × papéis) +
  bloco `ACOES_CAIXA_TECNICO` em `src/infrastructure/audit/acoes_canonicas.py` + **união em `ACOES_CANONICAS`**
  (9 slugs lowercase `caixa_tecnico.*`). **Editar arquivo existente** — não criar novo.
  **Editar:** `src/infrastructure/audit/acoes_canonicas.py`.
  **Criar:** `src/infrastructure/caixa_tecnico/migrations/0005_grants_app_user.py` e `0006_seed_authz.py`.
  **AC:** `from src.infrastructure.audit.acoes_canonicas import assert_acao_canonica; assert_acao_canonica('caixa_tecnico.despesa.lancada')` não levanta; `assert_acao_canonica('caixa_tecnico.prestacao.fechada')` não levanta (R4).
  Ref: D-CT-11; TL-CT-11; INV-008.

- [x] **T-CT-027** `management/commands/validar_caixa_tecnico.py` — drill estrutural: RLS enabled/force em todas as
  6 tabelas; ≥4 policies por tabela; trigger `caixa_tecnico_despesa_anti_mutacao` presente; block-delete `despesa`
  presente; WORM campos financeiros `prestacao_contas` presente; UNIQUE `foto_hash` com `tenant_id` primeiro;
  UNIQUE `client_offline_id`; grants `app_user`. + `tests/test_caixa_tecnico_schema_fatia1b.py` —
  cobre (todos `transaction=True`):
  (a) RLS ENABLE+FORCE+4 policies cross-tenant (INSERT em tenant A não visível de tenant B);
  (b) trigger anti-mutação: UPDATE `validada→pendente` via SQL direto → RAISE (R11);
  (c) trigger **não dispara** em UPDATE `rejeitada→pendente` (R3 — teste obrigatório TL-CT-05);
  (d) block-delete `despesa`: DELETE via SQL direto → RAISE; UPDATE `status=cancelada` → OK;
  (e) `PrestacaoContas` WORM: UPDATE `total_adiantado` via SQL direto → RAISE;
  (f) UNIQUE `foto_hash`: mesma foto mesmo tenant → IntegrityError; mesma foto tenant diferente → OK (R12);
  (g) UNIQUE `client_offline_id`: replay mesmo tenant → IntegrityError;
  (h) `validar_caixa_tecnico` verde (drill estrutural).
  **Criar:** `src/infrastructure/caixa_tecnico/management/commands/validar_caixa_tecnico.py` e `tests/test_caixa_tecnico_schema_fatia1b.py`.
  **AC:** `pytest tests/test_caixa_tecnico_schema_fatia1b.py --no-cov --reuse-db` verde, zero skips; `validar_caixa_tecnico` PASS.
  Ref: INV-CT-IMUT-001 / INV-CT-FOTO-DEDUP-001 / INV-CT-IDEMP-001; **Verificação 1b**.

## Fatia 2 — use cases + REST (núcleo autossuficiente; portas FAKE; NÃO toca módulo fechado)

> ✅ **DONE (2026-06-18)** — 10 use cases + 3 ViewSets + serializers (GPS read_only) + `/sync/despesas-lote` (per-item 207) + advisory lock no fechamento + idempotência REST; portas via `ports_stub.py` (Wave A). **24 testes E2E verdes**; ruff/format/mypy + hooks limpos. **Débito Fatia 3a:** `ports_stub.py` (stubs no infra) substituído por adapters reais (foto/GPS/OS/colaborador). Seed `0008` (ações reapresentar/sync).

- [x] **T-CT-030** `tests/fakes/caixa_tecnico_fakes.py` — fakes das 5 portas: `FotoComprovanteStorageFake`
  (armazena em dict em memória, retorna `foto_hash` determinístico); `OSReferenciaFake`; `ConsentimentoGpsFake`
  (configurável: opt-in on/off); `ColaboradorCaixaFake`; `ColaboradorReferenciadoFake`.
  **Criar:** `tests/fakes/caixa_tecnico_fakes.py`.
  **AC:** `isinstance(FotoComprovanteStorageFake(), FotoComprovanteStoragePort)` → True (runtime_checkable).
  Ref: D-CT-4/6/12; plan §4.

- [x] **T-CT-031** `lancar_despesa.py` — valida `foto_hash` (FAKE); calcula `valor_deslocamento` se
  `categoria=deslocamento`; lê opt-in GPS server-side (FAKE); `acima_limite` flag (não bloqueia); grava;
  publica `caixa_tecnico.despesa.lancada` no outbox dentro do `atomic`. + `reapresentar_despesa.py` —
  transição `rejeitada→pendente`; nova foto; audit do ciclo.
  **Criar:** `src/application/caixa_tecnico/lancar_despesa.py` e `src/application/caixa_tecnico/reapresentar_despesa.py`.
  **AC:** `lancar_despesa(sem_foto)` → `FotoComprovanteObrigatoria` 412; `lancar_despesa(deslocamento, km=10)` →
  `valor = km × tarifa`; opt-in GPS ausente → 403 mas despesa salva sem GPS; `reapresentar_despesa` → `pendente`.
  Ref: D-CT-4/5/6/9; INV-CT-FOTO-001 / INV-CT-IDEMP-001; AC-CT-002-1..6 / AC-CT-007-2.

- [x] **T-CT-032** `validar_despesa.py` (swipe valida; `pendente→validada`; publica `despesa.validada`) +
  `rejeitar_despesa.py` (swipe rejeita; motivo ≥30; `pendente→rejeitada`; publica `despesa.rejeitada`).
  **Criar:** `src/application/caixa_tecnico/validar_despesa.py` e `src/application/caixa_tecnico/rejeitar_despesa.py`.
  **AC:** `validar_despesa` → status `validada`; `rejeitar_despesa(motivo=curto)` → `TransicaoInvalida` 422
  (motivo inválido); `rejeitar_despesa(motivo_ok)` → `rejeitada`; tentar validar `validada` novamente → `TransicaoInvalida`.
  Ref: D-CT-3; INV-CT-IMUT-001; AC-CT-004-2 / AC-CT-007-1.

- [x] **T-CT-033** `solicitar_adiantamento.py` + `aprovar_adiantamento.py` + `recusar_adiantamento.py` +
  `entregar_adiantamento.py` — máquina de estados conforme D-CT-7; alçada `Politica.alcada_aprovacao`
  server-side em `aprovar`; recusar exige motivo; entregar = manual Wave A (PIX Wave B ADR-0050); tentativa de
  cancelar `entregue` → `AdiantamentoNaoCancelavel` 422.
  **Criar:** `src/application/caixa_tecnico/` (4 arquivos de use case).
  **AC:** `solicitado→aprovado→entregue` → OK; `entregue→cancelado` → 422; `solicitado→recusado(sem_motivo)` → 422;
  alçada incorreta → 403.
  Ref: D-CT-7; INV-CT-ADIAN-001; AC-CT-001-1..3.

- [x] **T-CT-034** `fechar_prestacao.py` — `pg_advisory_xact_lock(hash(tenant_id, tecnico_id))` (R6); `calcular_saldo`
  on-read; bloqueia novas despesas no período (`PERIODO_PRESTACAO_FECHADO` 422); grava `PrestacaoContas` WORM;
  publica `caixa_tecnico.prestacao.fechada` no outbox dentro do `atomic`; `direcao=tenant_deve` = estado
  consultável (sem execução de reembolso — GATE-CT-CONTAS-PAGAR).
  **Criar:** `src/application/caixa_tecnico/fechar_prestacao.py`.
  **AC:** fechar → `PrestacaoContas` com `saldo_final` correto; 2ª tentativa no mesmo período → 422; nova despesa
  no período fechado → 422; `caixa_tecnico.prestacao.fechada` no outbox.
  Ref: D-CT-8; INV-CT-PRESTACAO-001; AC-CT-006-1..2.

- [x] **T-CT-035** `sync_despesas_lote.py` — `POST /v1/caixa-tecnico/sync/despesas-lote`; valida `len ≤ 20` (413
  se exceder); `foto_base64` decode → `FotoComprovanteStoragePort` FAKE; atomicidade per-item (207 — 1 falha não
  trava lote); dedup `client_offline_id` (UNIQUE → retorna item existente, não duplica); LWW
  `(client_event_ts, device_id)`.
  **Criar:** `src/application/caixa_tecnico/sync_despesas_lote.py`.
  **AC:** lote de 3 → 207 com 3 resultados; lote de 21 → 413; 1 foto inválida no lote → 207 com erro só nesse item,
  restantes OK; replay do lote → 207 com itens existentes (sem duplicata).
  Ref: D-CT-5; INV-CT-IDEMP-001; AC-CT-002-2..3.

- [x] **T-CT-036** `serializers.py` — GPS `read_only=True` em serializers de escrita (nunca do payload — R5);
  `client_offline_id` aceito; `foto_base64` no serializer de lote. `views.py` — `DespesaViewSet` +
  `AdiantamentoViewSet` + `PrestacaoContasViewSet` + action `sync-lote`; `_aplicar_idempotencia` (molde
  `agenda/views.py`); `publicar_evento(outbox=True)` no `atomic`. `urls.py`.
  **Criar:** `src/infrastructure/caixa_tecnico/serializers.py`, `views.py`, `urls.py`.
  **AC:** `serializer.fields['gps_lat'].read_only == True`; endpoint `sync-lote` retorna 207.
  Ref: D-CT-5/6; INV-LGPD-CONSENT-001; AC-CT-002-5.

- [x] **T-CT-037** `tests/test_caixa_tecnico_api_fatia2.py` — cobre (todos `transaction=True`):
  lançar OK (201); sem foto → 412 (INV-CT-FOTO-001); `client_offline_id` replay → mesmo registro;
  `deslocamento` calcula valor; opt-in GPS ausente → 403 + despesa salva sem GPS;
  validar → `validada`; rejeitar motivo curto → 422; rejeitar OK → `rejeitada`;
  reapresentar → `pendente`; solicitar/aprovar/recusar/entregar adiantamento;
  fechar prestação → WORM; período fechado → nova despesa 422;
  sync lote OK (207); sync lote >20 → 413; lote parcial (1 ruim, resto aceita — 207);
  sem `Idempotency-Key` → 400/428; cross-tenant → 404;
  fechamento concorrente: 2 chamadas simultâneas → 1 fecha, 1 recebe 422 (advisory lock — INV-CT-PRESTACAO-001).
  **Criar:** `tests/test_caixa_tecnico_api_fatia2.py`.
  **AC:** `pytest tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db` verde, zero skips.
  Ref: INV-CT-FOTO-001 / INV-CT-IDEMP-001 / INV-CT-PRESTACAO-001 / INV-LGPD-CONSENT-001; **Verificação 2**.

## Fatia 3a — adapters reais (cross-módulo; R8 — skip hook + justificativa)

- [ ] **T-CT-040** `FotoComprovanteStorageLocal` (`src/infrastructure/caixa_tecnico/foto_storage.py`) — implementa
  `FotoComprovanteStoragePort`; pipeline: (1) valida JPG/PNG + MIME allowlist + ≤5MB; (2) Pillow EXIF strip;
  (3) `foto_hash = HMAC-SHA256(bytes_pós-strip, chave_tenant)` via helper `hashear_pii_com_salt_tenant`
  (ADR-0064); (4) content-address `media/caixa_tecnico/<tenant>/<hmac[:2]>/<hmac>`; (5) `if not exists` (idempotente).
  Molde `src/infrastructure/equipamentos/services_foto_storage.py`. Filesystem LOCAL (B2 = GATE pré-prod).
  **Criar:** `src/infrastructure/caixa_tecnico/foto_storage.py`.
  **AC:** foto JPG com EXIF GPS → bytes pós-strip sem EXIF GPS (teste EXIF-spoof — INV-LGPD-CONSENT-001);
  `foto_hash` = HMAC sobre bytes pós-strip (não pré-strip); replay não re-grava (`if not exists`);
  tipo TIFF → `FotoComprovanteObrigatoria`; >5MB → erro.
  Ref: D-CT-4; TL-CT-01/02/14; INV-CT-FOTO-001 / INV-CT-FOTO-DEDUP-001 / INV-LGPD-CONSENT-001.

- [ ] **T-CT-041** `ConsentimentoGpsAdapter` (`src/infrastructure/caixa_tecnico/consentimento_gps_adapter.py`) —
  implementa `ConsentimentoGpsPort`; lê `ConsentimentoGpsColaborador` (entidade no próprio `caixa_tecnico`);
  `opt_in_vigente(tenant, colaborador, na_data)` → verifica `vigencia_inicio ≤ na_data` + ausência de revogação.
  `ColaboradorCaixaAdapter` (`colaborador_caixa_adapter.py`) — implementa `ColaboradorCaixaPort` +
  `ColaboradorReferenciadoPort`; lê `PapelColaborador.TECNICO` via ORM de colaboradores (acoplamento de leitura —
  não estende módulo fechado); `esta_referenciado` verifica `CaixaTecnico`, `Despesa` (pendente/validada) ou
  `Adiantamento` (solicitado/aprovado/entregue) aberto.
  **Criar:** `src/infrastructure/caixa_tecnico/consentimento_gps_adapter.py` e `colaborador_caixa_adapter.py`.
  **AC:** `opt_in_vigente` com vigência ativa → True; revogado → False; `esta_referenciado` com despesa aberta → True; sem vínculos → False.
  Ref: D-CT-6/12; INV-LGPD-CONSENT-001 / INV-CT-REF-001; ADV-CT-06.

- [ ] **T-CT-042** `OSReferenciaAdapter` (`src/infrastructure/caixa_tecnico/os_referencia_adapter.py`) —
  implementa `OSReferenciaPort`; query `OrdemServico.objects.filter(tenant_id=..., id=os_id).exists()` (seam OS,
  leitura pura). Substituir stubs da view pelos 3 adapters reais em `apps.py:ready()`.
  **Criar:** `src/infrastructure/caixa_tecnico/os_referencia_adapter.py`. **Editar:** `apps.py`.
  **AC:** `existe_os` com OS real → True; UUID inexistente → False; OS de tenant diferente → False.
  Ref: D-CT-11; AC-CT-003-1.

- [ ] **T-CT-043** `tests/test_caixa_tecnico_adapters_fatia3a.py` — cobre:
  (a) `FotoComprovanteStorageLocal`: EXIF GPS stripado (foto com metadado GPS → pós-strip sem GPS — payload-spoof
  e EXIF-spoof rejeitados); `foto_hash` calculado sobre bytes pós-strip (não pré); foto idêntica cross-tenant →
  ambas aceitas (R12); foto idêntica mesmo tenant (status=pendente) → 409 (INV-CT-FOTO-DEDUP-001); tipo inválido → 422;
  (b) `ConsentimentoGpsAdapter`: vigente → True; revogado → False; NULL → False;
  (c) `ColaboradorCaixaAdapter.esta_referenciado`: com caixa ativo → True; sem vínculo → False;
  (d) `OSReferenciaAdapter`: OS existente → True; ausente → False; cross-tenant → False;
  (e) regressão Fatia 2 (adapters reais substituem FAKES — mesmos casos devem passar).
  **Criar:** `tests/test_caixa_tecnico_adapters_fatia3a.py`.
  **AC:** `pytest tests/test_caixa_tecnico_adapters_fatia3a.py tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db` verde.
  Ref: INV-CT-FOTO-DEDUP-001 / INV-CT-REF-001 / INV-LGPD-CONSENT-001; **Verificação 3a**.

## Fatia 3b — eventos e fan-out

- [ ] **T-CT-050** Confirmar `ACOES_CAIXA_TECNICO` + união em `ACOES_CANONICAS` (9 slugs — já feito em T-CT-026;
  verificar que nenhum slug foi omitido). Registrar consumer `colaborador.desligado` em
  `apps.py:ready()` (`try/except ValueError: pass` — molde `agenda/apps.py`) → `@consumer_idempotente` que marca
  `CaixaTecnico` como inativo + bloqueia novas operações; perfil do envelope (nunca do estado atual do tenant).
  **Editar:** `src/infrastructure/caixa_tecnico/apps.py` e `src/infrastructure/caixa_tecnico/consumers.py`.
  **AC:** `assert_acao_canonica('caixa_tecnico.prestacao.fechada')` não levanta (R4); consumer registrado sem
  levantar no `ready()`; re-registro do mesmo fn → `ValueError` capturado; fn diferente → acumula (fan-out).
  Ref: D-CT-11; INV-BUS-001; TL-CT-11.

- [ ] **T-CT-051** `tests/test_caixa_tecnico_eventos_fatia3b.py` — cobre:
  (a) `assert_acao_canonica` não falha para todos os 9 slugs `caixa_tecnico.*` (INV-008);
  (b) consumer `colaborador.desligado` idempotente (replay não duplica; molde ADR-0033);
  (c) fan-out não engole consumers existentes (R8 — verificar que `os.concluida` existente não é perdido);
  (d) perfil do envelope lido do evento (nunca `obter_perfil_tenant_corrente()` no worker);
  (e) publicação de `prestacao.fechada` dentro do `atomic` → outbox tem linha após commit.
  **Criar:** `tests/test_caixa_tecnico_eventos_fatia3b.py`.
  **AC:** `pytest tests/test_caixa_tecnico_eventos_fatia3b.py tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db` verde.
  Ref: INV-BUS-001 / INV-008; **Verificação 3b**.

## Fatia 3c — PDF da prestação (WeasyPrint)

- [ ] **T-CT-055** `pdf_prestacao.py` (`src/infrastructure/caixa_tecnico/pdf_prestacao.py`) — `gerar_pdf_prestacao`
  via WeasyPrint (existe: `pyproject:35` + molde `equipamentos/services_etiqueta.py`). Template HTML leve em
  `templates/caixa_tecnico/prestacao_pdf.html`. GPS **ausente** no PDF (retenção curta — AC-CT-002-7); só dados
  fiscais (valor, categoria, data, OS vinculada). Endpoint `GET /v1/caixa-tecnico/prestacoes/{id}/pdf/`
  (sob demanda; permissão técnico-próprio ou financeiro).
  **Criar:** `src/infrastructure/caixa_tecnico/pdf_prestacao.py` e `templates/caixa_tecnico/prestacao_pdf.html`.
  **Editar:** `src/infrastructure/caixa_tecnico/views.py` (action `pdf`). `src/infrastructure/caixa_tecnico/urls.py`.
  **AC:** `gerar_pdf_prestacao(prestacao, despesas, adiantamentos)` retorna bytes não-vazios; `Content-Type: application/pdf`; dados financeiros presentes; GPS ausente; cross-tenant → 404; outro técnico → 403.
  Ref: D-CT-8; TL-CT-03; AC-CT-006-2.

- [ ] **T-CT-056** `tests/test_caixa_tecnico_pdf_fatia3c.py` — cobre os AC acima + regressão fatias 1a/1b/2.
  **Criar:** `tests/test_caixa_tecnico_pdf_fatia3c.py`.
  **AC:** `pytest tests/test_caixa_tecnico_pdf_fatia3c.py tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db` verde; `bash .claude/hooks/_test-runner.sh` verde.
  Ref: **Verificação 3c**.

## Testes de INV adicionais (TL-CT-15 — 6 casos obrigatórios explícitos)

> Os 6 casos do tech-lead, consolidados em `tests/regressao/test_inv_ct_caixa_tecnico.py` (molde
> `tests/regressao/test_inv_ag_agenda.py` — TST-004 por ID, 1 caso nomeado por linha). Obrigatórios antes de
> fechar o módulo. Os 3 primeiros têm também cobertura natural nas fatias 1b/3a; aqui ficam explícitos e
> rastreáveis por INV-ID (não são duplicação — é a suíte de regressão de invariante).

- [ ] **T-CT-057** Reapresentação não dispara anti-mutação (INV-CT-IMUT-001): UPDATE `rejeitada→pendente` via
  ORM **não** levanta `DespesaValidadaImutavel`; UPDATE `validada→rejeitada` → RAISE.
  **Criar caso:** `test_reapresentacao_nao_dispara_trigger`. Ref: D-CT-3; TL-CT-05; INV-CT-IMUT-001.

- [ ] **T-CT-058** Foto idêntica cross-tenant coexiste (INV-CT-FOTO-DEDUP-001): 2 tenants; mesma foto em ambos →
  ambos aceitos; mesma foto no mesmo tenant (2ª vez) → 409.
  **Criar caso:** `test_foto_identica_cross_tenant_coexiste`. Ref: D-CT-4; TL-CT-02; INV-CT-FOTO-DEDUP-001.

- [ ] **T-CT-059** `foto_hash` sobre bytes pós-EXIF-strip (não pré): HMAC dos bytes pós-strip == `foto_hash` gravado.
  **Criar caso:** `test_foto_hash_sobre_bytes_pos_strip`. Ref: D-CT-4; ADV-CT-04; INV-CT-FOTO-DEDUP-001.

- [ ] **T-CT-060** Batch parcial (INV-CT-IDEMP-001): lote com 5 itens, 2 com foto inválida → 207 com 3 OK + 2
  erros; banco tem exatamente 3 despesas.
  **Criar caso:** `test_batch_parcial_per_item`. Ref: D-CT-5; TL-CT-06; INV-CT-IDEMP-001.

- [ ] **T-CT-061** Fechamento concorrente advisory lock (INV-CT-PRESTACAO-001): 2 threads simultâneas fecham
  prestação do mesmo `(tenant, tecnico)` → exatamente 1 commita (`fechada`), a outra recebe 422
  `PeriodoPrestacaoFechado`; banco tem exatamente 1 `PrestacaoContas` no período.
  **Criar caso:** `test_fechamento_concorrente_advisory_lock`. Ref: D-CT-2; TL-CT-10; INV-CT-PRESTACAO-001.

- [ ] **T-CT-062** EXIF GPS não vaza (INV-LGPD-CONSENT-001): foto JPG com EXIF GPS embutido → bytes armazenados
  sem tag GPS no EXIF (ou EXIF ausente).
  **Criar caso:** `test_exif_gps_nao_vaza`. Ref: D-CT-4/6; TL-CT-14; INV-LGPD-CONSENT-001; ADV-CT-03.

**Criar:** `tests/regressao/test_inv_ct_caixa_tecnico.py` (6 casos acima).
**AC:** `pytest tests/regressao/test_inv_ct_caixa_tecnico.py --no-cov --reuse-db` verde, zero skips.

## P8/P9 — fechamento

- [ ] **T-CT-070** P8: `docs/faseamento/caixa-tecnico/matriz-reconciliacao.md` — US↔código↔teste; INV-CT-*↔
  enforcement↔teste-com-ID (TST-004); reconciliação PRD↔spec: trigger na tabela `despesa` [AC-CT-005-3
  corrigido]; `direcao=tenant_deve` = estado consultável [D-CT-8]; GPS retenção própria curta [AC-CT-002-7];
  `ConsentimentoGpsPort` promovível a shared [nota, sem ADR agora]. Registrar GATE-CT-GPS-LGPD-OAB em
  `docs/governanca/gates-wave-a-consolidado.md` (D-CT-13 — bloqueante de produção). `STATUS-GERADO.md`
  (`bash scripts/status-projeto.sh --check`). Frontmatters spec/plan/tasks/prd → `stable`. Atualizar
  `docs/faseamento/plano-dependencia-sistema.md` (N5 — caixa-tecnico destrava app-tecnico N6 + custeio-real).
  **AC:** `status-projeto.sh --check` verde; GATE-CT-GPS-LGPD-OAB registrado; frontmatters `stable`.
  Ref: plan §8; spec §8 ações P3.2/P3.3.

- [ ] **T-CT-071** P9: mutirão de auditores roteados (INV-RITUAL-003). Roteamento:
  sempre: `auditor-seguranca`, `auditor-qualidade`, `auditor-llm-correctness`, `auditor-performance`,
  `auditor-observabilidade`, `auditor-idempotencia`. Condicional **SIM**: `auditor-conformidade-lgpd` (toca
  GPS/PII de colaborador). Condicional N/A: `auditor-supplychain` (não toca pyproject). `auditor-produto` no
  merge. MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial (R5/R6 do ritual — só auditores
  que tiveram MÉDIO+, restritos ao diff do conserto). Adversarial obrigatório em TODO achado MÉDIO+ antes do
  mutirão (R6).
  **AC:** 2ª passada sem MÉDIO+; módulo `caixa-tecnico` FECHADO — Wave A.
  Ref: plan §8; INV-RITUAL-001/003.
