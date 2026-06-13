---
owner: agente-ia
revisado-em: 2026-06-12
proximo-review: 2026-09-12
status: draft
proximo-passo: ready-for-implement (revisado pelo orquestrador 2026-06-12; stable em lote R22)
diataxis: reference
audiencia: [agente, tech-lead, auditor]
frente: precificacao
tipo: plan
relacionados:
  - docs/faseamento/precificacao/spec.md
  - docs/faseamento/precificacao/reviews-consolidado.md
  - docs/faseamento/precificacao/T-PRC-000-investigacao.md
  - docs/dominios/comercial/modulos/precificacao/prd.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - docs/faseamento/produtos-pecas-servicos/plan.md
  - docs/faseamento/configuracoes-sistema/plan.md
---

# Plan — frente `precificacao` (núcleo Wave A PARCIAL, stub custo)

> Deriva da `spec.md` v2 (P2 incorporado — tech-lead TL-PRC-01..18 +
> advogado ADV-PRC-01..09, AMBOS APROVA COM CORREÇÕES). Decisões D-PRC-1..15
> cravadas na spec §3; este plan só materializa arquitetura por camada, fatias,
> riscos e GATEs. Molde de execução = frentes #1 `configuracoes-sistema` e #2
> `produtos-pecas-servicos` (mesma anatomia de fatias). Frente FINANCEIRA →
> risco alto: P9 roda lente financeira completa; BAIXOs em lote pós-fechamento
> (ritual R10 — módulo não-metrológico).

## Arquitetura (resumo operacional)

- **Path (D-PRC-1):** raiz achatada `src/{domain,application,infrastructure}/precificacao/`.
  App label `precificacao`; módulo comercial, NÃO-metrologia → não aninha
  (ADR-0072 é só metrologia). Sem `_APP_MODULE_SUBPATH` no conftest.
- **Tabelas (7):** `regra_formacao_preco`, `perfil_composicao_preco`,
  `faixa_aprovacao_desconto`, `pedido_aprovacao_desconto`,
  `justificativa_decisao_desconto` (tabela-par mutável — D-PRC-15),
  `vinculo_tabela_preco_cliente` (D-PRC-12), `parametros_precificacao_tenant`
  (versionado). Todas RLS v2 FORCE + 4 policies.
- **Motor SEM persistência (D-PRC-9):** `calcular_precos` é função de aplicação
  determinística POR CESTA (D-PRC-11) que NÃO grava nada; saída
  `CalculoPrecoResultado` frozen autossuficiente pra replay/carimbo INV-026.
  Persistência da frente = SÓ config + workflow de aprovação. O consumidor
  (#5 orçamentos) carimba o snapshot — esta frente não tem read-model `CalculoPreco`
  no banco (o agregado do PRD `modelo-de-dominio.md` é só transiente).
- **Imutabilidade WORM molde Imposto/PPS (D-PRC-7):** `regra_formacao_preco`
  com molde Imposto COMPLETO (trigger Padrão B campos probatórios + `vigencia_fim`
  one-shot + `revogado_em`+motivo one-shot + block DELETE) + exclusion
  `btree_gist` `WHERE revogado_em IS NULL` por `(tenant, item)` (não-sobreposição).
  Correção de regra = revogar+recriar (molde D-PPS-8). `pedido_aprovacao_desconto`
  é WORM one-shot (SOLICITADO→APROVADO|NEGADO via UPDATE escopado + trigger).
- **Concorrência:** advisory lock por `(tenant, item)` na publicação de regra
  (densidade `versao_n = max+1` sob lock — molde PPS, **namespace novo** a alocar
  no P3 de implementação, ex. `880_404`); `replace-all` atômico de faixas sob
  lock por tenant (D-PRC-3 / TL-PRC-16).
- **Custo via porta STUB fail-closed (D-PRC-5):** `CustoProvider` (Protocol no
  domínio, molde `CoberturaEscopoPort` da calibração) + `StubCustoProvider`
  injetado na view que retorna `CustoIndisponivel` EXPLÍCITO (nunca 0 —
  INV-PRC-CUSTO-EXPLICITO). Fonte Wave A da margem = `custo_manual_declarado`
  na própria regra (origem `CUSTO_MANUAL` + obrigatório `custo_referencia_em`).
  Provider real chega no `custeio-real` (N7) sem mudar contrato.
- **Anti-cost-plus-sob-stub (D-PRC-6 / INV-PRC-COSTPLUS-STUB):** mecânica ADR-0007
  — função de domínio pura recebe `custo_real_disponivel: bool`; o use case
  `publicar_regra` consulta o `CustoProvider`. Publicar `COST_PLUS` sob stub →
  422 `CustoRealIndisponivel`. Fail-CLOSED (assimetria com fail-open lazy do M7 é
  legítima: gate em tempo de CONFIGURAÇÃO; modo de falha do open seria prejuízo
  silencioso). Molde correto: `PrecoTabelaAusente` (D-PPS-2) + validação-no-use-case
  (ADR-0073) — NÃO o M7.
- **RBAC de campo server-side (D-PRC-4):** choke-point ÚNICO
  `filtrar_visao_margem(payload, pode_ver_margem)` em TODO serializer da frente
  (incl. serializer de pedido de aprovação — ADV-PRC-06). `semaforo_margem` e
  `preco_minimo` saem pra qualquer papel com `precificacao.calcular`;
  `margem_estimada_percentual` + `custo_estimado` SÓ com `precificacao.ver_margem`.
  Leitura de regra (expõe custo/margem-alvo) exige `configurar` OU `ver_margem`.
  Papel aprovador DEVE ter `ver_margem` (seed coerente). Segredo comercial
  estende a logs/exceções/eventos/corpo de erro (INV-PRC-SEGREDO-LOG).
- **Binding aprovação↔cálculo (D-PRC-14):** `pedido_aprovacao_desconto.fingerprint_calculo`
  = hash canônico ADR-0029 de (entradas + refs + pct); o consumidor só consome a
  aprovação se o fingerprint do cálculo vigente bater (molde fingerprint de
  idempotência B6 — reusar `services_idempotencia`/helper de canonicalização, não
  reimplementar). Contexto tipado: `contexto_tipo` ENUM ORCAMENTO|OS|AVULSO +
  `contexto_id UUID NULL` + snapshot probatório embutido; FK real vira constraint
  aditiva quando `orcamentos` existir.
- **Predicate ABAC `alcada_cobre` (TL-PRC-11 / D-PRC-3):** registrado via
  `register_predicate("alcada_cobre", fn, actions={"precificacao.aprovar_desconto"})`
  (molde `src/infrastructure/authz/predicates.py`); resource = {alcada_exigida,
  papel_do_decisor}; nega se a alçada do papel não cobre a faixa exigida (gerente
  decidindo faixa DONO → deny). Segregação `decisor_id != solicitante_id`
  (INV-PRC-APROVACAO-INDEPENDENTE, molde ADR-0026) no domínio + CHECK + UNHAPPY.
- **Justificativa hash+par (D-PRC-15 / ADV-PRC-01):** WORM e eventos levam SÓ
  `justificativa_hash` (ADR-0029 + HMAC-tenant ADR-0064 — eliminável por
  crypto-shredding); texto cru vive em `justificativa_decisao_desconto`
  (soft-delete ADR-0031, TTL 5a — D-PRC-15) porque AC-PRC-004-3 exige leitura
  pelo vendedor.
- **Eventos (cadeia-só, `outbox=False`):** payload hashificado POR EVENTO
  (spec §6, tabela ADV-PRC-03) — `*_id_hash` de pessoa + `*_hash` de texto livre;
  **valores de Parametros/Faixas NUNCA entram em claro** (diff de NOMES de campos,
  segredo comercial). Reusar helper de hash canônico do M5/M9/PPS — não reimplementar.
- **Porta consumida `preco_para_os` (D-PRC-12):** ganha param ADITIVO
  `tabela_id: UUID | None = None` (emenda ADR-0081 JÁ APLICADA — verificada).
  `vinculo_tabela_preco_cliente` resolve cliente→tabela DENTRO desta frente (zero
  retrofit de schema na PPS fechada); **fallback POR ITEM na tabela padrão** quando
  a tabela do cliente não cobre o item (ambas são tabelas de VENDA; não viola
  anti-fallback ADR-0081 — só proíbe venda→lista). `cliente_id` segue ADR-0032
  (consumer de `Cliente.Anonimizado` revoga o vínculo).
- **Determinismo bit-a-bit (TL-PRC-18 / AC-002-3):** VO `Percentual` (0..100,
  escala 2); conversão pra fração documentada nas fórmulas; resultado
  `ROUND_HALF_EVEN` escala 2. Denominador ≤ 0 nas fórmulas → `ParametrosInviaveis`
  (422). `RegraVigenteAusente` levanta SÓ no endpoint `vigente` (404); o motor
  NUNCA o levanta — caminho sem regra é válido (`sem_regra_formacao: true` +
  semáforo INDISPONIVEL — TL-PRC-05).

## Cross-doc (verificado — JÁ APLICADO no commit `dcb8621`, NÃO recriar tasks)

- `retencao-matriz.md` — 4 linhas precificacao (regra/faixa/perfil/parâmetros;
  pedido WORM; justificativa crua; PrecoPraticado dormante) + DRILL-RET-PRC-01
  JÁ presentes (§2 linhas 96-99, §5 DRILL). Matriz CONGELADA (ritual R17) — só o
  apontador-PII; NÃO criar task de RAT formal.
- `lgpd-rat.md` — RAT-PRC-DESCONTO JÁ presente (linha 55).
- `ADR-0081` — emenda param `tabela_id` JÁ aplicada (linhas 46-54).
- **Pendência cross-doc REAL no P3 do plan:** nenhuma emenda nova; só a
  promoção/registro do **GATE-PPS-WIREIN-OS** (que passa a consumir ESTA frente)
  e o registro dos GATE-PRC-* no `STATUS-GERADO.md` + AGENTS §12 (P8).

## Fatias

| Fatia | Entrega | Verificação (não declarar pronto sem rodar) |
|---|---|---|
| **1a domínio puro** | enums (`ModoFormacaoPreco` PRECO_FIXO/MARGEM_ALVO/COST_PLUS, `OrigemCusto` CUSTO_MANUAL/PROVIDER_REAL/INDISPONIVEL, `Semaforo` VERDE/AMARELO/VERMELHO/INDISPONIVEL, `Alcada` LIVRE/GERENTE/DONO, `ContextoTipo` ORCAMENTO/OS/AVULSO, `EstadoPedido` SOLICITADO/APROVADO/NEGADO, `ModoMontagem` COMPONENTES_CHECKLIST/FECHADO_COM_AVISO) + VO `Percentual` + VO `CalculoPrecoResultado` frozen autossuficiente + entidades frozen (RegraFormacaoPreco, PerfilComposicaoPreco, FaixaAprovacaoDesconto, PedidoAprovacaoDesconto, VinculoTabelaPrecoCliente, ParametrosPrecificacaoTenant) + porta `CustoProvider` Protocol + `StubCustoProvider` + fórmulas canônicas puras (`calcular_precos` POR CESTA, semáforo, mínimo/sugerido, anti-retroativa de vigência, faixas-contíguas, fingerprint canônico, `decisor != solicitante`) + erros + repository Protocols | testes puros (determinismo bit-a-bit cross-versão; cesta sem componente esperado → `componentes_faltantes`; cortesia 100% não estoura Preco>0; faixas com buraco → `FaixasDescontoInvalidas`; mínimo violado → bloqueio; stub → `CustoIndisponivel`); ruff/mypy limpos |
| **1b schema PG** | models colunas tipadas (7 tabelas) + migrations 0001..0006 (CreateModel+UNIQUEs+CHECK `preco_final ≥ 0` na resultante / RLS v2 ×7 / triggers WORM molde Imposto na regra + one-shot estado no pedido / exclusion btree_gist `(tenant,item)` regra / grants / seed authz `precificacao.*`) + mappers + repositories Django (advisory lock namespace novo) + drill `validar_precificacao` + conftest seed | migrate OK; makemigrations --check; testes PG-real (RLS UNHAPPY ×7; trigger WORM regra UPDATE direto → raise; one-shot pedido; exclusion overlap + revogada+substituta mesma janela; CHECK; seed authz presente); drill PASS |
| **2 use cases + porta + REST** | publicar_regra (consulta CustoProvider → anti-cost-plus-stub) / revogar_regra / `calcular_precos` (porta de aplicação POR CESTA, stateless) / solicitar_aprovacao (fingerprint + contexto tipado) / decidir_aprovacao (one-shot + independência + alcada_cobre) / configurar_faixas (replace-all atômico) / configurar_perfil_composicao / configurar_parametros / `preco_para_os(..., tabela_id=)` consumido com fallback-por-item + ViewSets ACTION_MAP + `filtrar_visao_margem` em TODOS serializers + Idempotency-Key (solicitar/decidir/publicar/configurar — `calcular` SEM key, leitura computada) + eventos `Precificacao.*` hashificados + registro predicate `alcada_cobre` | testes puros (Fakes) + E2E PG-real (publicar COST_PLUS sob stub → 422; vazamento margem por endpoint não-calculadora; fingerprint divergente → recusa; decisor==solicitante → recusa; gerente decide alçada DONO → predicate nega; cesta multi-item; fallback-por-item na tabela padrão; replace-all faixas; `assertNumQueries` no `calcular_precos` — sem N+1, memoização por request) |
| **3 (P7) INVs + hooks + testes nomeados** | família `INV-PRC-*` (12) em REGRAS-INEGOCIAVEIS (nova seção `## INV-PRC-*`) + `TestINV_PRC_*` nomeadas (TST-004; PG-real onde enforcement é banco) + hooks novos no `pre-commit-manifest.tsv` (NÃO write-time — ritual R5/manifest): `prc-costplus-stub-check`, `prc-margem-rbac-check`, `prc-evento-pii-hash-check` + casos `_test-runner` + `settings.json` se necessário + contagens via `scripts/status-projeto.sh --check` (nunca em prosa — denylist) | hooks verdes contra arquivos reais (`bash .claude/hooks/_test-runner.sh`); anti-drift; `status-projeto.sh --check` verde |
| **P8** | matriz-reconciliação ENXUTA (ritual R20 — só §1 US/INV↔código, §2 INV↔teste, §8 ata do P9) + registro GATE-PRC-* no STATUS-GERADO + AGENTS §12 + GATE-PPS-WIREIN-OS atualizado (consome esta frente) + frontmatters draft→stable em LOTE periódico (ritual R22 — não passo formal aqui) | gate anti-drift; `status-projeto.sh --check` |
| **P9** | auditores roteados (INV-RITUAL-003): 6 essenciais SEMPRE (qualidade·segurança·llm·idempotência·conformidade-lgpd [PII em eventos/justificativa/RAT]·produto) + performance (motor+porta+cesta — N+1/200ms) + observabilidade (views financeiras + segredo em log) ; supplychain SÓ se dep nova (núcleo não traz); drift-docs FORA do fechamento (ritual R7 — gate mecânico + varredura semântica mensal). Verificação adversarial de TODO MÉDIO+ antes do mutirão (ritual R6); 2ª passada escopada (ritual R5) | zero C/A/M (INV-RITUAL-001) → frente FECHADA + CURRENT.md; BAIXOs em lote pós-fechamento (R10) |

## Riscos mapeados

1. **RBAC de campo é padrão NOVO no `src/`** (TL-PRC-12): zero molde — o
   choke-point `filtrar_visao_margem()` PRECISA estar em TODO serializer
   (incl. pedido de aprovação) ANTES de qualquer endpoint sair. Hook
   `prc-margem-rbac-check` + teste UNHAPPY por endpoint não-calculadora são
   obrigatórios. Risco = vazar custo/margem por um serializer esquecido.
2. **Fail-closed cost-plus sob stub** (D-PRC-6): a regressão a evitar é alguém
   "destravar" cost-plus no use case quando o provider real chegar e esquecer
   que sob STUB o gate é DURO. Teste E2E `publicar COST_PLUS sob stub → 422` +
   hook `prc-costplus-stub-check`.
3. **Segredo comercial além do RBAC** (INV-PRC-SEGREDO-LOG / ADV-PRC-06):
   custo/margem/parâmetros NUNCA em log estruturado, exceção, payload de evento
   em claro, corpo 4xx/5xx. Eventos Parametros/Faixas são refs-only (diff de
   NOMES de campos). Risco = `logger.info(f"... custo={custo}")` num `_falha`.
4. **N+1 no motor por cesta** (TL-PRC-14): `componentes_faltantes` exige avaliar
   a cesta inteira; sem memoização por request de Imposto/Parâmetros/Faixas vira
   N+1. `assertNumQueries` na Fatia 2 é cinto (lição GATE-PPS-KIT-BATCH).
5. **Fingerprint canônico** (D-PRC-14): canonicalizar (ADR-0029) ANTES do hash —
   reusar helper existente (M5/M9/PPS), não reimplementar. Fingerprint divergente
   tem que RECUSAR consumo da aprovação (teste nomeado).
6. **Hash de texto livre nos eventos**: justificativa/motivo/aviso_texto sempre
   hash (ADR-0029 + HMAC-tenant) — texto cru só na tabela-par mutável. Hook
   `prc-evento-pii-hash-check` (denylist adaptada do PEPH/PPS).
7. **Determinismo bit-a-bit** (TL-PRC-18): `ROUND_HALF_EVEN` escala 2 +
   conversão `Percentual`→fração documentada; AC-002-3 exige mesmo resultado
   cross-versão de motor (teste de regressão de determinismo).
8. **Fallback-por-item vs anti-fallback ADR-0081** (D-PRC-12): a única exceção
   permitida é tabela-cliente→tabela-padrão (ambas VENDA); jamais venda→lista.
   `PrecoResolvido.tabela_id` aponta a tabela realmente usada (rastreável).

## GATEs nascidos / rastreados (não bloqueiam fechamento do núcleo)

- **GATE-PRC-CUSTEIO-REAL** — cost-plus + preço mínimo REAL + alerta de staleness
  do `custo_referencia_em`; destrava quando `custeio-real` (N7) implementa o
  `CustoProvider` real (substitui o stub sem mudar contrato).
- **GATE-PRC-HISTORICO-ORCAMENTOS** — materialização de `Precificacao.PrecoPraticado`
  / `HistoricoPrecoPraticado`; **pré-condição: LIA art. 7º IX documentada**;
  perfil pricing PF/MEI entra no export art. 18 ao ativar. Quem publica o evento é
  o consumidor (#5 orçamentos) — diferido até `orcamentos` existir.
- **GATE-PRC-ALERTA-GESTOR** — alerta ativo + dashboard de margem (US-PRC-007 parte 2).
- **GATE-PRC-NOTIFICACAO** — push/e-mail de pedido de aprovação (ADR-0060);
  resolve contexto na ENTREGA, margem só com `ver_margem` (ADV-PRC-02).
- **GATE-PRC-COMISSAO-REAL** — comissão real (módulo `comissoes` próprio); hoje só
  simulação por % parâmetro.
- **GATE-PRC-TABELA-CONTRATO** — precedência contrato/segmento/região (AC-005-4
  completo); Wave A só cliente-específico > padrão.
- **GATE-PPS-WIREIN-OS** (herdado da frente #2; **bloqueante pré-1º tenant
  externo**) — preço da OS avulsa hoje client-supplied; conserto via porta
  `preco_para_os` fail-closed CONSOME esta frente (resolução de tabela por cliente).
- **`[OAB-PRE-PROD]`** — cláusula ToS: bloqueio de mínimo sempre reversível pelo
  tenant em autosserviço (fato probatório de alocação de responsabilidade —
  ADV-PRC-08); exclusão de lucros cessantes sob cap ADR-0019/0028; ressalva CDC
  finalismo mitigado pra MEI/pequeno. Texto pronto no `reviews-consolidado.md` §2.

## Decisões do orquestrador (2026-06-12 — revisão do P3; nenhuma de PRODUTO em aberto)

1. **Namespace do advisory lock = `880_404`** — CONFIRMADO (sequência da casa:
   `880_402` M8/CFG, `880_403` PPS).
2. **6 migrations (0001..0006)** — CONFIRMADO. A extensão `btree_gist` JÁ vem dos
   init scripts do PG (verificado nos moldes: `configuracoes_sistema/migrations/0004`
   e `produtos_pecas_servicos/migrations/0004` registram isso em comentário) —
   exclusion entra na 0004 sem `CREATE EXTENSION`.
3. **`CalculoPreco` transiente** — CONFIRMADO: spec v2 (D-PRC-9) vence; a emenda do
   `modelo-de-dominio.md` (draft divergente) acontece no P8 via T-PRC-060.
