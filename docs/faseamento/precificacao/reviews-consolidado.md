---
owner: agente-ia
revisado-em: 2026-06-12
proximo-review: 2026-09-12
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: precificacao
tipo: reviews-p2
relacionados:
  - docs/faseamento/precificacao/spec.md
  - docs/faseamento/precificacao/T-PRC-000-investigacao.md
---

# P2 — Revisões consolidadas da spec `precificacao` (2026-06-12)

> `tech-lead-saas-regulado` + `advogado-saas-regulado` = **AMBOS APROVA COM
> CORREÇÕES** (0 CRÍTICO / 10 ALTO / 11 MÉDIO / 4 BAIXO). Arquitetura validada
> (motor puro D-PRC-9 + fail-closed cost-plus + recorte parcial). Todos os
> achados incorporados na spec v2 (log §10 da spec).

## 1. Tech-lead — TL-PRC-NN

**ALTOS:**
- **TL-PRC-01** — `CalculoPrecoResultado` incompleto pra replay/carimbo INV-026:
  adicionar `motor_versao` (molde INV-CAL-VERSAO-001), versão/hash das
  `FaixaAprovacaoDesconto` (config mutável → base probatória), ref do `Imposto`
  (id+versão) e ECO das entradas (km, desconto_pct, modo_montagem, parcelas).
- **TL-PRC-06** — cortesia/desconto 100% (delegado pela PPS em
  `value_objects.py:6-8`) ausente: permitir com alçada DONO sempre;
  `preco_final: Decimal ≥ 0` próprio (NÃO reusar VO `Preco > 0`);
  flag `cortesia: bool` no resultado e no pedido.
- **TL-PRC-08** — aprovação sem binding ao cálculo = reutilizável em contexto
  alterado: campo obrigatório `fingerprint_calculo` (hash canônico ADR-0029 das
  entradas+refs+pct) no pedido; consumidor só consome se fingerprint do cálculo
  vigente bater (molde fingerprint idempotência B6).
- **TL-PRC-10** — segregação `decisor_id != solicitante_id` (molde ADR-0026):
  INV-PRC-APROVACAO-INDEPENDENTE, domínio + CHECK + teste UNHAPPY.
- **TL-PRC-11** — action única `aprovar_desconto` não distingue GERENTE/DONO:
  predicate ABAC `alcada_cobre` vinculado à action (molde M3
  `authz/django_provider.py:275-313`), resource = {alcada_exigida, papel}.
- **TL-PRC-12** — RBAC de campo é padrão NOVO (zero molde no src/): choke-point
  único `filtrar_visao_margem(payload, pode_ver_margem)` em TODO serializer da
  frente; leitura de regra (expõe custo/margem-alvo) exige `configurar` ou
  `ver_margem`; papel aprovador DEVE ter `ver_margem` (seed coerente); proibição
  estende a logs e ProductAnalytics; cache (se houver) sempre pré-filtro;
  hook candidato `prc-margem-rbac-check`; teste UNHAPPY por endpoint.
- **TL-PRC-13** — vínculo multi-tabela: tabela PRÓPRIA
  `vinculo_tabela_preco_cliente` (tenant, tabela_id FK, cliente_id, vigência,
  UNIQUE parcial vigente) — ZERO retrofit de schema na PPS fechada;
  `preco_para_os` ganha param aditivo `tabela_id: UUID | None = None`
  (+ emenda ADR-0081 no ponto "tabela PADRÃO"); `cliente_id` segue ADR-0032
  (consumer `Cliente.Anonimizado` revoga vínculo). **Decisão de semântica:
  fallback POR ITEM na tabela padrão** quando tabela do cliente não tem o item
  (não conflita com anti-fallback ADR-0081 — ambas são tabelas de VENDA;
  rastreável pois `PrecoResolvido.tabela_id` aponta a tabela realmente usada);
  explícito na spec + teste nomeado.

**MÉDIOS:**
- **TL-PRC-03** — D-PRC-6 citava molde ERRADO (M7 é fail-OPEN lazy): fail-closed
  está certo, citar moldes corretos (`PrecoTabelaAusente` D-PPS-2 + ADR-0073);
  mecânica: domínio puro recebe `custo_real_disponivel: bool`; use case
  `publicar_regra` consulta o `CustoProvider` (ADR-0007).
- **TL-PRC-05** — `RegraVigenteAusente` só no endpoint `vigente` → 404; motor
  NUNCA levanta; caminho sem regra carrega `sem_regra_formacao: true` +
  semáforo INDISPONIVEL (buraco visível, "não existe chão").
- **TL-PRC-07** — bloqueio duro MANTIDO (válvula = revogar+recriar, autosserviço);
  instrumentar staleness: `custo_referencia_em` na regra + eco
  `custo_declarado_em` no resultado + item no GATE-PRC-CUSTEIO-REAL.
- **TL-PRC-09** — contexto tipado: `contexto_tipo` ENUM (ORCAMENTO|OS|AVULSO) +
  `contexto_id UUID NULL` + snapshot probatório embutido (item, refs, pct,
  fingerprint); FK real vira constraint aditiva quando #5 existir.
- **TL-PRC-14** — entrada canônica do motor é a CESTA
  (`calcular_precos(itens=[...])`): `componentes_faltantes` é incomputável
  item-a-item; evita N+1 (lição GATE-PPS-KIT-BATCH); sem cache cross-request;
  memoização por request de Imposto/Parâmetros/Faixas; `assertNumQueries` no P7.
- **TL-PRC-15** — seed faixas default: etapa no `provisionar_tenant` (ADR-0015)
  + RunPython pra tenants existentes.
- **TL-PRC-16** — contiguidade de faixas é propriedade do CONJUNTO: replace-all
  atômico no use case (valida conjunto) + exclusion como cinto.

**BAIXOS:** TL-PRC-17 (Fatia 1a lista explícita: `CustoProvider` Protocol+stub
+ contrato `PrecoPraticado`); TL-PRC-18 (conversão `Percentual`→fração nas
fórmulas + ROUND_HALF_EVEN escala 2 — determinismo bit-a-bit).

**Testes exigidos (P3/P7):** vazamento margem por endpoint não-calculadora;
fingerprint divergente → recusa; decisor==solicitante → recusa; gerente decide
alçada DONO → predicate nega; desconto 100% não estoura `Preco>0`; faixas com
buraco → `FaixasDescontoInvalidas`; determinismo cross-versão motor; cesta sem
deslocamento esperado → `componentes_faltantes`.

## 2. Advogado — ADV-PRC-NN

**ALTOS:**
- **ADV-PRC-01** — `justificativa` CRUA em WORM imborrável (anti-padrão; molde
  triplo da casa): WORM/evento só `justificativa_hash` (ADR-0029 + HMAC-tenant,
  eliminável por crypto-shredding); texto cru em tabela-par MUTÁVEL
  `JustificativaDecisaoDesconto` (soft-delete ADR-0031; AC-PRC-004-3 exige
  leitura pelo vendedor); retenção cru 5a ou pedido do titular citado; INV nova
  **INV-PRC-JUSTIFICATIVA-HASH**.
- **ADV-PRC-04** — contrato `Precificacao.PrecoPraticado` é IRREVERSÍVEL:
  `cliente_ref` padrão ADR-0032 (nunca nome/CPF/CNPJ); payload mínimo (item_id,
  cliente_ref, orcamento_ref, preco_final, desconto_pct, fechado_em);
  **`margem_realizada` FORA do evento** (deriva sob RBAC na materialização);
  base legal legítimo interesse art. 7º IX com **LIA documentada como
  pré-condição do GATE-PRC-HISTORICO-ORCAMENTOS**; linha RAT dormante já;
  perfil pricing PF/MEI entra no export art. 18 quando GATE ativar.
- **ADV-PRC-09** — retenção: 4 linhas novas na `retencao-matriz.md` (config de
  preço 5a/teto 10a CC art. 205 — NÃO herda 25a; pedido aprovação 5a/10a;
  justificativa crua 5a TTL; PrecoPraticado linha DORMANTE) + DRILL-RET-PRC-01
  + linha RAT-PRC-DESCONTO no `lgpd-rat.md`. **Textos prontos no parecer —
  aplicar no P3.**

**MÉDIOS:**
- **ADV-PRC-02** — `contexto_consumidor` SÓ UUIDs (nunca nome/CPF/CNPJ);
  se ref direta de cliente um dia → `ReferenciaPIIAnonimizavel` ADR-0032;
  GATE-PRC-NOTIFICACAO resolve contexto na entrega + margem só com `ver_margem`.
- **ADV-PRC-03** — enumerar campo a campo o hashificado por evento (tabela na
  spec): solicitante/decisor/criado_por `*_id_hash`; justificativa/motivo/
  observacoes/aviso_texto `*_hash`; **valores de Parametros/Faixas NÃO entram
  em claro nos eventos** (diff de NOMES de campos, não valores); hook candidato
  **`prc-evento-pii-hash-check`** (denylist adaptada do PEPH).
- **ADV-PRC-05** — trilha de empregado: UUID cru operacional nas tabelas
  (pseudônimo art. 12, base art. 7º V + 37); eventos só hash; retenção 5a
  mínimo/teto 10a (NÃO 25a); linha RAT-PRC-DESCONTO.
- **ADV-PRC-06** — segredo comercial além do RBAC: **INV-PRC-SEGREDO-LOG**
  (custo/margem/parâmetros nunca em log estruturado, exceção, payload de evento
  em claro, corpo 4xx/5xx — só refs); eventos Parametros/Faixas refs-only;
  filtragem `ver_margem` alcança TODOS os serializers (incl. pedidos);
  endpoint `parametros` gated por `configurar`/`ver_margem`.

**BAIXOS:**
- **ADV-PRC-07** — `preco_minimo` visível a quem tem `calcular`: MANTER
  (vendedor precisa do chão; 422 às cegas é pior) — registrar decisão consciente
  em D-PRC-4 (vazamento parcial de piso aceito; custo/margem seguem gated).
- **ADV-PRC-08** `[OAB-PRE-PROD]` — bloqueio duro: frase na spec ("bloqueio
  sempre reversível pelo tenant em autosserviço — fato probatório de alocação
  de responsabilidade no ToS") + cláusula no lote OAB pré-produção (governança
  de preço sobre parâmetros do próprio tenant; exclusão lucros cessantes sob
  cap ADR-0019/0028; ressalva CDC finalismo mitigado pra MEI/pequeno).

## 3. Decisões que as revisões CRAVARAM (sem reabrir)

1. Fail-closed no cost-plus JUSTIFICADO (assimetria com M7 é legítima: gate em
   tempo de CONFIGURAÇÃO, modo de falha = prejuízo silencioso).
2. Bloqueio duro de mínimo MANTIDO (AC-PRC-003-3; válvula autosserviço existe).
3. Vínculo cliente em tabela própria da precificacao (zero retrofit PPS) +
   fallback POR ITEM na padrão + emenda ADR-0081.
4. Entrada canônica do motor = CESTA (batch desde o contrato).
5. Justificativa: hash no WORM + cru em tabela-par mutável.
6. `PrecoPraticado` minimizado + LIA pré-condição do GATE.

## 4. Pendências de aplicação

- [x] Spec v2 incorpora TL+ADV (este commit)
- [ ] P3: emendas cross-doc (retencao-matriz 4 linhas + DRILL + lgpd-rat
  RAT-PRC-DESCONTO — textos prontos no §2) + emenda ADR-0081 (param tabela_id)
  + plan.md + tasks.md
- [ ] Lote `[OAB-PRE-PROD]`: somar cláusula ADV-PRC-08
