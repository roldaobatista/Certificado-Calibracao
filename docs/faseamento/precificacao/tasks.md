---
owner: agente-ia
revisado-em: 2026-06-12
proximo-review: 2026-09-12
status: stable
proximo-passo: ready-for-implement (revisado pelo orquestrador 2026-06-12; stable em lote R22)
diataxis: reference
audiencia: [agente, auditor]
frente: precificacao
tipo: tasks
relacionados:
  - docs/faseamento/precificacao/plan.md
  - docs/faseamento/precificacao/spec.md
---

# Tasks — frente `precificacao` (núcleo Wave A PARCIAL, stub custo)

> T-PRC-NNN. Fatias do `plan.md`. Cada fatia fecha com verificação real
> (regra "não declarar pronto sem rodar") antes da próxima. Refs: US-PRC-*
> (PRD), AC-PRC-*, INV-PRC-* (spec §5), D-PRC-* (spec §3).

## Fatia 1a — domínio puro (`src/domain/precificacao/`)

- [ ] **T-PRC-010** `enums.py` — `ModoFormacaoPreco` (PRECO_FIXO/MARGEM_ALVO/COST_PLUS),
      `OrigemCusto` (CUSTO_MANUAL/PROVIDER_REAL/INDISPONIVEL), `Semaforo`
      (VERDE/AMARELO/VERMELHO/INDISPONIVEL), `Alcada` (LIVRE/GERENTE/DONO),
      `ContextoTipo` (ORCAMENTO/OS/AVULSO), `EstadoPedido` (SOLICITADO/APROVADO/NEGADO),
      `ModoMontagem` (COMPONENTES_CHECKLIST/FECHADO_COM_AVISO). Ref: D-PRC-2/3/4/5; US-PRC-001/004.
- [ ] **T-PRC-011** `value_objects.py` — VO `Percentual` (Decimal 0..100, escala 2,
      `ROUND_HALF_EVEN`; conversão→fração documentada na docstring — TL-PRC-18) +
      `CalculoPrecoResultado` frozen AUTOSSUFICIENTE (itens[preco_base PrecoResolvido
      embutido, preco_final Decimal ≥ 0, desconto_pct, semaforo, margem_estimada?,
      custo_estimado?, preco_minimo?, origem_custo, custo_declarado_em?,
      sem_regra_formacao, cortesia], componentes_faltantes, avisos, alcada_exigida,
      motor_versao, faixas_versao, imposto_ref, parametros_versao, eco_entradas).
      `preco_final` é Decimal ≥ 0 PRÓPRIO (NUNCA reusa VO `Preco>0` da PPS — D-PRC-13).
      Ref: D-PRC-9/13; TL-PRC-01; AC-PRC-002-3; INV-026.
- [ ] **T-PRC-012** `entities.py` — `RegraFormacaoPreco` (modo, preco_fixo?,
      custo_manual_declarado?, custo_referencia_em?, margem_alvo_pct?, margem_piso_pct?,
      vigência ADR-0030, versão densa), `PerfilComposicaoPreco` (componentes_esperados,
      aviso_texto?, deletado_em mutável), `FaixaAprovacaoDesconto` (faixas contíguas
      [pct_de, pct_ate, alcada] + versao/hash do conjunto), `PedidoAprovacaoDesconto`
      (contexto_tipo, contexto_id?, snapshot probatório, pct_solicitado, cortesia:bool,
      alcada_exigida, fingerprint_calculo, estado, solicitante_id, decisor_id,
      justificativa_hash), `VinculoTabelaPrecoCliente` (tabela_id, cliente_id, vigência),
      `ParametrosPrecificacaoTenant` (custo_km, taxa_parcelamento_mensal,
      pct_comissao_prevista, margem_alvo_default, margem_piso_default; versionado).
      Frozen dataclasses. Ref: spec §4; D-PRC-3/7/12/14.
- [ ] **T-PRC-013** `portas.py` — `CustoProvider` (Protocol) + `StubCustoProvider`
      (retorna `CustoIndisponivel` EXPLÍCITO, nunca 0 — INV-PRC-CUSTO-EXPLICITO; molde
      `CoberturaEscopoPort` da calibração). Ref: D-PRC-5; US-PRC-001.
- [ ] **T-PRC-014** `transicoes.py` — `calcular_precos` puro POR CESTA (D-PRC-11): preço
      novo + semáforo + alçada + mínimo/sugerido (fórmulas glossário; denominador ≤ 0 →
      `ParametrosInviaveis`) + `componentes_faltantes` (avalia cesta) + `sem_regra_formacao`/
      semáforo INDISPONIVEL quando não há regra (TL-PRC-05) ; `validar_vigencia_nao_retroativa`
      regra; `validar_faixas_contiguas` (conjunto 0..100 sem buraco/sobreposição — TL-PRC-16);
      `fingerprint_calculo` (hash canônico ADR-0029 de entradas+refs+pct — reusar helper,
      não reimplementar — D-PRC-14); `validar_decisor_independente` (decisor != solicitante —
      INV-PRC-APROVACAO-INDEPENDENTE); `alcada_para_pct` (faixa→alçada). Ref: US-PRC-002/003/004/006.
- [ ] **T-PRC-015** `erros.py` (`CustoRealIndisponivel`, `PrecoMinimoViolado`,
      `ParametrosInviaveis`, `FaixasDescontoInvalidas`, `RegraVigenteAusente`,
      `CustoIndisponivel`, `FingerprintDivergente`, `AlcadaInsuficiente`,
      `DecisorNaoIndependente`) + `repository.py` (Protocols: RegraRepository,
      FaixaRepository, PedidoRepository, VinculoTabelaRepository, ParametrosRepository) —
      tipos reais, zero `object`/`Any` de escape (lição M1). Ref: spec §4 Erros; TL-PRC-05.
- [ ] **T-PRC-016** Testes puros (`tests/test_precificacao_dominio.py`): determinismo
      bit-a-bit cross-versão motor (AC-PRC-002-3); mínimo/sugerido pela fórmula com custo
      manual (AC-PRC-002-1/2); cesta sem componente esperado → `componentes_faltantes`
      (D-PRC-2); cortesia 100% → `preco_final=0` sem estourar (D-PRC-13); faixas com buraco
      → `FaixasDescontoInvalidas` (INV-PRC-FAIXAS-CONTIGUAS); mínimo violado calculável →
      `PrecoMinimoViolado` (INV-PRC-MINIMO-BLOQUEIO); stub → `CustoIndisponivel`
      (INV-PRC-CUSTO-EXPLICITO); fingerprint estável/divergente; decisor==solicitante →
      raise; sem regra → `sem_regra_formacao` + INDISPONIVEL (TL-PRC-05). ruff/mypy limpos.

## Fatia 1b — schema PG (`src/infrastructure/precificacao/`)

- [ ] **T-PRC-020** `models.py` (7 tabelas colunas tipadas) + `apps.py` + INSTALLED_APPS +
      `urls.py` raiz (molde fiscal/PPS). Ref: D-PRC-1; spec §4.
- [ ] **T-PRC-021** Migrations 0001 CreateModel + UNIQUEs (`(tenant,item,versao_n)` regra;
      vínculo UNIQUE parcial vigente por `(tenant,cliente)` — D-PRC-12; parâmetros singleton
      por tenant) + CHECK `preco_final ≥ 0` onde resultante persistir refs; **estado one-shot
      no pedido**. Ref: INV-PRC-REGRA-IMUTAVEL; INV-PRC-APROVACAO-ONE-SHOT; INV-PRC-APROVACAO-INDEPENDENTE (CHECK decisor != solicitante).
- [ ] **T-PRC-022** Migration 0002 RLS v2 FORCE nas 7 tabelas + 4 policies cada (lição B1
      cross-tenant). Ref: INV-TENANT-001/003.
- [ ] **T-PRC-023** Migration 0003 triggers WORM molde Imposto na `regra_formacao_preco`
      (campos probatórios congelados + `vigencia_fim` one-shot + `revogado_em`+motivo one-shot
      + block DELETE) + trigger one-shot de estado em `pedido_aprovacao_desconto`
      (SOLICITADO→APROVADO|NEGADO, sem volta) + trigger anti-mutação dos campos probatórios
      do pedido pós-decisão. Ref: D-PRC-7; INV-PRC-REGRA-IMUTAVEL; INV-PRC-APROVACAO-ONE-SHOT.
- [ ] **T-PRC-024** Migration 0004 exclusion btree_gist `(tenant, item)` `WHERE revogado_em
      IS NULL` na regra (não-sobreposição de vigência — molde PPS 0004). Ref: INV-PRC-REGRA-SEM-SOBREPOSICAO.
- [ ] **T-PRC-025** Migration 0005 grants `app_user` + 0006 seed authz `precificacao.*`
      (`configurar`, `calcular`, `ver_margem`, `aprovar_desconto`) — papel aprovador recebe
      `ver_margem` no seed (coerência D-PRC-4). Ref: spec §7.
- [ ] **T-PRC-026** `mappers.py` + `repositories.py` Django (advisory lock namespace novo —
      `(tenant, item)` na publicação de regra; densidade `versao_n=max+1` sob lock; replace-all
      faixas sob lock por tenant — TL-PRC-16) + injeção `StubCustoProvider` na view. Ref: D-PRC-3/5/7.
- [ ] **T-PRC-027** Drill `validar_precificacao` (estrutura: 7 tabelas/colunas/RLS/triggers/
      exclusion/grants/seed authz) + conftest `_SEED_MIGRATIONS` += seed authz. Ref: plan Fatia 1b.
- [ ] **T-PRC-028** Testes PG-real (`tests/test_precificacao_schema_fatia1b.py`): RLS UNHAPPY
      cross-tenant ×7; UPDATE direto em regra publicada → trigger raise; one-shot pedido
      (2ª decisão → raise); CHECK decisor != solicitante; exclusion overlap raise +
      revogada+substituta mesma janela OK; seed authz presente. Verificar: migrate +
      makemigrations --check + drill PASS.

## Fatia 2 — use cases + porta + REST (`src/application/` + `src/infrastructure/.../views.py`)

- [ ] **T-PRC-030** `application/.../regra.py` — `publicar_regra` (consulta `CustoProvider`;
      COST_PLUS sob stub → 422 `CustoRealIndisponivel` — D-PRC-6/INV-PRC-COSTPLUS-STUB; anti-
      retroativa de vigência + encerra anterior MESMA transação) + `revogar_regra` (revoga+recria
      é o caminho de correção — D-PRC-7). Ref: US-PRC-001; AC-PRC-001-3.
- [ ] **T-PRC-031** `application/.../calculo.py` — `calcular_precos` (porta de aplicação POR
      CESTA; stateless; memoização POR REQUEST de Imposto/Parâmetros/Faixas — TL-PRC-14;
      sem cache cross-request) consumindo `preco_para_os(..., tabela_id=)` com **fallback POR
      ITEM na tabela padrão** (D-PRC-12) + simulação fiscal `Imposto` vigente (D-PRC-10,
      estimada) + deslocamento (R$/km×km) + parcelamento + comissão prevista. Ref: US-PRC-002/003/005/006; AC-PRC-003-1.
- [ ] **T-PRC-032** `application/.../aprovacao.py` — `solicitar_aprovacao` (gera/grava
      `fingerprint_calculo` + contexto tipado — D-PRC-14; alçada DONO sempre p/ cortesia 100% —
      D-PRC-13) + `decidir_aprovacao` (one-shot; `decisor != solicitante` —
      INV-PRC-APROVACAO-INDEPENDENTE; predicate `alcada_cobre`; consumo recusa se fingerprint
      do cálculo vigente divergir — D-PRC-14; grava `justificativa_hash` no WORM + texto cru na
      tabela-par `JustificativaDecisaoDesconto` — D-PRC-15). Ref: US-PRC-003/004; AC-PRC-004-1/3/4.
- [ ] **T-PRC-033** `application/.../configuracao.py` — `configurar_faixas` (replace-all
      atômico valida CONJUNTO 0..100 — TL-PRC-16/INV-PRC-FAIXAS-CONTIGUAS) +
      `configurar_perfil_composicao` + `configurar_parametros` + etapa de seed faixas default
      0-10 livre/10-20 gerente/20+ dono no `provisionar_tenant` (ADR-0015) + RunPython p/ tenants
      existentes (D-PRC-3/TL-PRC-15). Ref: US-PRC-004; AC-PRC-004-1.
- [ ] **T-PRC-034** `infrastructure/.../serializers.py` — choke-point ÚNICO
      `filtrar_visao_margem(payload, pode_ver_margem)` aplicado em TODOS os serializers da frente
      (incl. serializer de pedido de aprovação — ADV-PRC-06): `semaforo`/`preco_minimo` sempre;
      `margem_estimada`/`custo_estimado` só com `precificacao.ver_margem`. Ref: D-PRC-4; INV-PRC-MARGEM-RBAC.
- [ ] **T-PRC-035** `infrastructure/.../views.py` — `RegraFormacaoPrecoViewSet` (publicar/
      revogar/retrieve/`vigente?item_id&em=` leitura gated `configurar`|`ver_margem`) +
      `CalculoPrecoView` (POST `calcular`, SEM Idempotency-Key — leitura computada) +
      `AprovacaoDescontoViewSet` (solicitar/decidir one-shot/pendentes; predicate `alcada_cobre`
      vinculado à action) + `ConfiguracaoPrecificacaoViewSet` (faixas/perfil/parametros gated
      `configurar`|`ver_margem`, NUNCA só `calcular`). ACTION_MAP `precificacao.*` + Idempotency-Key
      em solicitar/decidir/publicar/configurar (fingerprint = payload+alvo, lição B6) +
      `_falha` com log SEM custo/margem (INV-PRC-SEGREDO-LOG). Ref: spec §7; TL-PRC-11.
- [ ] **T-PRC-036** Registro do predicate ABAC `alcada_cobre` via `register_predicate` (molde
      `src/infrastructure/authz/predicates.py`; `actions={"precificacao.aprovar_desconto"}`;
      resource={alcada_exigida, papel}; deny se alçada do papel não cobre a faixa). Ref: TL-PRC-11; D-PRC-3.
- [ ] **T-PRC-037** Eventos `Precificacao.*` em `ACOES_PRECIFICACAO` (acoes_canonicas.py;
      cadeia-só `outbox=False`) — payload hashificado POR EVENTO (spec §6 / ADV-PRC-03): `*_id_hash`
      de pessoa + `*_hash` de justificativa/motivo/aviso_texto; **valores de Parametros/Faixas
      NUNCA em claro** (diff de NOMES — segredo comercial). Reusar helper de hash canônico do
      M5/M9/PPS. Ref: D-PRC-15; INV-PRC-JUSTIFICATIVA-HASH; INV-PRC-SEGREDO-LOG.
- [ ] **T-PRC-038** Testes: puros com Fakes (publicar COST_PLUS sob stub; fingerprint
      divergente; decisor==solicitante; replace-all faixas) + E2E PG-real: publicar COST_PLUS
      sob stub → 422 (INV-PRC-COSTPLUS-STUB); vazamento margem por endpoint não-calculadora →
      ausente sem `ver_margem` (INV-PRC-MARGEM-RBAC, UNHAPPY por endpoint); gerente decide alçada
      DONO → predicate nega (alcada_cobre); cesta multi-item; fallback-por-item na tabela padrão;
      `assertNumQueries` no `calcular_precos` (sem N+1 — TL-PRC-14); cortesia 100% (D-PRC-13).
      Ref: reviews-consolidado §1 "Testes exigidos".

## Fatia 3 (P7) — INVs + hooks + testes nomeados

- [ ] **T-PRC-050** Família `INV-PRC-*` (12) em REGRAS-INEGOCIAVEIS.md (nova seção
      `## INV-PRC-*`, molde da seção INV-PPS): COSTPLUS-STUB, REGRA-IMUTAVEL,
      REGRA-SEM-SOBREPOSICAO, APROVACAO-ONE-SHOT, APROVACAO-INDEPENDENTE, MINIMO-BLOQUEIO,
      CUSTO-EXPLICITO, MARGEM-RBAC, SEGREDO-LOG, JUSTIFICATIVA-HASH, FAIXAS-CONTIGUAS +
      INV-026 herdada (motor não persiste) — colunas enforcement/origem/perfil/efeito.
      Ref: spec §5.
- [ ] **T-PRC-051** `TestINV_PRC_*` nomeadas (TST-004; PG-real onde enforcement é banco:
      REGRA-IMUTAVEL/SEM-SOBREPOSICAO/APROVACAO-ONE-SHOT/INDEPENDENTE; puro onde é domínio:
      COSTPLUS-STUB/CUSTO-EXPLICITO/FAIXAS-CONTIGUAS/MINIMO-BLOQUEIO; E2E onde é serializer/log:
      MARGEM-RBAC/SEGREDO-LOG/JUSTIFICATIVA-HASH). Ref: T-PRC-050.
- [ ] **T-PRC-052** Hooks novos registrados no `.claude/hooks/pre-commit-manifest.tsv`
      (ritual R5 — manifest pré-commit, NÃO write-time): `prc-costplus-stub-check`
      (`/precificacao/.*publicar_regra\.py$|/application/precificacao/.*\.py$`),
      `prc-margem-rbac-check` (`/precificacao/.*serializers\.py$`),
      `prc-evento-pii-hash-check` (`/precificacao/.*\.py$` — denylist adaptada do PEPH/PPS) +
      scripts em `.claude/hooks/` + casos no `_test-runner.sh` + `settings.json` se necessário +
      contagens via `scripts/status-projeto.sh --check` (NUNCA em prosa — denylist). Verificar:
      `bash .claude/hooks/_test-runner.sh` verde. Ref: spec §5; ADV-PRC-03/06.

## P8/P9 — fechamento

- [ ] **T-PRC-060** matriz-reconciliacao.md ENXUTA (ritual R20 — só §1 US/INV↔código,
      §2 INV↔teste, §8 ata do P9) + registro GATE-PRC-* no STATUS-GERADO + AGENTS §12 +
      GATE-PPS-WIREIN-OS atualizado (consome esta frente) + emenda
      `docs/dominios/comercial/modulos/precificacao/modelo-de-dominio.md` (`CalculoPreco` é
      transiente/snapshot do consumidor, não tabela desta frente — reconcilia com D-PRC-9).
      Frontmatters draft→stable em LOTE periódico (R22 — não passo formal aqui). Verificar:
      `status-projeto.sh --check`. Ref: plan P8.
- [ ] **T-PRC-061** P9 auditores roteados (INV-RITUAL-003): 6 essenciais (qualidade·segurança·
      llm·idempotência·conformidade-lgpd [eventos/justificativa/RAT]·produto) + performance
      (motor+porta+cesta) + observabilidade (views financeiras + segredo em log); supplychain SÓ
      se dep nova (núcleo não traz); drift-docs FORA (R7). Verificação adversarial de TODO MÉDIO+
      antes do mutirão (R6); 2ª passada escopada (R5). Conserto causa-raiz → re-passada → zero
      C/A/M (INV-RITUAL-001) → frente FECHADA + CURRENT.md. BAIXOs em lote pós-fechamento (R10).
