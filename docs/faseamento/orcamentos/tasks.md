---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
proximo-passo: MÓDULO 100% Wave A FECHADO (Fatia 2 Ondas 2a-2f + P8/P9 + T-ORC-039 Templates). US Wave B: 003/006/010
diataxis: reference
audiencia: [agente, auditor]
frente: orcamentos
tipo: tasks
relacionados:
  - docs/faseamento/orcamentos/plan.md
  - docs/faseamento/orcamentos/spec.md
---

# Tasks — frente `orcamentos` (módulo novo, 1ª ponta de receita)

> T-ORC-NNN. Fatias do `plan.md`. Cada fatia fecha com verificação real antes da próxima.
> Refs: D-ORC-* (spec §3), INV-ORC-* (spec §5), seams (spec §11), TL-ORC-* / ADV-ORC-* (reviews).
> **Greenfield** — a ponta da OS já existe (envelope por item, ADR-0082).

## Fatia 1a — domínio puro (`src/domain/comercial/orcamentos/`) — ✅ DONE 2026-06-14 (45 testes; Dinheiro VO)

- [ ] **T-ORC-010** `enums.py` — `EstadoOrcamento` (8 estados D-ORC-3), `TipoAtividadeAlvo`
      (calibracao/manutencao/instalacao/verificacao/vistoria — SEM `outro`, D-ORC-16),
      `VeredictoAnaliseCritica`, `CanalAprovacao`. Ref: D-ORC-3/16.
- [ ] **T-ORC-011** `value_objects.py` — reuso `Dinheiro`/`Desconto`/`CondicoesPagamento` + `JanelaVigencia`
      (shared) + import `PrecoResolvido` (pps) + `ReferenciaPIIAnonimizavel` (shared). Ref: D-ORC-1/4.
- [ ] **T-ORC-012** `entities.py` — `Orcamento` (raiz) + `VersaoOrcamento` + `ItemOrcamento` (`equipamento_id?`
      + carimbo preço SEM margem/custo) + `LinkPublico` + `Aprovacao` (hash aprovador + aceite rico) +
      `AnaliseCriticaOrcamento` + `Template`. Ref: spec §4; D-ORC-15/17; INV-ORC-MARGEM-OFF.
- [ ] **T-ORC-013** `erros.py` — 8 erros com http_status (spec §4). `repository.py` — Protocols
      `OrcamentoRepository`+`TemplateRepository` (sem Django).
- [ ] **T-ORC-014** `transicoes.py` — máquina de estados D-ORC-3 (válidas+proibidas; convertido terminal) +
      `traduzir_tipo_atividade_alvo` (mapa fechado D-ORC-16) + `montar_envelope_orcamento_aprovado` (função pura
      → dict do payload por item; base do INV-ORC-APROVADO-ENVELOPE). Ref: D-ORC-3/6/16.
- [ ] **T-ORC-015** Testes puros (`tests/test_orcamentos_dominio.py`): estados happy/unhappy; tradução enum;
      bifurcação item calibração(equip)→atividade × comercial(sem equip)→linha; envelope montado correto;
      preço sem margem. ruff/mypy limpos.

## Fatia 1b — schema PG (`src/infrastructure/orcamentos/`) — ✅ DONE 2026-06-14 (drill 20/20; ruff/mypy limpos)

> **Decisões de schema (Opus — reconciliação P8):**
> - **`item_orcamento.versao` FK NOT NULL, SEM `orcamento_id`** — espelha a entidade `ItemOrcamento.versao_id`
>   (que não tem `orcamento_id`). A versão corrente nasce na criação do orçamento (snapshot={}) e CONGELA ao
>   enviar (one-shot). O orçamento deriva via `versao.orcamento`. (Decisão inicial item↔orcamento revertida.)
> - **`versao_orcamento` = WORM congelamento one-shot** (não Padrão B puro): trigger permite preencher snapshot
>   vazio→cheio 1×, setar `revogado_em`; bloqueia re-edição do snapshot, mudança de núcleo e DELETE.
>   `aprovacao`/`analise_critica_orcamento` continuam INSERT-only puro.
> - **Monetário** persistido como `*_centavos` + `moeda`; `preco_resolvido`/`itens_avaliados`/`snapshot` em jsonb.
> - **Tabelas:** `orcamento_link_publico`/`orcamento_aprovacao` prefixados (evita colisão no schema global).

- [x] **T-ORC-020** `apps.py` (label `orcamentos`) + `models.py` — 7 tabelas, `tenant` FK NOT NULL, índices;
      ReferenciaPIIAnonimizavel no orçamento (cliente) + aprovação (aprovador, HMAC). Ref: spec §4; D-ORC-2/4.
- [x] **T-ORC-021** Migration `0001_initial` (7 models). `makemigrations --check` limpo.
- [x] **T-ORC-022** Migration `0002_rls_policies` — RLS v2 (ENABLE+FORCE + 4 policies) nas 7 tabelas +
      `0005_grants_app_user` (GRANT separado, molde precificacao). Ref: INV-TENANT-001/002/003.
- [x] **T-ORC-023** Migration `0003_triggers_worm` — `aprovacao`+`analise` INSERT-only puro; `versao` congelamento
      one-shot (ver decisão acima). `reverse_sql` completo. Ref: INV-ORC-APROVACAO-WORM / ANALISE-WORM / D-ORC-8.
- [x] **T-ORC-024** Migration `0004_constraints` — partial unique `orcamento_link_publico` (1 ativo WHERE
      revogado_em IS NULL) + trigger estado terminal (não CHECK — transição exige OLD vs NEW) + unique `numero`
      por tenant + CHECK bifurcação item. Ref: INV-ORC-LINK-TOKEN / CONVERTIDO-TERMINAL / EQUIP-ITEM.
- [x] **T-ORC-025** Migration `0006_seed_authz` — 9 ações `orcamento.*` × 5 perfis (27 linhas; `ver_margem`
      restrito a admin/gerente). + conftest `_SEED_MIGRATIONS` (re-seed após TRUNCATE transacional). Ref: D-ORC-12.
- [x] **T-ORC-025b** (TL-ORC CRIT-1) `audit/acoes_canonicas.py` — bloco `ACOES_ORCAMENTOS` (7 eventos lowercase)
      + union `ACOES_CANONICAS`. **CORREÇÃO (REGRA #0): a migration `0007_acoes_orcamentos_check` era
      DESNECESSÁRIA** — o CHECK `bus_outbox_acao_enum_semantico` é puramente SINTÁTICO (regex de formato slug,
      só na `audit/0011`), não enumera valores; nenhum dos ~14 módulos pós-0011 criou migration de CHECK ao
      adicionar ações. Os slugs `orcamento.*` já passam no CHECK existente. Ref: spec §6.
- [x] **T-ORC-026** `repositories.py` + `mappers.py` — adapters dos Protocols (CRUD + WORM INSERT; round-trip
      Dinheiro/JanelaVigencia/PrecoResolvido/CondicoesPagamento). **`get_link_por_token` (lookup SEM RLS,
      D-ORC-19) DIFERIDO para Fatia 2** (endpoint público; exige SECURITY DEFINER/tabela-índice). **Numeração
      via `SerieDocumento` é orquestração do use case `criar_orcamento` (Fatia 2)** — a 1b crava a constraint
      `uq_orcamento_numero_tenant` (defesa de banco). Ref: spec §11; D-ORC-18.
- [x] **T-ORC-027** **Drill em banco COM dados** (`tests/test_orcamentos_schema.py`, PG-real, **20 testes**):
      RLS FORCE+UNHAPPY cross-tenant nas 7 tabelas; WORM UPDATE/DELETE RAISE; versão congelamento one-shot;
      partial unique link; unique numero/tenant; CHECK bifurcação; estado terminal; seed authz. `auditor-seguranca`.

## Fatia 2 — use cases + consumers + REST

> **Preparação (2026-06-14 — briefing dos 12 seams + investigação REGRA #0):**
> Seams verificados (paths/assinaturas): `calcular_precos` (injetável; deps montadas na view via
> `_construir_resolver_com_tabela_padrao` — `precificacao/views.py:164`); `ItemCalculado` (preco_base
> `PrecoResolvido`, preco_final `Decimal`, desconto_pct `Percentual`, semaforo `Semaforo`; margem/custo
> `Decimal|None` — NÃO persistir); `SerieDocumento` (`reservar_numero`/`confirmar_numero` — `serie.py`);
> cliente bloqueado (`Cliente.bloqueado` property + `ClienteBloqueio`); análise crítica (`escopos_cmc.cobre`,
> `procedimentos.cobre_procedimento`/`vigente_em`, `perfil_tenant_helper.tenant_perfil_e`); `publicar_evento`
> (`audit/event_helpers` — cadeia+outbox, idempotência por `(causation_id,acao)`); idempotência REST
> (`_aplicar_idempotencia` — `precificacao/_views_suporte.py`); rate-limit (`equipamentos/services_ratelimit`
> `avaliar_limite_ip`); consumer (`@consumer_idempotente` — `bus/consumer_base`; `registrar_consumer` —
> `audit/outbox_worker`); HMAC PII (`calibracao/lgpd` `derivar_*`); canonicalização ADR-0029
> (`domain/metrologia/calibracao/hash_versionado` `canonicalizar_payload_para_hmac`).
>
> **DECISÕES (REGRA #0):**
> - **D-FATIA2-A — Numeração = BURACOS_ACEITOS** (NÃO gap-less). O regime é DERIVADO do tipo
>   (`regime_numeracao_do_tipo`, ADR-0080 fixa gap-less só p/ fatura/certificado — exigência fiscal/ISO).
>   Reconcilia D-ORC-18: buracos só ocorrem em ROLLBACK de criação (falha rara) — não em cancelamento —
>   logo na prática a numeração é sequencial limpa. Diferença com gap-less é desprezível; evita mexer no
>   motor central (configuracoes_sistema fechado). **Roldão pode pedir gap-less se quiser nº 100% garantido.**
> - **D-FATIA2-B — Provisionamento de série LAZY.** `serie_documento` está VAZIA (Wave A não fez onboarding
>   de séries). `criar_orcamento` faz obter-ou-criar a série de orçamento do tenant (advisory lock, idempotente)
>   antes de `reservar_numero`. Confirmar API `criar_serie`/`obter` de configuracoes_sistema na implementação.
> - **D-FATIA2-C — Arquitetura use-case×view (TL-ORC ALTO-2).** A VIEW (infra) monta as deps de
>   `calcular_precos`, chama-o, e passa o `ItemCalculado` resolvido ao use case `adicionar_item` (fino), que
>   persiste SÓ PrecoResolvido+preco_final+desconto_pct+semaforo (INV-ORC-MARGEM-OFF). Use case NÃO instancia
>   repos de precificacao.

- [ ] **T-ORC-030** `criar_orcamento` — cliente ativo/não-bloqueado (D-ORC-4); numero (buracos-aceitos via
      SerieDocumento, D-FATIA2-A/B); rascunho + VersaoOrcamento V1 snapshot={}. Ref: AC-ORC-001.
- [ ] **T-ORC-031** `adicionar_item`/`editar_item` — `calcular_precos` (cesta) → persiste SÓ `PrecoResolvido`+
      `preco_final`+`desconto_pct`+`semaforo` (INV-ORC-MARGEM-OFF); `equipamento_id` no item calibração;
      rejeita tabela expirada (422). **(TL-ORC ALTO-2)** deps de `calcular_precos` montadas na VIEW (infra),
      reusando `_construir_resolver_com_tabela_padrao` (`precificacao/views.py:164`) — anti-N+1 `tabela_padrao`
      1x/request; NÃO instanciar repos no use case. Ref: D-ORC-1/10; TL-ORC-06/09; AC-ORC-001/004.
- [ ] **T-ORC-032** `enviar_orcamento` — `VersaoOrcamento` V1 (snapshot) + `LinkPublico` (token urlsafe ≥128b,
      ADV-ORC-08a) + publica `Orcamento.Enviado`. Ref: D-ORC-7/8; AC-ORC-002/003.
- [x] **T-ORC-033** ✅ DONE 2026-06-15 (Onda 2c-2) `aprovar_orcamento` — análise crítica cl. 7.1 perfil-aware (D-ORC-5: portas CMC+procedimento
      por grandeza/faixa do equipamento; A fail-closed / B ressalva-média / C ressalva-baixa / D off; perfil
      indeterminado fail-closed) → grava `AnaliseCriticaOrcamento` WORM com **`itens_avaliados` ricos
      (procedimento_id/codigo/versão + cmc_codigo_ref — C1), `norma_referencia` (C6), `avaliada_por`
      (`user_id` interno OU `"SISTEMA/AUTO"`+`aprovacao_id` no público — C5)** + snapshot_hash (canonicalização
      ADR-0029) → `aprovado_pendente_os` → publica `orcamento.aprovado` (envelope por item D-ORC-6, lowercase) +
      `orcamento.analise_critica_reprovada`/`_com_ressalva` (com `severidade`). Idempotente. Ref: D-ORC-5/6/14/15;
      INV-ORC-CL71-001 / APROVADO-ENVELOPE / ANALISE-WORM; AC-ORC-007/009.
- [ ] **T-ORC-034** `recusar_orcamento` / `cancelar_orcamento` (409 se convertido) + `expirar_orcamentos`
      (job idempotente por orcamento_id + timezone tenant). Ref: D-ORC-3; INV-ORC-CONVERTIDO-TERMINAL / EXP-001;
      AC-ORC-008.
- [x] **T-ORC-035** ✅ DONE 2026-06-15 (Onda 2d) Consumer `handle_os_aberta` — lê `envelope["payload"]["orcamento_id"]`; **se ausente/None
      → no-op (OS avulsa também publica `os.aberta` — TL-ORC ALTO-1)**; senão `aprovado_pendente_os→convertido`
      + publica `orcamento.convertido`. `@consumer_idempotente`. Ref: D-ORC-14; AC-ORC-007.
- [x] **T-ORC-036** ✅ DONE 2026-06-15 (Onda 2d) Consumer `handle_cliente_anonimizado` — por estado (rascunho
      **cancela**; **enviado EXPIRA** — decisão Roldão 2026-06-15, máquina D-ORC-3 proíbe enviado→cancelado;
      ambos revogam link; aprovado+ preserva). Escuta `cliente.dados_anonimizados` (canônico). Ref: ADV-ORC-06;
      D-ORC-4. GATEs: **GATE-ANON-EVENTO-RECONCILIAR** (`clientes` ainda não publica anonimização — consumer
      dormente; `ordens_servico` escuta `cliente.anonimizado` divergente, alinhar quando `clientes` publicar) ·
      **GATE-ORC-ANON-BULK** (loop N×`atualizar_estado` 2-query — `transicionar_estado_bulk` pós-instrumentação;
      BAIXO, worker batch + cardinalidade baixa + dormente).
- [x] **T-ORC-037** ✅ DONE (ondas 2a/2b/2c-2) REST `OrcamentoViewSet` (criar/adicionar-item/enviar/aprovar/
      recusar/cancelar/retrieve/list; ACTION_MAP `orcamento.*`; idempotência helper reusável; margem só
      `ver_margem`). Ref: D-ORC-12; spec §7.
- [x] **T-ORC-038** ✅ DONE 2026-06-15 (Onda 2e) REST `OrcamentoPublicoView` — GET `{token}` (allowlist ADV-ORC-09;
      devolve ressalvas + `requer_confirmacao_ressalvas`) + POST `{token}/aprovar/` (token resolve tenant SEM RLS
      via SECURITY DEFINER `resolver_orc_publico_token` migration 0009 D-ORC-19; rate-limit 30/min/IP; Aprovacao
      WORM aceite rico LGPD HMAC; exige `ressalvas_confirmadas` se `com_ressalva`→422; reprova A→422+análise WORM
      sem Aprovacao; link revogado one-shot ao aprovar). Camada A: 7 auditores PASS zero MÉDIO+. **7 testes E2E**.
      GATEs: **GATE-ORC-RATELIMIT-PUBLICO** (alerta `aprovacao-suspeita`+lockout, pré-prod) · **GATE-LGPD-RETENCAO-
      APROVACAO** (linha `orcamento_aprovacao` na matriz de retenção — congelado até GATE-LGPD-RAT-CONSOLIDACAO) ·
      **GATE-ORC-PUB-PERF** (versao/itens lidos 2× no POST) · **GATE-ORC-PUB-FORENSE** (correlation_id na Aprovacao
      WORM) · GATE-ORC-CONVERTIDO-OSID. Ref: D-ORC-7/19; TL-ORC-07; ADV-ORC-04/08a/09; INV-ORC-APROVACAO-WORM.
- [x] **T-ORC-039** ✅ DONE 2026-06-15 (fecha módulo 100%; 15 testes verdes; hook `orc-template-selo-rbc-check` + INV-ORC-SELO-RBC; auditores seg/qual/llm/idemp PASS, produto MÉDIO CHANGELOG consertado) REST `TemplateViewSet` — CRUD + gate selo RBC por perfil (hook). Ref: D-ORC-13; AC-ORC-005.
- [ ] **T-ORC-040** Testes (`tests/test_orcamentos_fatia2.py` + `tests/test_orcamentos_api.py`): fluxo criar→
      enviar→aprovar→envelope; público 1-clique; anti-vazamento allowlist; idempotência replay; `assertNumQueries`
      (TL-ORC-09). Ref: AC-ORC-001..009.

## Fatia 3 — INVs + testes contrato/regressão + perfil-aware

- [x] **T-ORC-050** ✅ DONE 2026-06-15 (Onda 2f) REGRAS-INEGOCIAVEIS.md — cravar INV-ORC-PRECO-001 · CL71-001 · CONVERTIDO-TERMINAL ·
      APROVACAO-WORM · LINK-TOKEN · APROVADO-ENVELOPE · ANALISE-WORM · EQUIP-ITEM · MARGEM-OFF (mover
      INV-ORC-EXP-001 de invariantes-futuras). INV-checker OK. Ref: spec §5.
- [x] **T-ORC-051** ✅ DONE 2026-06-15 (Onda 2f; runner 637 ok 0 falhas) Hooks proporcionais: envelope-contrato (payload exato), margem-off (snapshot sem margem),
      analise-perfil (A fail-closed). `bash .claude/hooks/_test-runner.sh` verde.
- [x] **T-ORC-052** ✅ DONE 2026-06-15 (Onda 2f; 3 testes verdes) **Teste de contrato E2E** (`tests/regressao/test_inv_orc_envelope.py`): monta
      `orcamento.aprovado` real → `handle_orcamento_aprovado` → OS com N atividades (equip. certo) +
      `ItemComercialOS` (comerciais, **`tipo=OUTRO`+descricao derivada — MÉDIO-2**) + replay → 1 OS (confirmar
      dedup via `consumer_idempotencia`). **+ UNHAPPY: OS avulsa publica `os.aberta` sem `orcamento_id` →
      `handle_os_aberta` no-op (ALTO-1).** Ref: INV-ORC-APROVADO-ENVELOPE; R3.
- [x] **T-ORC-053** ✅ DONE 2026-06-15 (Onda 2f; 4 testes verdes) Testes UNHAPPY por perfil (`tests/regressao/test_inv_orc_cl71.py`): A reprova→422+WORM;
      B unknown→aprova+ressalva; D off; perfil indeterminado→fail-closed. Ref: INV-ORC-CL71-001; R1.
- [x] **T-ORC-054** ✅ DONE 2026-06-15 (Onda 2f; 3 testes verdes) Testes anti-vazamento (`test_inv_orc_margem_off` + público allowlist): snapshot sem margem;
      serializer público nunca devolve margem/comissão/custo/observacoes. Ref: INV-ORC-MARGEM-OFF; ADV-ORC-09; R2/R4.

## P8/P9 — fechamento

- [x] **T-ORC-060** ✅ DONE 2026-06-15 (P8; ADR-0083 + emenda PRD + matriz-reconciliacao + STATUS-GERADO + frontmatters stable) P8: ADR reconciliação `PrecoResolvido`×`Preco` (D-ORC-1; emenda PRD/modelo) +
      matriz-reconciliacao (AC↔código↔teste, INV↔teste, ata P9) + STATUS-GERADO + GATEs rastreados
      (PDF/TELA-PUBLICA/PADRAO/SAGA-DLQ/ORIGEM-ITEM/KMS-APROVADOR/US010/LGPD-RAT + **EXPIRY-JOB** [sweep
      manual→procrastinate por tenant] + **TRILHA-CANCELAMENTO** [cancelar não emite evento/auditoria — BAIXO,
      aceitável Wave A; avaliar trilha quando F-C entrar] + **GATE-ORC-PERF-APROVAR** [Onda 2c-2: 2 queries/item
      nas portas CMC/procedimento + itens carregados 2× (view+use case) — BAIXO aceitável Wave A; batch por
      grandeza + passar itens da view ao use case pós-instrumentação] + **GATE-OBS-ORC-METRICA-APROVACAO**
      [Onda 2c-2: counter `orcamento_analise_critica_total{perfil,veredito}` em `_publicar_eventos_analise` —
      BAIXO até F-C]) + frontmatters draft→stable.
      `status-projeto.sh --check`. Ref: plan §6.
- [x] **T-ORC-061** ✅ DONE 2026-06-15 (P9; 8 auditores roteados → 1 MÉDIO QUAL [INV-ORC-PRECO-001 sem teste] consertado causa-raiz + 2ª passada PASS; 8/8 PASS zero C/A/M — INV-RITUAL-001 OK) P9 auditores roteados (INV-RITUAL-003): essenciais + **performance** (N+1) +
      **observabilidade** (WORM/outbox/correlation_id) + **conformidade-lgpd OBRIGATÓRIO** (PII aprovador +
      ReferenciaPIIAnonimizavel + endpoint público) ; supplychain só se dep nova. Verificação adversarial de
      MÉDIO+ (R6); 2ª passada escopada (R5). Conserto causa-raiz → zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md.
