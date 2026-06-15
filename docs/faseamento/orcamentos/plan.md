---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
proximo-passo: Fatia 2 (Ondas 2a-2f) + P8/P9 FECHADAS; pendente T-ORC-039 (Templates)
diataxis: explanation
audiencia: [agente, auditor]
frente: orcamentos
tipo: plan
relacionados:
  - docs/faseamento/orcamentos/spec.md
  - docs/faseamento/orcamentos/reviews-consolidado.md
  - docs/faseamento/orcamentos/tasks.md
---

# Plan — frente `orcamentos` (P3, derivado da spec v2)

> Estratégia de implementação fatiada do módulo `orcamentos` (1ª ponta de receita, Wave A).
> Cada fatia fecha com verificação real (regra "não declarar pronto sem rodar") antes da próxima.
> Greenfield (módulo novo) — a ponta da OS (consumer `Orcamento.Aprovado` + `abrir_os_via_orcamento`)
> JÁ existe e foi preparada na frente `os-multi-equipamento` (ADR-0082, envelope por item).
> Refs: D-ORC-* / INV-ORC-* (spec §3/§5), seams reais (spec §11), correções P2 (reviews-consolidado).

## 0. Princípio de sequenciamento

Dependência interna: domínio puro → schema PG → use cases/REST → INVs/testes → fechamento.
Peças compartilhadas (numeração, idempotência, outbox, ReferenciaPIIAnonimizavel, rate-limit) **não se
constroem** — reusam moldes existentes (spec §11). Decisão técnica/metrológica vai a subagente, não ao Roldão.

## 1. Riscos e mitigações (cravados antes de codar)

| # | Risco | Severidade | Mitigação |
|---|-------|-----------|-----------|
| R1 | Análise crítica cl. 7.1 perfil-aware errada (A fail-closed vs B ressalva) | ALTO | `consultor-rbc` revisa o plan; testes UNHAPPY por perfil (A reprova→422, B aprova+ressalva, perfil indeterminado→fail-closed); `tenant_perfil_e` server-side, nunca payload |
| R2 | Endpoint público vaza cross-tenant ou PII/margem | ALTO | token resolve tenant SEM RLS (D-ORC-19); serializer público allowlist (ADV-ORC-09) + teste anti-vazamento; rate-limit; pentest `[SEC-PRE-PROD]` |
| R3 | Envelope `Orcamento.Aprovado` diverge do que a OS consome | ALTO | INV-ORC-APROVADO-ENVELOPE = teste de contrato que monta o envelope e chama `handle_orcamento_aprovado` real (E2E orçamento→OS), incl. item calibração→atividade + item comercial→ItemComercialOS |
| R4 | Snapshot do item persiste margem/custo (vaza no PDF futuro) | ALTO | INV-ORC-MARGEM-OFF: persistir SÓ `PrecoResolvido`+`preco_final`+`desconto_pct`+`semaforo`; teste que inspeciona o registro |
| R5 | Duplicação de OS no replay / saga não fecha | MÉDIO | idempotência outbox `causation_id=orcamento_id`; consumer `OS.Aberta` idempotente fecha `convertido`; teste replay → 1 OS |
| R6 | Numeração com buracos (cliente vê salto) | MÉDIO | regime gap-less `SerieDocumento` (D-ORC-18); advisory lock; `confirmar_numero` no atomic da criação |
| R7 | N+1 em listagem/visão (itens + preços) | MÉDIO | resolver batch (tabela padrão 1x — `preco_para_os(tabela_padrao=...)`); `assertNumQueries` (TL-ORC-09) |
| R8 | PII aprovador sem cifragem KMS (ADV-ORC-05b) | MÉDIO | HMAC Wave A + `GATE-ORC-KMS-APROVADOR` (exibição diferida); advogado confirma no review |

## 2. Fatia 1a — domínio puro (`src/domain/comercial/orcamentos/`)

- `enums.py`: `EstadoOrcamento` (rascunho/enviado/aprovado/aprovado_pendente_os/convertido/recusado/expirado/
  cancelado), `TipoAtividadeAlvo` (calibracao/manutencao/instalacao/verificacao/vistoria — SEM `outro`; D-ORC-16),
  `VeredictoAnaliseCritica` (aprovada/reprovada/com_ressalva/desabilitada), `CanalAprovacao`, `OrigemPreco` (reuso pps).
- `value_objects.py`: reusar `Dinheiro`/`Desconto`/`CondicoesPagamento` (modelo PRD) + `JanelaVigencia` (ADR-0030,
  shared) + `PrecoResolvido` (importado de pps). `ReferenciaPIIAnonimizavel` de `domain/shared`.
- `entities.py`: `Orcamento` (raiz), `VersaoOrcamento`, `ItemOrcamento` (com `equipamento_id?` + carimbo preço
  sem margem), `LinkPublico`, `Aprovacao`, `AnaliseCriticaOrcamento`, `Template` (spec §4).
- `erros.py`: `ClienteBloqueado`(422), `TabelaPrecoExpirada`(422), `AnaliseCriticaReprovada`(422),
  `EstadoInvalido`/`TransicaoProibida`(409), `OrcamentoConvertido`(409), `TokenInvalidoOuExpirado`(404/410),
  `PerfilIndeterminado`(422).
- `transicoes.py`: máquina de estados D-ORC-3 (transições válidas + proibidas); `traduzir_tipo_atividade_alvo`
  (D-ORC-16, mapa fechado → `TipoAtividade` da OS); montagem do envelope `Orcamento.Aprovado` (função pura
  que recebe os snapshots e devolve o dict do payload — testável isoladamente, base do INV-ORC-APROVADO-ENVELOPE).
- `repository.py`: Protocols (`OrcamentoRepository`, `TemplateRepository`) — sem Django.
- **Verificação:** `tests/test_orcamentos_dominio.py` (máquina de estados happy/unhappy; tradução enum;
  bifurcação item calibração×comercial; montagem do envelope; preço sem margem). ruff/mypy limpos.

## 3. Fatia 1b — schema PG (`src/infrastructure/orcamentos/`)

- `apps.py` (label `orcamentos`; predicate authz no `ready()` se houver). `models.py`: 7 tabelas
  (`orcamento`, `versao_orcamento`, `item_orcamento`, `link_publico`, `aprovacao`, `analise_critica_orcamento`,
  `template_orcamento`) — todas `tenant_id` NOT NULL; ReferenciaPIIAnonimizavel no orçamento + aprovação.
- **Ações canônicas do bus (TL-ORC CRIT-1 — pré-requisito da Fatia 2):** criar bloco `ACOES_ORCAMENTOS` em
  `src/infrastructure/audit/acoes_canonicas.py` (`orcamento.enviado/aprovado/recusado/expirado/convertido/
  analise_critica_reprovada/analise_critica_com_ressalva` — **lowercase**, `outbox=True`) + incluir na union
  `ACOES_CANONICAS` + migration `0007_acoes_orcamentos_check` que emenda o `CHECK bus_outbox_acao_enum_semantico`.
  Sem isso, `publicar_evento(acao="orcamento.aprovado", outbox=True)` quebra no CHECK do PG (saga invisível).
- Migrations: `0001_initial` · `0002_rls_policies` (RLS v2 FORCE + 4 policies/tabela + grants `app_user`) ·
  `0003_triggers_worm` (anti-mutação em `aprovacao` + `analise_critica_orcamento` + `versao_orcamento`;
  `snapshot_hash` via canonicalização ADR-0029, molde `append_evento_calibracao` — TL-ORC MÉDIO-4) ·
  `0004_constraints` (partial unique `link_publico` 1-ativo WHERE revogado IS NULL; CHECK estado terminal;
  unique numero por tenant) · `0005_grants` (se separado) · `0006_seed_authz` (ações `orcamento.criar/editar/
  enviar/aprovar/recusar/cancelar/ver/gerir_template/ver_margem` × perfis — matriz molde 0013 OS) ·
  `0007_acoes_orcamentos_check` (CHECK do bus acima).
- `repositories.py` + `mappers.py`: adapters Django dos Protocols; numeração via `SerieDocumento`
  (`reservar_numero`/`confirmar_numero`); CRUD + WORM append.
- **Verificação (drill em banco COM dados):** `migrate` + `makemigrations --check`; RLS UNHAPPY cross-tenant
  por tabela; trigger WORM bloqueia UPDATE/DELETE em aprovacao/analise; numeração densa concorrente (gap-less);
  partial unique link. `tests/test_orcamentos_schema.py` (PG-real). `auditor-seguranca` passa.

## 4. Fatia 2 — use cases + consumers + REST

- **Use cases** (`src/application/comercial/orcamentos/`):
  - `criar_orcamento` (cliente ativo/não-bloqueado — D-ORC-4; numero gap-less; estado rascunho).
  - `adicionar_item` / `editar_item`: chama `calcular_precos` (cesta) → persiste SÓ `PrecoResolvido`+
    `preco_final`+`desconto_pct`+`semaforo` (INV-ORC-MARGEM-OFF); `equipamento_id` no item de calibração.
    **(TL-ORC ALTO-2)** a montagem das deps de `calcular_precos` (`resolver_preco_fn`, `aliquota_imposto_fn`,
    3 repos de precificacao) mora na **camada de infra (view de orcamentos)**, NÃO no use case; reusar
    `_construir_resolver_com_tabela_padrao(tenant_id, data_ref)` de `infrastructure/precificacao/views.py:164`
    (anti-N+1 da `tabela_padrao` — resolve `obter_padrao` 1x/request, não por item).
  - `enviar_orcamento`: cria `VersaoOrcamento` V1 (snapshot) + `LinkPublico` (token ≥128 bits) + publica
    `Orcamento.Enviado`.
  - `aprovar_orcamento` (interno + público): **análise crítica cl. 7.1 perfil-aware (D-ORC-5)** por item de
    calibração via portas CMC+procedimento (grandeza/faixa do equipamento) → grava `AnaliseCriticaOrcamento`
    WORM + `snapshot_hash` → transição `aprovado_pendente_os` → publica `Orcamento.Aprovado` (envelope por item)
    + `Orcamento.AnaliseCriticaReprovada`/`ComRessalva`. Idempotente.
  - `recusar_orcamento` / `cancelar_orcamento` (409 se convertido — INV-ORC-CONVERTIDO-TERMINAL).
  - `expirar_orcamentos` (job idempotente por orcamento_id — INV-ORC-EXP-001). **Timezone (TL-ORC MÉDIO-3):
    não há seam `timezone_by_tenant`; Wave A compara em UTC com `validade_ate` (`JanelaVigencia`) e registra
    GATE-ORC-TIMEZONE-TENANT (corrigir quando houver config de fuso por tenant).**
- **Consumers** (`src/infrastructure/orcamentos/consumers/`):
  - `handle_os_aberta`: lê `envelope["payload"]["orcamento_id"]` (o evento `os.aberta` carrega esse campo —
    verificado `abrir_os_via_orcamento.py:327`); **se ausente/None → no-op** (OS avulsa também publica
    `os.aberta` — TL-ORC ALTO-1); senão transiciona `aprovado_pendente_os→convertido` + publica
    `orcamento.convertido`. `@consumer_idempotente` (dedup por `event_id`) — replay não transiciona 2x.
  - `handle_cliente_anonimizado`: por estado (rascunho/enviado → cancela + revoga LinkPublico; aprovado+ →
    preserva — ADV-ORC-06).
- **REST** (`src/infrastructure/orcamentos/views.py` + `views_publico.py`): `OrcamentoViewSet` (criar/
  adicionar-item/enviar/aprovar/recusar/cancelar/retrieve/list; ACTION_MAP `orcamento.*`; idempotência via
  helper reusável; margem/comissão SÓ com `orcamento.ver_margem`), `OrcamentoPublicoView` (GET `{token}`
  allowlist — **devolve ressalvas quando houver, C3**; POST `{token}/aprovar` rate-limit + WORM; token resolve
  tenant — D-ORC-19; **exige `ressalvas_confirmadas` quando análise = `com_ressalva`, senão 422; grava
  `ressalvas_aceitas` na Aprovacao WORM — cl. 7.1.1-d C2**), `TemplateViewSet` (CRUD + gate selo RBC por
  perfil — D-ORC-13).
- **Verificação:** `tests/test_orcamentos_fatia2.py` + `tests/test_orcamentos_api.py` (APIClient: happy criar→
  enviar→aprovar→envelope; público aprovar 1-clique; anti-vazamento allowlist; idempotência; `assertNumQueries`).

## 5. Fatia 3 — INVs + testes regressão/contrato + análise crítica perfil-aware

- REGRAS-INEGOCIAVEIS.md: cravar INV-ORC-PRECO-001 · CL71-001 · CONVERTIDO-TERMINAL · APROVACAO-WORM ·
  LINK-TOKEN · APROVADO-ENVELOPE · ANALISE-WORM · EQUIP-ITEM · MARGEM-OFF (mover INV-ORC-EXP-001 de
  invariantes-futuras). Hooks proporcionais (envelope-contrato; margem-off; análise-perfil).
- **Teste de contrato E2E (R3):** monta `orcamento.aprovado` real e chama `handle_orcamento_aprovado` →
  verifica OS criada com atividades (1 por item calibração, equipamento certo) + `ItemComercialOS` (itens
  comerciais, **`tipo=OUTRO` + `descricao_publica` derivada — TL-ORC MÉDIO-2**) + replay → 1 OS (confirmar
  dedup via `consumer_idempotencia`). **+ UNHAPPY: OS avulsa publica `os.aberta` sem `orcamento_id` →
  `handle_os_aberta` no-op (TL-ORC ALTO-1).**
- **Testes UNHAPPY por perfil (R1):** A reprova→422+evento WORM; B unknown→aprova+ressalva; C warning;
  D off; perfil indeterminado→fail-closed.
- Anti-vazamento (R2/R4): serializer público + snapshot sem margem.

## 6. P8/P9 — fechamento

- **P8:** ADR de reconciliação `PrecoResolvido` vs VO `Preco` do PRD (D-ORC-1; emenda PRD/modelo) +
  matriz-reconciliacao (AC↔código↔teste; INV↔teste; ata P9) + STATUS-GERADO + frontmatters draft→stable +
  GATEs rastreados (PDF, TELA-PUBLICA, PADRAO, SAGA-DLQ, ORIGEM-ITEM, KMS-APROVADOR, US010, LGPD-RAT). denylist `--check`.
- **P9:** auditores roteados (INV-RITUAL-003): essenciais (qualidade·segurança·llm·idempotência·produto) +
  **performance** (N+1 listagem/preço — R7) + **observabilidade** (eventos WORM/outbox/correlation_id) +
  **conformidade-lgpd** OBRIGATÓRIO (PII aprovador + ReferenciaPIIAnonimizavel + endpoint público) +
  supplychain SÓ se dep nova. Verificação adversarial de todo MÉDIO+ (R6); 2ª passada escopada (R5);
  conserto causa-raiz → zero C/A/M (INV-RITUAL-001) → FECHADA + CURRENT.md.

## 7. Revisão do plan — CONCLUÍDA (2026-06-14)

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES** (CRIT-1 `ACOES_ORCAMENTOS`/lowercase; ALTO-1
  casamento `handle_os_aberta` por `payload.orcamento_id`+no-op OS avulsa; ALTO-2 reuso
  `_construir_resolver_com_tabela_padrao`; MÉDIO-1..4). **Todas incorporadas** na spec v2 (D-ORC-6/§6) + plan
  (Fatia 1b/2) + tasks.
- ✅ `consultor-rbc-iso17025` — **APROVA COM CORREÇÕES** (C1 `itens_avaliados` com procedimento_id/codigo/versão;
  C2/C3 confirmação de ressalva no endpoint público cl. 7.1.1-d; C4 texto verbatim ressalva padrão; C5/C6/C7
  campos WORM; C8 GATE-ORC-CMC-PREENCHIDO; C9 GATE-ORC-RT-MINIMO). **Incorporadas** em D-ORC-5/7/15 + §9.
  `rt_competencia` fora do orçamento = correto. **Limite:** parecer consultivo IA; dossiê CGCRE exige consultor
  humano credenciado pré-acreditação.
- 🔲 `advogado-saas-regulado`: D-ORC-17 (HMAC + GATE-ORC-KMS-APROVADOR) já segue o padrão do projeto (HMAC
  Wave A + GATE KMS) + consumer anonimização por estado (ADV-ORC-06 P2) — confirmar no P9 (auditor-conformidade-lgpd
  OBRIGATÓRIO já cobre PII aprovador + endpoint público).

## 8. Non-goals do plan

Não construir: PDF/telas (GATEs) · V2/V3+comparação+tracking (Wave B) · saga-manager DLQ · cobrança/gateway ·
cifragem KMS real (GATE) · `padrao_disponivel` real (GATE) · `origem_item_id` na OS (GATE). Não tocar OS/
precificacao/pps além de consumir suas portas já existentes.
