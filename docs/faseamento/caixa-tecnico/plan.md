---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: caixa-tecnico
tipo: plan
proximo-passo: P4 — codar Fatia 1a (domínio puro, T-CT-010..016; não exige Docker/PG)
relacionados:
  - docs/faseamento/caixa-tecnico/spec.md
  - docs/faseamento/caixa-tecnico/reviews-consolidado.md
  - docs/faseamento/caixa-tecnico/tasks.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
  - docs/faseamento/contas-receber/plan.md
---

# Plan — frente `caixa-tecnico` (P3, derivado da spec P1+P2)

> Regra "não declarar pronto sem rodar" (feedback 2026-05-18): cada fatia tem **Verificação** executada em
> ambiente real antes de seguir. Greenfield total (T-CT-000 §2 confirmou zero linhas `caixa_tecnico` em `src/`).
> Molde técnico = `contas-receber` (vizinho financeiro FECHADO, path FLAT idêntico) + ritual `agenda` (referência
> de idempotência, eventos e estrutura de tasks).

## 0. Princípio de sequenciamento (ordem por dependência + anti-retrabalho)

Dependência interna: **domínio puro → schema PG (RLS + WORM + constraints) → use cases/REST (núcleo com
portas-FAKE) → adapters reais cross-módulo → eventos/fan-out → PDF → fechamento**. Peças compartilhadas
(`Dinheiro`, `ReferenciaPIIAnonimizavel`, `JanelaVigencia`, enums, transições) entram no domínio (Fatia 1a)
e são reusadas pelas fatias seguintes. O **núcleo (Fatia 2) entrega lançamento + validação + fechamento de
prestação SEM tocar nada fechado** (portas FAKE em `tests/fakes/` e stubs no infra). O que depende de tocar
módulo fechado (adapters OS/colaboradores/GPS) é Fatia 3a; eventos/fan-out é 3b; PDF é 3c. Mesma disciplina
do `contas-receber`.

## 1. Riscos e mitigações (cravados antes de codar)

| # | Risco | Sev | Mitigação | Origem |
|---|-------|-----|-----------|--------|
| R1 | `foto_hash` sem `tenant_id` na constraint → a mesma foto em tenants ≠ bloqueia (RLS não escopa constraint) | **CRIT** | `UNIQUE (tenant_id, foto_hash) WHERE status NOT IN ('rejeitada','cancelada')` — `tenant_id` **1ª coluna** (molde cicatriz TL-AGE-01); fotos idênticas cross-tenant coexistem; teste cross-tenant obrigatório | TL-CT-02 / INV-CT-FOTO-DEDUP-001 |
| R2 | `AnexoStoragePort` (PDF) usado para foto JPG/PNG → sem EXIF strip + hash errado | **CRIT** | Port próprio `FotoComprovanteStoragePort` (molde `equipamentos/services_foto_storage.py`); pipeline: JPG/PNG + MIME + ≤5MB + **EXIF strip** (Pillow) + `foto_hash = HMAC-SHA256(bytes_pós-strip, chave_tenant)` (ADR-0064). **Nunca `AnexoStoragePort`** | TL-CT-01 / D-CT-4 |
| R3 | Reapresentação `rejeitada→pendente` dispara trigger anti-mutação (UPDATE legítimo bloqueado) | ALTO | Trigger `WHEN (OLD.status = 'validada')` — **não** `WHEN OLD.status != 'pendente'`; teste explícito de reapresentação SEM disparo do trigger obrigatório | TL-CT-05 / D-CT-3 |
| R4 | `ACOES_CAIXA_TECNICO` não adicionada à `ACOES_CANONICAS` → `assert_acao_canonica` derruba todo publish | ALTO | Registrar frozenset + **união em `ACOES_CANONICAS`** no mesmo commit de `acoes_canonicas.py` (molde cicatriz TL-CR-11) | TL-CT-11 / D-CT-11 |
| R5 | GPS lido do payload ou do EXIF em vez do opt-in server-side | ALTO | `ConsentimentoGpsPort.opt_in_vigente` chamada no use case (server-side); serializer **não aceita** `gps_lat`/`gps_lng` do payload quando opt-in ausente; EXIF sempre stripado antes de qualquer uso (D-CT-6/INV-LGPD-CONSENT-001); teste de payload-spoof + EXIF-spoof | D-CT-6 / ADV-CT-01 |
| R6 | Dois fechamentos concorrentes para o mesmo `(tenant, tecnico)` congela saldos divergentes | ALTO | `pg_advisory_xact_lock(hash(tenant_id, tecnico_id))` no use case de fechamento (molde `contas-receber` advisory lock); teste de concorrência REAL (2 conexões, 1 commita, outra 422) | D-CT-2 / INV-CT-PRESTACAO-001 |
| R7 | Sync offline lote aceita mais de 20 itens sem limite → DoS / timeout | MÉDIO | `POST /v1/caixa-tecnico/sync/despesas-lote` valida `len(itens) <= 20` + tamanho total (413 se exceder); atomicidade per-item (207 — 1 foto ruim não trava o lote) | TL-CT-06 / D-CT-5 |
| R8 | Pré-commit em módulos fechados (OS/colaboradores) trava por hook de invariante em código legado | MÉDIO | Skip oficial + justificativa ≥10 chars no diff (não é mascaramento — memória `feedback_precommit_modulos_fechados`); stage seletivo; **nunca commits concorrentes**; pré-commit ~5min | R14 CR |
| R9 | `ConsentimentoGpsColaborador` duplicada vs. app-tecnico futuro (registro divergente) | MÉDIO | Entidade nasce no `caixa_tecnico` (G1 resolvido — molde D-AGE-15, override na própria frente); `ConsentimentoGpsPort` desenhada para **promoção a `shared`** — app-tecnico consumirá a **porta**, nunca a tabela; ADR curta diferida até app-tecnico nascer (spec §8 ação P3.2) | D-CT-6 / TL-CT-04 |
| R10 | Foto grande (≤5MB) + batch de 20 falha com out-of-memory no worker | MÉDIO | **Limite de honestidade** (TL-CT-15): sync offline de fotos grandes é net-new sem molde direto — teste de carga com falha de rede deve ser executado antes do 1º tenant pago em produção | TL-CT-15 |
| R11 | Drill anti-mutação em PG real não coberto por fixture | MÉDIO | **Limite de honestidade**: executar UPDATE/DELETE direto via `connection.execute(SQL)` (não ORM) em teste `transaction=True` para disparar o trigger de verdade; molde `test_contas_receber_schema_fatia1b.py` | INV-CT-IMUT-001 |
| R12 | Foto idêntica cross-tenant coexiste mas constraint não foi testada cross-tenant | MÉDIO | **Limite de honestidade**: criar 2 tenants no mesmo teste + inserir mesma foto em ambos → deve aceitar (constraint é por tenant) | TL-CT-02 / INV-CT-FOTO-DEDUP-001 |

## 2. Fatia 1a — domínio puro (`src/domain/caixa_tecnico/`)

Criar (molde `src/domain/shared/` + `src/domain/contas_receber/`):

- `enums.py` — `CategoriaDespesa`(combustivel|alimentacao|pedagio|hospedagem|peca|deslocamento),
  `TipoDespesa`(normal|estorno), `EstadoDespesa`(pendente|validada|rejeitada|cancelada),
  `EstadoAdiantamento`(solicitado|aprovado|entregue|recusado|cancelado), `MeioEntrega`(pix|transferencia|dinheiro),
  `DirecaoPrestacao`(tecnico_deve|tenant_deve|quitado). Todos `str, Enum`.
- `entities.py` — `CaixaTecnico`(raiz por técnico; campo `desligado_em: datetime|None` — fail-closed do consumer
  `colaborador.desligado`, D-CT-11/Fatia 3b), `Adiantamento`, `Despesa`(raiz), `PrestacaoContas`(WORM),
  `Politica`(por tenant), `ConsentimentoGpsColaborador`(opt-in GPS, colaborador-scoped, INSERT-com-vigência).
  Todos `@dataclass(frozen=True, slots=True)`. `Despesa.__post_init__`: valida `foto_hash is not None` →
  `FotoComprovanteObrigatoria`.
- `value_objects.py` — reusa `Dinheiro` (`src/domain/shared/value_objects.py`); `Periodo(de, ate)` (imutável,
  valida `de < ate`); `Coordenada(lat, lng)` (opcional, validada); `ResultadoSaldo(total_adiantado,
  total_despesas, saldo_final, direcao)` (puro). `ReferenciaPIIAnonimizavel` já existe em shared — reusa.
- `regras/calcular_saldo.py` — `calcular_saldo(adiantamentos, despesas) -> ResultadoSaldo` (determinístico;
  Σ entregues − Σ validadas).
- `regras/deslocamento.py` — `valor_deslocamento(km_percorridos, tarifa_km) -> Dinheiro` (puro).
- `transicoes_despesa.py` — `_TRANSICOES: Mapping[EstadoDespesa, frozenset]` + `validar_transicao`
  (pendente→validada, pendente→rejeitada, rejeitada→pendente, pendente→cancelada). Padrão A (molde `agenda/transicoes.py`).
- `transicoes_adiantamento.py` — `_TRANSICOES: Mapping[EstadoAdiantamento, frozenset]` + `validar_transicao`
  (solicitado→aprovado, aprovado→entregue, solicitado→recusado, solicitado→cancelado; `entregue` é estado
  terminal — `AdiantamentoNaoCancelavel` 422).
- `portas.py` (Protocols `@runtime_checkable`):
  - `FotoComprovanteStoragePort` — `validar_e_processar(bytes, mime) -> (bytes_limpos, foto_hash)`; `salvar(tenant_id, foto_hash, bytes_limpos) -> url`; `if_not_exists` (idempotente). **Não é `AnexoStoragePort`**.
  - `OSReferenciaPort` — `existe_os(os_id, tenant_id) -> bool` (seam OS, valida no lançamento).
  - `ConsentimentoGpsPort` — `opt_in_vigente(tenant_id, colaborador_id, na_data) -> bool` (server-side; promovível a `shared`).
  - `ColaboradorCaixaPort` — `e_tecnico(tenant_id, colaborador_id) -> bool`; dados mínimos.
  - `ColaboradorReferenciadoPort` — `esta_referenciado(tenant_id, colaborador_id) -> bool` (D-CT-12).
- `erros.py` — `FotoComprovanteObrigatoria`(412), `DespesaValidadaImutavel`(409), `FotoDuplicada`(409),
  `GpsConsentimentoAusente`(403, não bloqueia despesa), `AdiantamentoNaoCancelavel`(422),
  `PeriodoPrestacaoFechado`(422), `TransicaoInvalida`(422), `LoteExcedido`(413, batch >20 — D-CT-5),
  `CaixaTecnicoDesligado`(409, lançar/solicitar em caixa de técnico desligado — D-CT-11/consumer). [spec §4
  + erros derivados de D-CT-5 (lote) e D-CT-11 (desligamento)].

**Verificação 1a:** `pytest tests/test_caixa_tecnico_dominio_fatia1a.py --no-cov` — domínio puro, sem Django/PG.
Cobre: máquina de estados despesa (happy+unhappy+reapresentação `rejeitada→pendente`); máquina de estados
adiantamento (happy+unhappy+entregue-imutável); `calcular_saldo` após N operações mistas; `valor_deslocamento`;
`Despesa.__post_init__` sem `foto_hash` → `FotoComprovanteObrigatoria`; `Periodo` valida `de<ate`; `Coordenada`
validada; Protocols `runtime_checkable`.

## 3. Fatia 1b — schema PG (`src/infrastructure/caixa_tecnico/`)

Criar (molde `src/infrastructure/contas_receber/migrations/0001..0005` + `src/infrastructure/orcamentos/migrations/0003_triggers_worm.py`):

- `apps.py` — `CaixaTecnicoConfig` (`app_label = "caixa_tecnico"`); `ready()` com `# TODO Fatia 3b: registrar consumers`.
- `models.py` — `CaixaTecnico`, `Adiantamento`, `Despesa`, `PrestacaoContas`, `Politica`,
  `ConsentimentoGpsColaborador` (tabelas achatadas; `_choices(enum)`; `revision`). Campos GPS em `Despesa`:
  `gps_lat`/`gps_lng` como `DecimalField(null=True)` (retenção curta — AC-CT-002-7). `foto_hash` NOT NULL em
  `Despesa`. `foto_url` NOT NULL em `Despesa`.
- `mappers.py` + `repositories.py` (`DjangoCaixaTecnicoRepository`, etc., implementam Protocols).
- Migrations (sequência igual CR):
  - `0001_initial.py` — CreateModel + índices (`(tenant_id, tecnico_id)` em `CaixaTecnico`, `(tenant_id, data)` em `Despesa`). `UNIQUE(tenant_id, tecnico_id)` em `CaixaTecnico`.
  - `0002_rls_policies.py` — ENABLE+FORCE+4 policies em **TODAS** as tabelas (molde `contas_receber/migrations/0002_rls_policies.py`).
  - `0003_triggers_worm.py` — (a) `caixa_tecnico_despesa_anti_mutacao` `BEFORE UPDATE OR DELETE ON despesa FOR EACH ROW WHEN (OLD.status = 'validada')` → RAISE (molde `orcamentos/migrations/0003_triggers_worm.py`); (b) block-delete `despesa` **sempre** (toda despesa é documento fiscal, retenção 5a — nunca DELETE físico; molde `contas_receber titulo_receber_block_delete`); (c) `PrestacaoContas` WORM (campos congelados pós-fecha: INSERT-only ou trigger congela mutação dos campos financeiros).
  - `0004_constraints.py` — `UNIQUE(tenant_id, foto_hash) WHERE status NOT IN ('rejeitada','cancelada')` (**`tenant_id` primeira coluna** — R1/R12); `UNIQUE(tenant_id, client_offline_id)` em `Despesa` (per-item dedup batch — D-CT-5).
  - `0005_grants_app_user.py` — grants `app_user`.
  - `0006_seed_authz.py` — ações `caixa_tecnico.{solicitar_adiantamento,aprovar_adiantamento,entregar_adiantamento,recusar_adiantamento,lancar_despesa,validar_despesa,rejeitar_despesa,fechar_prestacao,ver}` × papéis.
- `audit/acoes_canonicas.py` — bloco `ACOES_CAIXA_TECNICO` (frozenset de slugs lowercase `caixa_tecnico.*`) **+ união em `ACOES_CANONICAS`** — editar o arquivo existente (não criar novo). Slugs: `caixa_tecnico.adiantamento.solicitado`/`.aprovado`/`.entregue`/`.recusado`/`.cancelado`, `caixa_tecnico.despesa.lancada`/`.validada`/`.rejeitada`, `caixa_tecnico.prestacao.fechada`.
- `management/commands/validar_caixa_tecnico.py` — drill: RLS enabled/force em todas as tabelas, ≥4 policies, trigger `caixa_tecnico_despesa_anti_mutacao` presente, block-delete `despesa` presente, WORM `prestacao_contas` presente, UNIQUE `foto_hash` com `tenant_id` primeiro, UNIQUE `client_offline_id`, grants.

**Nota sobre `EventoAuditoriaCaixa`:** GPS sensível **não** vai no payload geral do bus (dados de geolocalização pessoal do colaborador) — portanto a trilha de GPS fica na entidade `Despesa` com retenção própria curta (crypto-shredding AC-CT-002-7) e **não** é replicada no envelope de evento. A trilha de auditoria de ações segue via evento canônico WORM do bus (TL-CT-13 — sem `EventoAuditoriaCaixa` redundante).

**Verificação 1b:** `pytest tests/test_caixa_tecnico_schema_fatia1b.py --no-cov --reuse-db` (`transaction=True`). Cobre:
RLS ENABLE+FORCE+4 policies + isolamento cross-tenant; trigger `caixa_tecnico_despesa_anti_mutacao` bloqueia UPDATE em `validada` (SQL direto — R11); trigger **não dispara** em UPDATE `rejeitada→pendente` (reapresentação — R3); block-delete `despesa` sempre (UPDATE status=cancelada OK; DELETE direto → RAISE); `PrestacaoContas` INSERT-only (campos financeiros imutáveis); UNIQUE `foto_hash` por tenant (**mesma foto, mesmo tenant → 409; mesma foto, tenant diferente → aceita** — R12); UNIQUE `client_offline_id`; `validar_caixa_tecnico` verde.

## 4. Fatia 2 — use cases + REST (NÚCLEO autossuficiente; portas FAKE; não toca módulo fechado)

`src/application/caixa_tecnico/`:

- `lancar_despesa.py` — valida foto (porta FAKE na Fatia 2); `foto_hash` NOT NULL → 412 sem foto; calcula `valor_deslocamento` se `categoria=deslocamento`; `UNIQUE client_offline_id` (dedup per-item); lê opt-in GPS **server-side** (porta FAKE); `acima_limite` flag (não bloqueia); grava + publica `caixa_tecnico.despesa.lancada` no outbox dentro do `atomic`. Idempotência `Idempotency-Key` REST (molde `agenda/views.py`).
- `validar_despesa.py` (swipe valida) — transição `pendente→validada`; grava; publica `caixa_tecnico.despesa.validada`; bloqueia mutação via trigger PG (não código).
- `rejeitar_despesa.py` (swipe rejeita) — transição `pendente→rejeitada`; motivo ≥30 chars obrigatório; publica `caixa_tecnico.despesa.rejeitada`.
- `reapresentar_despesa.py` — transição `rejeitada→pendente`; nova foto (substitui `foto_hash`); grava; audit do ciclo.
- `solicitar_adiantamento.py` — transição `solicitado`; justificativa ≥30; alçada `Politica.alcada_aprovacao` server-side.
- `aprovar_adiantamento.py` / `recusar_adiantamento.py` / `entregar_adiantamento.py` — transições conforme máquina; recusar exige motivo; entregar = manual Wave A (PIX automático Wave B ADR-0050).
- `fechar_prestacao.py` — **advisory lock** `pg_advisory_xact_lock(hash(tenant_id, tecnico_id))` por `(tenant, tecnico)` (R6); calcula `calcular_saldo` on-read; bloqueia novas despesas no período (`PERIODO_PRESTACAO_FECHADO` 422); grava `PrestacaoContas` WORM; publica `caixa_tecnico.prestacao.fechada` no outbox dentro do `atomic`; `direcao=tenant_deve` = estado consultável (G4 fail-open lazy — sem execução de reembolso).
- `sync_despesas_lote.py` — `POST /v1/caixa-tecnico/sync/despesas-lote`; valida `len(itens) <= 20` (413); `foto_base64` decodifica + envia ao `FotoComprovanteStoragePort` FAKE; atomicidade per-item (207); dedup por `client_offline_id`; LWW `(client_event_ts, device_id)`.

`src/infrastructure/caixa_tecnico/`:

- `serializers.py` — GPS **nunca aceito do payload** (campos `gps_lat`/`gps_lng` `read_only=True` no serializer de escrita — D-CT-6/R5); `client_offline_id` aceito; `Idempotency-Key` do header.
- `views.py` — `CaixaTecnicoViewSet` + `AdiantamentoViewSet` + `DespesaViewSet` + `PrestacaoContasViewSet` + action `sync-lote`; `_aplicar_idempotencia` (molde `agenda/views.py`); `publicar_evento(outbox=True)` no `atomic`.
- `urls.py`.
- `tests/fakes/caixa_tecnico_fakes.py` — fakes das portas: `FotoComprovanteStorageFake`, `OSReferenciaFake`, `ConsentimentoGpsFake`, `ColaboradorCaixaFake`.

**Verificação 2:** `pytest tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db` (`transaction=True`). Cobre:
lançar despesa OK (201); sem foto → 412; `client_offline_id` replay → mesmo registro (IDEMP); categoria `deslocamento` calcula valor; opt-in GPS ausente → 403 mas despesa segue; validar → `validada`; rejeitar motivo curto → 422; rejeitar OK → `rejeitada`; reapresentar → `pendente`; solicitar adiantamento; aprovar; recusar motivo ausente → 422; fechar prestação → WORM; período fechado → nova despesa 422; sync lote OK (207); sync lote > 20 → 413; lote parcial (1 foto ruim, resto aceita — 207); sem `Idempotency-Key` → 400/428; cross-tenant → 404.

## 5. Fatia 3a — adapters reais (cross-módulo)

> **R8:** commits desta fatia tocam módulos fechados (`ordens_servico`, `colaboradores`) → pré-commit pode pegar hook de invariante em código legado; resolver com skip oficial + justificativa. Stage seletivo; nunca commits concorrentes.

- `FotoComprovanteStorageLocal` (`src/infrastructure/caixa_tecnico/foto_storage.py`) — implementa `FotoComprovanteStoragePort`; molde `src/infrastructure/equipamentos/services_foto_storage.py`: (1) valida JPG/PNG + MIME allowlist + ≤5MB; (2) `Pillow` EXIF strip (`ImageOps.exif_transpose` + salvar sem EXIF); (3) `foto_hash = HMAC-SHA256(bytes_pós-strip, chave_tenant)` — helper `hashear_pii_com_salt_tenant` (`src/infrastructure/authz/perfil_tenant_helper.py`) ou equivalente de ADR-0064; (4) content-address por-tenant `media/caixa_tecnico/<tenant>/<hmac[:2]>/<hmac>`; (5) storage filesystem LOCAL (G3 — B2 = GATE pré-prod); `if not exists` (idempotente por hash — replay não re-grava). **Nunca `AnexoStoragePort`.**
- `ConsentimentoGpsAdapter` (`src/infrastructure/caixa_tecnico/consentimento_gps_adapter.py`) — implementa `ConsentimentoGpsPort`; lê `ConsentimentoGpsColaborador` (entidade no próprio `caixa_tecnico` — G1); `opt_in_vigente(tenant, colaborador, na_data)` → verifica vigência e ausência de revogação. **IA nunca grava opt-in** — só fluxo de RH/colaborador.
- `OSReferenciaAdapter` (`src/infrastructure/caixa_tecnico/os_referencia_adapter.py`) — implementa `OSReferenciaPort`; query `OrdemServico.objects.filter(tenant_id=..., id=os_id).exists()` (seam OS — leitura pura; não estende módulo fechado). Non-goal: despesa **não segue** cancelamento da OS (rastro histórico — D-CT-11).
- `ColaboradorCaixaAdapter` (`src/infrastructure/caixa_tecnico/colaborador_caixa_adapter.py`) — implementa `ColaboradorCaixaPort` + `ColaboradorReferenciadoPort`; lê `PapelColaborador.TECNICO` via ORM de colaboradores (acoplamento de leitura — aceitável, molde `ColaboradorAgendaAdapter`). `esta_referenciado` verifica se colaborador tem `CaixaTecnico`, `Despesa` ou `Adiantamento` aberto (D-CT-12/INV-CT-REF-001).

Substituir stubs da view pelos adapters reais no `apps.py:ready()`.

**Nota sobre `ConsentimentoGpsPort` → `shared`:** a porta está desenhada para promoção a `shared` quando o `app-tecnico` (N6) nascer — ele consumirá **a porta**, nunca a tabela do `caixa_tecnico`. Registrar como nota em `docs/adr/INDICE.md` (sem ADR nova agora — spec §8 ação P3.2 diferida).

**Verificação 3a:** `pytest tests/test_caixa_tecnico_adapters_fatia3a.py tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db`.
Cobre: `FotoComprovanteStorageLocal` — EXIF strip remove GPS (spoof EXIF-GPS → não vaza); HMAC-tenant (bytes pós-strip, não pré); foto idêntica cross-tenant coexiste; foto idêntica mesmo tenant → 409; tipo inválido → 422; `OSReferenciaAdapter` retorna `True`/`False` correto; `ConsentimentoGpsAdapter` opt-in vigente/revogado; `ColaboradorCaixaAdapter.esta_referenciado` bloqueia hard-delete; regressão Fatia 2.

## 6. Fatia 3b — eventos e fan-out (`acoes_canonicas.py` + consumers)

- `src/infrastructure/audit/acoes_canonicas.py` — adicionar `ACOES_CAIXA_TECNICO` + **união em `ACOES_CANONICAS`** (já feito na 1b — verificar que nada foi omitido; re-confirmar todos os 9 slugs).
- Consumers `@consumer_idempotente` registrados no `apps.py:ready()` (cada `registrar_consumer` em `try/except ValueError: pass` — molde `agenda/apps.py`):
  - Reavaliação `colaborador.desligado` (spec §6 ação P3, D-CT-11): **registrar consumer** `colaborador.desligado` que marca `CaixaTecnico` como desligado + bloqueia novas operações (fail-closed, audit); implementar em Wave A (técnico desligado não deve ter caixa ativo).
  - **Sem consumer de `os.*`** em Wave A: vínculo `os_id` é validado on-write via `OSReferenciaPort` (não fan-out — D-CT-11 reduz acoplamento).
- Publicação de `caixa_tecnico.prestacao.fechada` dentro do `atomic` (outbox): já feito no use case `fechar_prestacao.py` (Fatia 2) — verificar que o consumer de `contas-pagar` futuro conseguirá fazer backfill por query das prestações `tenant_deve` não-reembolsadas (GATE-CT-CONTAS-PAGAR — D-CT-8).

**Verificação 3b:** `pytest tests/test_caixa_tecnico_eventos_fatia3b.py tests/test_caixa_tecnico_api_fatia2.py --no-cov --reuse-db`.
Cobre: `assert_acao_canonica` não falha para todos os 9 slugs; consumer `colaborador.desligado` idempotente (replay não duplica); fan-out não engole consumers existentes (R8 molde CR); perfil do envelope lido do evento (nunca do estado atual do tenant); regressão Fatia 2.

## 7. Fatia 3c — PDF da prestação (WeasyPrint)

- `src/infrastructure/caixa_tecnico/pdf_prestacao.py` — `gerar_pdf_prestacao(prestacao: PrestacaoContas, despesas, adiantamentos) -> bytes`. WeasyPrint existe (`pyproject:35` + molde `equipamentos/services_etiqueta.py`). Template HTML leve em `templates/caixa_tecnico/prestacao_pdf.html`. **Dado estruturado é a fonte WORM; PDF é projeção on-demand (não persistido como fonte, regenerável a qualquer momento)** — TL-CT-03/D-CT-8.
- Endpoint `GET /v1/caixa-tecnico/prestacoes/{id}/pdf/` — renderiza sob demanda; permissão técnico-próprio ou financeiro.
- GPS não vai no PDF (retenção própria curta — AC-CT-002-7); apenas dados fiscais (valor, categoria, data, OS vinculada).

**Verificação 3c:** `pytest tests/test_caixa_tecnico_pdf_fatia3c.py --no-cov --reuse-db`. Cobre: PDF gerado (bytes não-vazios); cabeçalho tem `Content-Type: application/pdf`; dados financeiros presentes; GPS ausente no PDF; cross-tenant → 404; técnico-próprio OK; outro técnico → 403.

## 8. P8/P9 — fechamento

- **P8:** `matriz-reconciliacao.md` (US↔código↔teste; INV-CT-*↔enforcement↔teste-com-ID; reconciliação PRD↔spec:
  trigger é na tabela `despesa` [corrigido AC-CT-005-3]; `direcao=tenant_deve` = estado consultável [D-CT-8];
  GPS = retenção própria curta [AC-CT-002-7]; `ConsentimentoGpsPort` promovível a shared). `STATUS-GERADO.md`
  (`status-projeto.sh --check`). Frontmatters spec/plan/tasks → `stable`. Registrar GATE-CT-GPS-LGPD-OAB em
  `gates-wave-a-consolidado.md` (D-CT-13). Atualizar `plano-dependencia-sistema.md` (N5 — caixa-tecnico
  destrava app-tecnico N6 e custeio-real).
- **P9:** mutirão de auditores roteados (INV-RITUAL-003). Sempre: seguranca, qualidade, llm-correctness,
  performance, observabilidade, idempotencia. Condicionais: conformidade-lgpd (**SIM** — toca GPS/PII de
  colaborador); supplychain (só se tocar pyproject — improvável). Produto no merge. MÉDIO+ bloqueia
  (INV-RITUAL-001); 2ª passada escopada + adversarial (R5/R6 do ritual).

## 9. Non-goals do plan

Não construir: execução de reembolso PIX/transferência (GATE-CT-CONTAS-PAGAR); execução de devolução
técnico-deve (GATE-CT-DEVOLUCAO-EXEC); OCR de recibo (GATE-CT-OCR); cartão corporativo Pluggy; PIX
instantâneo (ADR-0050 Wave B); app Flutter offline (ADR-0009 — só endpoints idempotentes); custeio/margem
real da OS (Wave B); anti-fraude semântica de foto (crop/re-foto muda hash — non-goal); múltiplas moedas;
adiantamento via folha; desconto em folha; `EventoAuditoriaCaixa` redundante ao bus (TL-CT-13); ADR nova
para `ConsentimentoGpsPort` (diferida ao nascer app-tecnico). RAT/DPIA/minutas GPS CONGELADOS
(GATE-LGPD-RAT-CONSOLIDACAO — R17).
