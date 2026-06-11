---
owner: agente-ia
revisado-em: 2026-06-11
status: stable
frente: produtos-pecas-servicos
tipo: tasks
ready-for-implement: true
relacionados:
  - docs/faseamento/produtos-pecas-servicos/plan.md
  - docs/faseamento/produtos-pecas-servicos/spec.md
---

# Tasks — frente `produtos-pecas-servicos` + TabelaPreco

> T-PPS-NNN. Fatias do `plan.md`. Cada fatia fecha com verificação real
> (regra "não declarar pronto sem rodar") antes da próxima.

## Fatia 1a — domínio puro (`src/domain/produtos_pecas_servicos/`)

- [ ] **T-PPS-010** `enums.py` — TipoItem (PRODUTO/PECA/SERVICO/KIT), StatusItem
      (ATIVO/INATIVO), OrigemPreco (MANUAL/SOMA_PARTES), StatusLinhaImportacao
      (VALIDADA/REJEITADA/ACEITA). Nota TL-PPS-14 no docstring (produto×peça = rótulos).
- [ ] **T-PPS-011** `value_objects.py` — VO `Preco` (Decimal escala 2 ROUND_HALF_EVEN,
      `> 0` — TL-PPS-15/16; molde `Aliquota`). Reusa `JanelaVigencia` de shared.
- [ ] **T-PPS-012** `entities.py` — ItemCatalogo (controla_estoque no ITEM — TL-PPS-12),
      ItemCatalogoVersao, KitComposicao (sem UM própria — TL-PPS-11), TabelaPreco
      (eh_padrao), LinhaTabelaPreco, PrecoResolvido (contrato ADR-0081 completo:
      refs + origem_preco + composicao_resolvida). Frozen dataclasses.
- [ ] **T-PPS-013** `transicoes.py` — `validar_vigencia_nao_retroativa` (TL-PPS-08; exceção
      1ª versão), `validar_kit_sem_ciclo` (filho ≠ kit), `resolver_preco` puro (linha
      vigente não-revogada; kit exige linha própria), `proxima_versao_n` (max+1).
- [ ] **T-PPS-014** `erros.py` + `repository.py` (Protocols: ItemCatalogoRepository,
      TabelaPrecoRepository) — tipos reais, zero `object` (lição M1 da frente #1).
- [ ] **T-PPS-015** Testes puros (`tests/test_pps_dominio.py`): VO Preco (escala/
      arredondamento/`<=0` raise), anti-retroativa, kit sem ciclo, resolver_preco
      (vigente/ausente/revogada/kit), versão densa. ruff/mypy limpos.

## Fatia 1b — schema PG (`src/infrastructure/produtos_pecas_servicos/`)

- [ ] **T-PPS-020** `models.py` (5 tabelas colunas tipadas) + `apps.py` + INSTALLED_APPS +
      `urls.py` raiz (molde fiscal).
- [ ] **T-PPS-021** Migrations: 0001 CreateModel + UNIQUEs (codigo_interno por tenant
      INV-PPS-CODIGO-UNICO; (tenant,item,versao_n); eh_padrao parcial) + CHECK `preco > 0`
      ×2; 0002 RLS v2 FORCE nas 5; 0003 triggers WORM molde Imposto ×2 (versão + linha:
      campos probatórios + one-shot vigencia_fim/revogado_em + block DELETE); 0004
      exclusions btree_gist ×2 `WHERE revogado_em IS NULL`; 0005 grants app_user;
      0006 seed authz `catalogo.*` (ver/editar/gerenciar_tabela/importar).
- [ ] **T-PPS-022** `mappers.py` + `repositories.py` (advisory lock 880_403 por item em
      criar/corrigir versão; por (tabela,item) em linha; densidade max+1 sob lock).
- [ ] **T-PPS-023** Drill `validar_produtos_pecas_servicos` (estrutura: tabelas/colunas/
      RLS/triggers/exclusions/grants/seed) + conftest `_SEED_MIGRATIONS` += 0006.
- [ ] **T-PPS-024** Testes PG-real (`tests/test_pps_schema_fatia1b.py`): RLS UNHAPPY
      cross-tenant nas 5 tabelas (lição B1); unhappy UPDATE direto em versão E linha
      (trigger raise); exclusion overlap raise + revogada+substituta mesma janela OK;
      CHECK preco<=0 raise; one-shot. Verificar: migrate + makemigrations --check + drill.

## Fatia 2 — use cases + porta + REST

- [ ] **T-PPS-030** `application/.../item.py` — cadastrar_item (código dup → CodigoDuplicado
      409; cria v1 vigente hoje OU vigência passada se importação), nova_versao_preco
      (anti-retroativa + encerra anterior MESMA transação), corrigir_versao (revoga+recria
      atômico — D-PPS-8), inativar_item, montar_kit.
- [ ] **T-PPS-031** `application/.../tabela.py` — criar_tabela (2ª eh_padrao → 422),
      criar_linha (default sugerido do preco_padrao; kit linha própria), corrigir_linha
      (revoga+recria), encerrar_linha.
- [ ] **T-PPS-032** `query_service.py` — `preco_para_os` (resolução server-side; contrato
      PrecoResolvido completo; docstring crava data_referencia = data da CONTRATAÇÃO —
      ADV-PPS-05) + teste de contrato dedicado.
- [ ] **T-PPS-033** `serializers.py` + ViewSets (ItemCatalogoViewSet: cadastrar/
      nova-versao/corrigir-versao/inativar/montar-kit/retrieve; TabelaPrecoViewSet:
      criar/criar-linha/corrigir-linha/encerrar-linha/preco-vigente) — ACTION_MAP +
      Idempotency-Key (fingerprint = payload completo + alvo — lição B6) + resumo
      persistido sem texto livre (lição B9) + `_falha` com log (lição B13).
- [ ] **T-PPS-034** Eventos `Catalogo.*` em `ACOES_CATALOGO` (acoes_canonicas.py) —
      payload `criado_por_id_hash` + descricao/motivo hashificados ADR-0029 (reusar
      helper M5/M9) — ADV-PPS-01/02.
- [ ] **T-PPS-035** Testes: puros com Fakes (ordem revoga→recria; anti-retroativa) +
      E2E PG-real (409/422/404; porta vigente/ausente/revogada/kit-sem-linha; **regressão
      INV-026 DURA** [consulta histórica não muda após nova versão — TL-PPS-08];
      concorrência 2 criar-versão simultâneos; reconciliação centavos TL-PPS-15).

## Fatia 3 — importação CSV (staging)

- [ ] **T-PPS-040** `extracao_csv.py` parser puro (dialeto Excel BR `;` + vírgula decimal +
      BOM; layout fixo; colunas extras DESCARTADAS — ADV-PPS-06) + fixture replay
      (`tests/replay_*/pps_importacao.json` se aplicável — determinismo).
- [ ] **T-PPS-041** Models/migrations staging (`importacao_catalogo` + linhas; RLS; TTL
      90d) + use cases importar (staging RASCUNHO — INV-ECMC-007 molde) / aceitar_linha
      (reusa cadastrar_item; one-shot) / rejeitar_linha.
- [ ] **T-PPS-042** REST importar/aceitar-linha + SHA-256 do arquivo no evento WORM +
      command TTL `limpar_importacoes_expiradas` (idempotente).
- [ ] **T-PPS-043** Testes: parser (BR/BOM/extras) + staging não-auto-persiste + aceite
      cria item v1 + TTL elimina rejeitadas/abandonadas + hook `csv-safety-import` cobre.

## Fatia 4 (P7) — INVs + hooks

- [ ] **T-PPS-050** Família `INV-PPS-*` em REGRAS-INEGOCIAVEIS.md (CODIGO-UNICO,
      VERSAO-IMUTAVEL, PRECO-NAO-RETROATIVO, LINHA-IMUTAVEL, LINHA-SEM-SOBREPOSICAO,
      KIT-SEM-CICLO, PRECO-POSITIVO, IMPORTACAO-STAGING) + `TestINV_PPS_*` nomeadas
      (TST-004; PG-real onde o enforcement é banco).
- [ ] **T-PPS-051** Hooks camada A (validar necessidade contra catálogo existente —
      candidatos: `pps-porta-fail-closed-check` [porta não regride a fallback lista];
      `pps-evento-pii-hash-check` [payload Catalogo.* sem texto livre cru]) + casos
      `_test-runner` + settings.json + contagens sincronizadas (status-projeto --check).

## P8/P9 — fechamento

- [ ] **T-PPS-060** matriz-reconciliacao.md (molde M7 8 seções) + ADR-0081 promovida
      aceito (§11 AGENTS) + frontmatters stable + GATEs registrados (WIREIN-OS bloqueante
      pré-tenant-externo · XLSX · OUTBOX-ESTOQUE).
- [ ] **T-PPS-061** P9 auditores roteados (INV-RITUAL-003): seguranca · qualidade · llm ·
      produto · idempotencia · conformidade-lgpd · performance (+observabilidade — views
      novas; supplychain NÃO se CSV-only mantido). Conserto causa-raiz → re-passada →
      zero C/A/M (INV-RITUAL-001) → frente FECHADA + CURRENT.md.
