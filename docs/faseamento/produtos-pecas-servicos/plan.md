---
owner: agente-ia
revisado-em: 2026-06-11
status: stable
frente: produtos-pecas-servicos
tipo: plan
ready-for-tasks: true
relacionados:
  - docs/faseamento/produtos-pecas-servicos/spec.md
  - docs/faseamento/produtos-pecas-servicos/T-PPS-000-investigacao.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
---

# Plan — frente `produtos-pecas-servicos` + TabelaPreco (núcleo)

> Deriva da `spec.md` v2 (P2 incorporado — TL-PPS-01..16 + ADV-PPS-01..09). Decisões
> D-PPS-1..10 cravadas lá; este plan só materializa fatias, arquivos e riscos. Molde
> de execução = frente #1 `configuracoes-sistema` (mesma anatomia de fatias).

## Arquitetura (resumo operacional)

- **Path (D-PPS-1):** raiz achatada `src/{domain,application,infrastructure}/produtos_pecas_servicos/`.
  App label `produtos_pecas_servicos`; sem `_APP_MODULE_SUBPATH` no conftest.
- **Tabelas (5):** `item_catalogo`, `item_catalogo_versao`, `kit_composicao`,
  `tabela_preco`, `linha_tabela_preco` (+ staging `importacao_catalogo` +
  `importacao_catalogo_linha` na Fatia 3 = 7). Todas RLS v2 FORCE + 4 policies.
- **Imutabilidade (D-PPS-8):** `item_catalogo_versao` e `linha_tabela_preco` com molde
  Imposto COMPLETO (trigger Padrão B campos probatórios + `vigencia_fim` one-shot +
  `revogado_em`+motivo one-shot + block DELETE) + exclusion `btree_gist`
  `WHERE revogado_em IS NULL` (versão: por item; linha: por (tabela, item)).
- **VO `Preco`:** Decimal escala 2, `ROUND_HALF_EVEN`, `> 0` (CHECK espelhado no banco).
- **Concorrência:** advisory lock por item (criar/corrigir versão — namespace novo
  `880_403`) e por (tabela,item) nas linhas; densidade `versao_n = max+1` sob o lock.
- **Anti-retroatividade (INV-PPS-PRECO-NAO-RETROATIVO):** use case valida
  `inicio_nova ≥ max(agora, inicio_da_vigente)`; exceção única: 1ª versão de item novo
  (importação) pode ter vigência passada.
- **Porta `preco_para_os`:** módulo `query_service.py` (molde M6/M7) — função pura de
  resolução + adapter Django; contrato `PrecoResolvido` completo (ADR-0081 §4).
- **Eventos:** `Catalogo.{ItemCadastrado,ItemAtualizado,PrecoAlterado,ItemInativado,
  KitAlterado,TabelaCriada,LinhaPrecoCriada,LinhaPrecoCorrigida,ImportacaoConcluida}` —
  ACOES_CATALOGO em `acoes_canonicas.py`, cadeia-só (`outbox=False`), payload com
  `criado_por_id_hash` + `descricao/motivo` hashificados (ADV-PPS-01/02).
- **Importação (Fatia 3):** parser CSV puro (dialeto Excel BR: `;`, vírgula decimal,
  BOM; colunas fora do layout descartadas) + staging RASCUNHO + aceite por linha
  (reusa `cadastrar_item`) + TTL 90d (command idempotente, molde alertas M9).

## Fatias

| Fatia | Entrega | Verificação |
|---|---|---|
| **1a domínio puro** | enums (TipoItem, StatusItem, OrigemPreco, StatusLinhaImportacao) + VO `Preco` + entidades frozen (ItemCatalogo, ItemCatalogoVersao, KitComposicao, TabelaPreco, LinhaTabelaPreco, PrecoResolvido) + transições (validar anti-retroativa, kit sem ciclo, resolver_preco puro) + erros (CodigoDuplicadoError, PrecoTabelaAusente, PrecoInvalidoError, VersaoRetroativaError, KitComCicloError) + repository Protocols | testes puros; ruff/mypy limpos |
| **1b schema PG** | models colunas tipadas + migrations 0001..0006 (CreateModel+UNIQUEs+CHECK preco>0 / RLS v2 / triggers WORM molde Imposto ×2 / exclusions ×2 / grants / seed authz `catalogo.*`) + mappers + repositories Django (advisory 880_403) + drill `validar_produtos_pecas_servicos` + conftest seed | migrate OK; makemigrations --check; testes PG-real (RLS UNHAPPY 5 tabelas, triggers, exclusions, unhappy UPDATE direto); drill PASS |
| **2 use cases + porta + REST** | cadastrar_item / nova_versao_preco (anti-retroativa + lock) / corrigir_versao (revoga+recria) / montar_kit / inativar_item / criar_tabela (eh_padrao) / criar_linha / corrigir_linha / `preco_para_os` (query_service + contrato) + ViewSets ACTION_MAP + Idempotency + eventos | testes puros (Fakes) + E2E PG-real (409 código dup; 422 retroativa; kit; porta: vigente/ausente/revogada/kit-sem-linha; regressão INV-026 dura — consulta histórica imutável; concorrência 2 criar-versão) |
| **3 importação CSV** | parser puro + fixture replay + ImportacaoCatalogo staging + aceitar/rejeitar linha + REST importar/aceitar + TTL 90d command + SHA-256 no evento | testes parser (dialeto BR, BOM, colunas extras descartadas) + E2E staging não-auto-persiste + TTL |
| **4 (P7)** | família INV-PPS-* em REGRAS-INEGOCIAVEIS + `TestINV_PPS_*` nomeadas (TST-004) + hooks (candidatos: `pps-linha-imutavel-check` anti-regressão fail-open na porta; `pps-preco-nao-retroativo-check`; `pps-evento-pii-hash-check`) + casos `_test-runner` + contagens sincronizadas | hooks verdes contra arquivos reais; anti-drift |
| **P8** | matriz-reconciliacao (molde M7 8 seções) + ADR-0081 promovida aceito + emendas restantes (glossario? metricas?) + frontmatters stable | gate anti-drift |
| **P9** | auditores roteados INV-RITUAL-003 (seguranca·qualidade·llm·produto·idempotencia·lgpd [PII eventos/importação]·performance [porta+kit]; observabilidade se views; supplychain SÓ se dep nova — CSV-only não traz) | zero C/A/M (INV-RITUAL-001) |

## Riscos mapeados

1. **Sentinela 0 da OS** (TL-PPS-16): CHECK `preco > 0` em AMBAS as tabelas — teste unhappy.
2. **Truncamento retroativo** (TL-PPS-08): teste de regressão dura é OBRIGATÓRIO na Fatia 2.
3. **Exclusion + revogadas:** linha revogada sai do WHERE — repetir o teste M2 da frente #1
   (revogada + substituta mesma janela → resolve substituta) pra versão E linha.
4. **Kit:** `composicao_resolvida` usa a MESMA `data_referencia` pra todas as partes.
5. **Hash de texto livre nos eventos:** canonicalizar (ADR-0029) ANTES do hash — reusar
   helper existente do M5/M9 (não reimplementar).

## GATEs nascidos nesta frente (rastreados, não bloqueiam núcleo)

GATE-PPS-WIREIN-OS (**bloqueante pré-1º tenant externo** — preço da OS avulsa hoje é
client-supplied) · GATE-PPS-XLSX (dep openpyxl) · GATE-PPS-OUTBOX-ESTOQUE (promoção dos
eventos a outbox) · `[OAB-PRE-PROD]` cláusula ToS titularidade dados importados.
