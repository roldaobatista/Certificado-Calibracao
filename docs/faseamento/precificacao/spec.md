---
owner: agente-ia
revisado-em: 2026-06-12
proximo-review: 2026-09-12
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: precificacao
tipo: spec
versao: 2
relacionados:
  - docs/faseamento/precificacao/T-PRC-000-investigacao.md
  - docs/faseamento/precificacao/reviews-consolidado.md
  - docs/dominios/comercial/modulos/precificacao/prd.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - docs/faseamento/plano-dependencia-sistema.md
---

# Spec v2 — frente `precificacao` (núcleo Wave A PARCIAL, stub custo)

> Recorte sobre o PRD `docs/dominios/comercial/modulos/precificacao/prd.md`
> (US-PRC-001..008). Frente #3 da cadeia de preço. Greenfield (T-PRC-000 §1).
> **v2 (2026-06-12):** incorpora P2 — tech-lead TL-PRC-01..18 + advogado
> ADV-PRC-01..09, AMBOS APROVA COM CORREÇÕES (`reviews-consolidado.md`).
> **Decisões Roldão 2026-06-12 (rodada batch P0):** (1) DOIS modos de montagem
> completos com escolha na hora; (2) alçadas de desconto 10%/20%/dono;
> (3) semáforo de margem pro vendedor, números completos só pra papel autorizado.

## 1. Tese e fronteira

Precificação é **biblioteca de regras + motor de cálculo determinístico**
consumida por `orcamentos` (#5), `os` (US-OS-015 wire-in futuro) e `marketplace`
(V2). **Não emite documento próprio e não persiste resultado de cálculo** —
quem carimba snapshot é o consumidor (INV-026; molde `PrecoResolvido` ADR-0081).
Compõe SOBRE o preço de venda vigente da frente #2 (`preco_para_os` fail-closed)
— nunca refaz resolução de tabela, nunca cai pra preço de lista.

**Fronteira com billing:** ADR-0013 = preço DO SAAS (Wave B). Zero interseção.

## 2. Recorte núcleo vs diferido (por US do PRD)

| US | Núcleo Wave A | Diferido (GATE) |
|----|---------------|-----------------|
| US-PRC-001 regra por item | modos `PRECO_FIXO` + `MARGEM_ALVO` (custo manual declarado); versionamento WORM | `COST_PLUS` real — publicação BLOQUEADA sob stub (INV-PRC-COSTPLUS-STUB) → GATE-PRC-CUSTEIO-REAL |
| US-PRC-002 mínimo + sugerido | fórmulas canônicas do glossário; mínimo/sugerido ESTIMADOS quando regra tem custo manual (origem `CUSTO_MANUAL` explícita); determinismo AC-002-3 bit-a-bit (TL-PRC-18) | mínimo com custo REAL (custeio-real N7) |
| US-PRC-003 impacto do desconto | motor puro `calcular_precos` POR CESTA (<200ms p95): preço novo + semáforo + alçada + bloqueio mínimo | UI tempo-real (frente de telas) |
| US-PRC-004 aprovação por faixa | `FaixaAprovacaoDesconto` (default 0-10 livre / 10-20 gerente / 20+ dono) + `PedidoAprovacaoDesconto` one-shot WORM com fingerprint de binding + eventos | notificação push/e-mail (ADR-0060) → GATE-PRC-NOTIFICACAO |
| US-PRC-005 multi-tabela | matching **cliente-específico > padrão** via `VinculoTabelaPrecoCliente` (tabela própria desta frente — D-PRC-12); fallback POR ITEM na padrão | precedência contrato/segmento/região → GATE-PRC-TABELA-CONTRATO |
| US-PRC-006 simulações | deslocamento (R$/km × km) + imposto (alíquota vigente frente #1, SIMULAÇÃO — D-PRC-10) + parcelamento (taxa tenant) + comissão PREVISTA (% parâmetro) | comissão real → GATE-PRC-COMISSAO-REAL; carimbo no orçamento (consumidor #5) |
| US-PRC-007 alerta margem | motor expõe `abaixo_margem_minima` + `sem_regra_formacao` no resultado | alerta ativo + dashboard → GATE-PRC-ALERTA-GESTOR |
| US-PRC-008 histórico praticado | só o CONTRATO do evento `PrecoPraticado` MINIMIZADO (ADV-PRC-04) | materialização → GATE-PRC-HISTORICO-ORCAMENTOS (**pré-condição: LIA documentada**) |

## 3. Decisões cravadas (D-PRC-1..15)

- **D-PRC-1 — Path raiz achatada** `src/{domain,application,infrastructure}/precificacao/`
  (módulo comercial; molde D-PPS-1; ADR-0072 é só metrologia).
- **D-PRC-2 — Dois modos de montagem completos (decisão Roldão):**
  `COMPONENTES_CHECKLIST` (deslocamento/hora-técnica/ART são ITENS do catálogo;
  `PerfilComposicaoPreco` declara componentes esperados por item-serviço; motor
  emite `componentes_faltantes` avaliando a CESTA inteira) e `FECHADO_COM_AVISO`
  (1 valor; motor emite `aviso_composicao` configurável). **Escolha é POR
  ORÇAMENTO, na hora, pelo vendedor** (consumidor envia `modo_montagem`).
- **D-PRC-3 — Alçadas default 10/20/dono (decisão Roldão):** seed via etapa no
  `provisionar_tenant` (ADR-0015) + RunPython pra tenants existentes (TL-PRC-15);
  faixas editáveis por tenant — alteração é **replace-all atômico** (use case
  valida o CONJUNTO contíguo 0..100 sem buraco/sobreposição; TL-PRC-16).
- **D-PRC-4 — Semáforo RBAC server-side (decisão Roldão):** `semaforo_margem`
  (VERDE ≥ alvo / AMARELO entre piso e alvo / VERMELHO < piso ou prejuízo /
  INDISPONIVEL sem custo) pra qualquer papel com `precificacao.calcular`;
  `margem_estimada_percentual` + `custo_estimado` SÓ com `precificacao.ver_margem`
  — **choke-point único `filtrar_visao_margem()` em TODO serializer da frente**
  (TL-PRC-12), incl. pedidos de aprovação (ADV-PRC-06); leitura de regra
  (expõe custo/margem-alvo) exige `configurar` ou `ver_margem`; papel aprovador
  DEVE ter `ver_margem` (seed coerente). **`preco_minimo` é visível a qualquer
  papel com `calcular`** — vazamento parcial de piso aceito CONSCIENTEMENTE
  (vendedor precisa do chão; ADV-PRC-07); custo/margem seguem gated.
- **D-PRC-5 — `CustoProvider` (Protocol) + stub fail-closed:** stub retorna
  `CustoIndisponivel` EXPLÍCITO (nunca 0 silencioso — INV-PRC-CUSTO-EXPLICITO).
  Custo manual declarado na regra (`custo_manual_declarado > 0` + obrigatório
  `custo_referencia_em`, origem `CUSTO_MANUAL`) é a fonte Wave A pra MARGEM_ALVO;
  provider real chega com `custeio-real` (N7) sem mudar contrato.
- **D-PRC-6 — INV-PRC-COSTPLUS-STUB fail-closed:** publicar regra `COST_PLUS`
  exige provider de custo real; sob stub → 422 `CustoRealIndisponivel`.
  Mecânica ADR-0007: função de domínio pura recebe `custo_real_disponivel: bool`;
  o use case `publicar_regra` consulta o `CustoProvider`. Moldes fail-closed da
  casa: `PrecoTabelaAusente` (D-PPS-2) + validação-no-use-case (ADR-0073).
  Assimetria com M7 (fail-open lazy) é LEGÍTIMA: aqui o gate é em tempo de
  CONFIGURAÇÃO e o modo de falha do fail-open seria prejuízo silencioso (gap #6).
- **D-PRC-7 — `RegraFormacaoPreco` versionada WORM molde Imposto:** imutável
  pós-publicação + one-shot `revogado_em` + block-DELETE + não-sobreposição de
  vigência por `(tenant, item)` (exclusion btree_gist molde PPS 0004); correção
  = revogar+recriar (D-PPS-8).
- **D-PRC-8 — Preço mínimo Wave A ESTIMADO; bloqueio DURO quando calculável:**
  com custo manual → mínimo pela fórmula; violação = 422 `PrecoMinimoViolado`
  (PROIBIÇÃO, não aprovável — AC-PRC-003-3). Sem custo → mínimo `INDISPONIVEL`,
  governam só as alçadas. Resultado SEMPRE carrega `origem_custo` +
  `custo_declarado_em` (staleness visível — TL-PRC-07). **O bloqueio é sempre
  reversível pelo próprio tenant em autosserviço (revogar a regra remove o
  mínimo); o sistema nunca impede venda por política que o tenant não possa
  desfazer** — fato probatório de alocação de responsabilidade no ToS
  (ADV-PRC-08 `[OAB-PRE-PROD]`).
- **D-PRC-9 — Motor puro, sem persistência:** `calcular_precos` determinístico;
  saída `CalculoPrecoResultado` frozen AUTOSSUFICIENTE pra replay (TL-PRC-01):
  refs probatórias + `motor_versao` + eco das entradas. Consumidor carimba.
  Persistência da frente: só config + workflow de aprovação.
- **D-PRC-10 — Simulação fiscal usa `Imposto` vigente da frente #1** (estimada;
  "cálculo fiscal exato" é non-goal do PRD — porta fiscal NÃO entra no motor).
- **D-PRC-11 — Entrada canônica do motor é a CESTA** (TL-PRC-14):
  `calcular_precos(itens=[...], modo_montagem, ...)` — `componentes_faltantes`
  é incomputável item-a-item; evita N+1 (lição GATE-PPS-KIT-BATCH). Sem cache
  cross-request; memoização POR REQUEST de Imposto/Parâmetros/Faixas;
  `assertNumQueries` no P7.
- **D-PRC-12 — Vínculo multi-tabela em tabela PRÓPRIA desta frente** (TL-PRC-13):
  `VinculoTabelaPrecoCliente` (tenant, tabela_id FK→PPS, cliente_id, vigência
  ADR-0030, UNIQUE parcial vigente por (tenant, cliente)) — **zero retrofit de
  schema na PPS fechada**. `preco_para_os` ganha parâmetro ADITIVO
  `tabela_id: UUID | None = None` (+ emenda ADR-0081 no ponto "tabela PADRÃO").
  **Fallback POR ITEM na tabela padrão** quando a tabela do cliente não cobre o
  item (não conflita com anti-fallback ADR-0081 — ambas são tabelas de VENDA;
  `PrecoResolvido.tabela_id` aponta a realmente usada). `cliente_id` segue
  ADR-0032: consumer de `Cliente.Anonimizado` revoga o vínculo.
- **D-PRC-13 — Cortesia/desconto 100% (delegação PPS `value_objects.py:6-8`):**
  PERMITIDO com alçada **DONO sempre** (independe de faixa); `preco_final` no
  resultado é `Decimal ≥ 0` próprio (NUNCA reusa VO `Preco > 0` —
  INV-PPS-PRECO-POSITIVO intacto); flag `cortesia: bool` no resultado e no pedido.
- **D-PRC-14 — Binding aprovação↔cálculo por fingerprint** (TL-PRC-08):
  `PedidoAprovacaoDesconto.fingerprint_calculo` = hash canônico ADR-0029 de
  (entradas + refs + pct); consumidor só consome a aprovação se o fingerprint
  do cálculo vigente bater (molde fingerprint de idempotência B6). Contexto
  tipado (TL-PRC-09): `contexto_tipo` ENUM ORCAMENTO|OS|AVULSO + `contexto_id
  UUID NULL` + snapshot probatório embutido — FK real é constraint aditiva
  quando `orcamentos` existir.
- **D-PRC-15 — Justificativa: hash no WORM, cru em tabela-par mutável**
  (ADV-PRC-01, molde triplo da casa): tabela WORM e eventos levam SÓ
  `justificativa_hash` (ADR-0029 + HMAC-tenant — eliminável por
  crypto-shredding); texto cru vive em `JustificativaDecisaoDesconto`
  (soft-delete ADR-0031, retenção 5a ou pedido do titular citado) porque
  AC-PRC-004-3 exige leitura pelo vendedor.

## 4. Modelo (domínio)

**Entidades:** `RegraFormacaoPreco` (tenant, item_id, modo PRECO_FIXO|MARGEM_ALVO|COST_PLUS,
preco_fixo?, custo_manual_declarado?, **custo_referencia_em?**, margem_alvo_pct?,
margem_piso_pct?, vigência ADR-0030, versão densa, WORM) · `PerfilComposicaoPreco`
(tenant, item_servico_id, componentes_esperados: tuple[item_id], aviso_texto?,
mutável `deletado_em`) · `FaixaAprovacaoDesconto` (tenant, faixas contíguas
[pct_de, pct_ate, alcada LIVRE|GERENTE|DONO], **versao/hash do conjunto** —
replace-all atômico) · `PedidoAprovacaoDesconto` (tenant, contexto_tipo,
contexto_id?, snapshot probatório, pct_solicitado, **cortesia: bool**,
alcada_exigida, **fingerprint_calculo**, estado SOLICITADO→APROVADO|NEGADO
one-shot, solicitante_id, decisor_id, **justificativa_hash**, WORM) ·
`JustificativaDecisaoDesconto` (tabela-par mutável: pedido_id, texto cru,
soft-delete — D-PRC-15) · `VinculoTabelaPrecoCliente` (D-PRC-12) ·
`ParametrosPrecificacaoTenant` (custo_km, taxa_parcelamento_mensal,
pct_comissao_prevista, margem_alvo_default, margem_piso_default; versionado).

**VOs:** `Percentual` (0..100, escala 2; conversão pra fração documentada nas
fórmulas; resultado `ROUND_HALF_EVEN` escala 2 — determinismo bit-a-bit
TL-PRC-18) · `CalculoPrecoResultado` (frozen, POR CESTA: itens[preco_base
PrecoResolvido embutido, preco_final Decimal ≥ 0, desconto_pct, semaforo,
margem_estimada?, custo_estimado?, preco_minimo?, origem_custo,
custo_declarado_em?, sem_regra_formacao, cortesia], componentes_faltantes,
avisos, alcada_exigida, **motor_versao**, **faixas_versao**, **imposto_ref
(id+versão)**, **parametros_versao**, **eco das entradas** [km, desconto_pct,
modo_montagem, parcelas] — autossuficiente pra replay/carimbo INV-026) ·
fórmulas canônicas do glossário (denominador ≤ 0 → `ParametrosInviaveis` 422).

**Erros:** `CustoRealIndisponivel`, `PrecoMinimoViolado`, `ParametrosInviaveis`,
`FaixasDescontoInvalidas`, `RegraVigenteAusente` (SÓ no endpoint `vigente` →
404; o motor NUNCA o levanta — caminho sem regra é válido e marca
`sem_regra_formacao: true` + semáforo INDISPONIVEL: "não existe chão", buraco
visível — TL-PRC-05).

## 5. Invariantes candidatas (P7 crava em REGRAS)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-PRC-COSTPLUS-STUB | domínio fail-closed + teste + hook `prc-costplus-stub-check` |
| INV-PRC-REGRA-IMUTAVEL | WORM Padrão B (triggers molde Imposto/PPS) |
| INV-PRC-REGRA-SEM-SOBREPOSICAO | exclusion btree_gist (tenant, item) WHERE revogado IS NULL |
| INV-PRC-APROVACAO-ONE-SHOT | UPDATE escopado em SOLICITADO + trigger one-shot |
| INV-PRC-APROVACAO-INDEPENDENTE | `decisor_id != solicitante_id` — domínio + CHECK + UNHAPPY (TL-PRC-10, molde ADR-0026) |
| INV-PRC-MINIMO-BLOQUEIO | 422 duro quando mínimo calculável; NUNCA aprovável |
| INV-PRC-CUSTO-EXPLICITO | stub nunca retorna 0; ausência = `CustoIndisponivel` tipado |
| INV-PRC-MARGEM-RBAC | `filtrar_visao_margem()` choke-point em TODOS os serializers + teste UNHAPPY por endpoint + hook `prc-margem-rbac-check` |
| INV-PRC-SEGREDO-LOG | custo/margem/parâmetros NUNCA em log estruturado, exceção, payload de evento em claro, corpo 4xx/5xx — só refs (ADV-PRC-06) |
| INV-PRC-JUSTIFICATIVA-HASH | texto livre nunca cru em WORM/evento; cru só na tabela-par mutável + hook `prc-evento-pii-hash-check` |
| INV-PRC-FAIXAS-CONTIGUAS | replace-all atômico valida CONJUNTO (0..100) + exclusion cinto |
| INV-026 (herdada) | motor não persiste; consumidor carimba snapshot |

## 6. Portas, eventos e seams

- **Consome:** `preco_para_os`/`PrecoResolvido` (PPS; ganha param aditivo
  `tabela_id` — D-PRC-12); `Imposto`/`RegimeTributario` vigentes (frente #1);
  authz + idempotência + eventos canônicos + perfil server-side (F-B/F-C).
- **Expõe:** `calcular_precos` (porta de aplicação POR CESTA); `CustoProvider`
  Protocol (real = custeio-real N7); contrato do evento
  `Precificacao.PrecoPraticado` MINIMIZADO (ADV-PRC-04): item_id, `cliente_ref`
  padrão ADR-0032, orcamento_ref, preco_final, desconto_pct, fechado_em —
  **`margem_realizada` FORA** (deriva sob RBAC na materialização).
- **Eventos WORM (cadeia; campos hashificados por evento — ADV-PRC-03):**

| Evento | Hashificados | Em claro permitidos |
|--------|--------------|---------------------|
| `AprovacaoSolicitada` | `solicitante_id_hash` | pct, cortesia, alcada_exigida, contexto (UUIDs), fingerprint |
| `AprovacaoDecidida` | `decisor_id_hash`, `justificativa_hash` | estado, pct, contexto (UUIDs) |
| `RegraPublicada`/`RegraRevogada` | `criado_por_id_hash`, `motivo_hash` | item_id, modo, versão, vigências |
| `PerfilComposicaoAlterado` | `aviso_texto_hash`, `criado_por_id_hash` | item_servico_id, componentes (UUIDs) |
| `ParametrosAlterados`/`FaixasDescontoAlteradas` | `criado_por_id_hash`; **valores NÃO entram** (diff de NOMES de campos — segredo comercial) | versões/refs |

## 7. REST (núcleo)

`RegraFormacaoPrecoViewSet`: publicar / revogar / retrieve / `vigente?item_id&em=`
(leitura gated `configurar`|`ver_margem`) · `CalculoPrecoView`: POST `calcular`
(cesta, stateless, SEM Idempotency-Key — leitura computada, molde `consultar`
fiscal) · `AprovacaoDescontoViewSet`: solicitar / decidir (one-shot; predicate
ABAC **`alcada_cobre`** vinculado à action, resource={alcada_exigida, papel} —
TL-PRC-11 molde M3) / pendentes · `ConfiguracaoPrecificacaoViewSet`:
faixas-desconto (replace-all) / perfil-composicao / parametros (gated
`configurar`|`ver_margem` — NUNCA só `calcular`) · `VinculoTabelaClienteViewSet`:
criar / revogar / listar vínculo cliente→tabela (gated `configurar`|`ver` —
fecha AC-PRC-005-1 via REST). Ações authz `precificacao.*`: núcleo
(`configurar`, `calcular`, `ver_margem`, `aprovar_desconto`) + granulares de RBAC
(`ver` leitura sem margem, `solicitar_aprovacao`, `alcada_dono`, `alcada_gerente`
— derivam o papel do decisor server-side; seed migrations 0006/0009).

## 8. Non-goals (além dos do PRD §5)

UI/dashboard · notificação push/e-mail (ADR-0060) · histórico praticado
materializado (GATE + LIA) · preço por ponto de calibração (ADR-0077 habilita
futuro; sem PRD) · comissão real · multi-tabela por contrato/região · juros
compostos exatos de gateway · cache cross-request de cálculo.

## 9. GATEs rastreados

GATE-PRC-CUSTEIO-REAL (cost-plus + mínimo real + alerta de staleness do custo
manual) · GATE-PRC-HISTORICO-ORCAMENTOS (**pré-condição: LIA art. 7º IX
documentada**; perfil pricing PF/MEI entra no export art. 18 ao ativar) ·
GATE-PRC-ALERTA-GESTOR · GATE-PRC-NOTIFICACAO (resolve contexto na ENTREGA;
margem só com `ver_margem` — ADV-PRC-02) · GATE-PRC-COMISSAO-REAL ·
GATE-PRC-TABELA-CONTRATO (AC-005-4 completo) · **GATE-PPS-WIREIN-OS** (da
frente #2; consome ESTA frente + KIT-BATCH; bloqueante pré-1º tenant externo).

## 10. Log de revisões (P2 — 2026-06-12)

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES**: TL-PRC-01..18
  incorporados (01 refs replay / 03 molde corrigido / 05 RegraVigenteAusente /
  06 cortesia / 07 staleness / 08 fingerprint / 09 contexto tipado / 10
  independência / 11 predicate alcada_cobre / 12 choke-point margem / 13
  vínculo cliente + fallback por item / 14 cesta / 15 seed provisionar / 16
  replace-all / 17-18 fatia 1a + arredondamento).
- ✅ `advogado-saas-regulado` — **APROVA COM CORREÇÕES**: ADV-PRC-01..09
  incorporados (01 justificativa hash+par / 02 contexto UUIDs / 03 tabela de
  hashificados + hook / 04 PrecoPraticado minimizado + LIA / 05 RAT empregado /
  06 INV-PRC-SEGREDO-LOG / 07 preco_minimo consciente / 08 frase
  reversibilidade + lote OAB / 09 retenção — textos prontos no
  `reviews-consolidado.md`, aplicar cross-doc no P3).
- Emendas cross-doc pendentes P3: retencao-matriz (4 linhas + DRILL-RET-PRC-01)
  + lgpd-rat (RAT-PRC-DESCONTO) + ADR-0081 (param `tabela_id`).
- Decisões Roldão incorporadas: D-PRC-2 (dois modos), D-PRC-3 (alçadas),
  D-PRC-4 (semáforo RBAC).
