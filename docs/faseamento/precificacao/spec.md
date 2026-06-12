---
owner: agente-ia
revisado-em: 2026-06-12
proximo-review: 2026-09-12
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: precificacao
tipo: spec
relacionados:
  - docs/faseamento/precificacao/T-PRC-000-investigacao.md
  - docs/dominios/comercial/modulos/precificacao/prd.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - docs/faseamento/plano-dependencia-sistema.md
---

# Spec — frente `precificacao` (núcleo Wave A PARCIAL, stub custo)

> Recorte sobre o PRD `docs/dominios/comercial/modulos/precificacao/prd.md`
> (US-PRC-001..008). Frente #3 da cadeia de preço. Greenfield (T-PRC-000 §1).
> **Decisões Roldão 2026-06-12 (rodada batch P0):** (1) DOIS modos de montagem
> completos com escolha na hora; (2) alçadas de desconto 3 níveis 10%/20%/dono;
> (3) semáforo de margem pro vendedor, números completos só pra papéis autorizados.

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
| US-PRC-002 mínimo + sugerido | fórmulas canônicas do glossário; mínimo/sugerido ESTIMADOS quando regra tem custo manual (origem `CUSTO_MANUAL` explícita); determinismo AC-002-3 | mínimo com custo REAL (custeio-real N7) |
| US-PRC-003 impacto do desconto | motor puro `calcular_preco` (<200ms p95): preço novo + semáforo + alçada violada + bloqueio mínimo | UI tempo-real (frente de telas) |
| US-PRC-004 aprovação por faixa | `FaixaAprovacaoDesconto` (default 0-10 livre / 10-20 gerente / 20+ dono) + `PedidoAprovacaoDesconto` one-shot WORM + eventos | notificação push/e-mail (ADR-0060 reservada) → GATE-PRC-NOTIFICACAO |
| US-PRC-005 multi-tabela | matching mínimo: **cliente-específico > padrão** (schema PPS já N tabelas; vínculo `TabelaPreco↔cliente` nasce aqui) | precedência contrato/segmento/região (módulos inexistentes) → GATE-PRC-TABELA-CONTRATO |
| US-PRC-006 simulações | deslocamento (R$/km × km, parâmetro tenant) + imposto (alíquota vigente `configuracoes_sistema`, SIMULAÇÃO estimada D-PRC-10) + parcelamento (taxa tenant) + comissão PREVISTA (% parâmetro tenant, sem módulo comissoes) | comissão real (módulo `comissoes`) → GATE-PRC-COMISSAO-REAL; carimbo no orçamento (consumidor #5) |
| US-PRC-007 alerta margem | motor expõe `abaixo_margem_minima` no resultado | alerta ativo + dashboard exigem `orcamentos` produzindo → GATE-PRC-ALERTA-GESTOR |
| US-PRC-008 histórico praticado | só o CONTRATO do evento de entrada (definido aqui, anti-retrabalho) | tabela WORM + timeline exigem orçamentos fechados → GATE-PRC-HISTORICO-ORCAMENTOS |

## 3. Decisões cravadas (D-PRC-1..10)

- **D-PRC-1 — Path raiz achatada** `src/{domain,application,infrastructure}/precificacao/`
  (módulo comercial; molde D-PPS-1, não aninha — ADR-0072 é só metrologia).
- **D-PRC-2 — Dois modos de montagem completos (decisão Roldão):**
  `COMPONENTES_CHECKLIST` (deslocamento/hora-técnica/ART são ITENS do catálogo;
  `PerfilComposicaoPreco` declara componentes esperados por item-serviço; motor
  emite `componentes_faltantes` se orçamento não os incluir) e `FECHADO_COM_AVISO`
  (1 valor; motor emite `aviso_composicao` configurável). **Escolha é POR
  ORÇAMENTO, na hora, pelo vendedor** (consumidor #5 envia `modo_montagem`);
  precificacao entrega modelo + validação + avisos nos dois modos.
- **D-PRC-3 — Alçadas default 10/20/dono (decisão Roldão):** seed por tenant na
  primeira configuração (0-10% `LIVRE`, 10-20% `GERENTE`, >20% `DONO`); faixas
  editáveis por tenant (contíguas, sem buraco/sobreposição — CHECK + domínio).
- **D-PRC-4 — Semáforo RBAC server-side (decisão Roldão):** resultado do motor
  tem DOIS níveis de visão: `semaforo_margem` (VERDE ≥ alvo / AMARELO entre piso
  e alvo / VERMELHO < piso ou prejuízo / INDISPONIVEL sem custo) pra qualquer
  papel com `precificacao.calcular`; campos `margem_estimada_percentual` +
  `custo_estimado` SÓ pra papel com `precificacao.ver_margem` — **filtragem no
  serializer server-side, nunca no front** (INV-PRC-MARGEM-RBAC).
- **D-PRC-5 — `CustoProvider` (Protocol) + stub fail-closed:** stub retorna
  `CustoIndisponivel` EXPLÍCITO (nunca 0 silencioso — INV-PRC-CUSTO-EXPLICITO).
  Custo manual declarado na própria regra (`custo_manual_declarado > 0`, origem
  `CUSTO_MANUAL`) é a fonte Wave A pra MARGEM_ALVO; provider real chega com
  `custeio-real` (N7) sem mudar contrato.
- **D-PRC-6 — INV-PRC-COSTPLUS-STUB:** publicar regra `COST_PLUS` exige provider
  de custo real; sob stub → 422 `CustoRealIndisponivel` (camada domínio,
  molde `metodo_exige_validacao_pendente` M7 — fail-closed, não lazy).
- **D-PRC-7 — `RegraFormacaoPreco` versionada WORM molde Imposto:** imutável
  pós-publicação + one-shot `revogado_em` + block-DELETE + não-sobreposição de
  vigência por `(tenant, item)` (exclusion btree_gist molde PPS 0004); correção
  = revogar+recriar (D-PPS-8).
- **D-PRC-8 — Preço mínimo Wave A é ESTIMADO e bloqueio é DURO quando calculável:**
  com custo manual → mínimo pela fórmula canônica; violação = 422
  `PrecoMinimoViolado` (PROIBIÇÃO, não aprovável — AC-PRC-003-3). Sem custo →
  mínimo `INDISPONIVEL`, governam só as alçadas de desconto. Resultado carrega
  `origem_custo` SEMPRE (ressalva probatória).
- **D-PRC-9 — Motor puro, sem persistência:** `calcular_preco` é função
  determinística (mesmas entradas → mesmo resultado, AC-PRC-002-3); saída
  `CalculoPrecoResultado` (frozen) com refs probatórias (regra_versao, linha_tabela_id
  via `PrecoResolvido` embutido, parametros_versao, origem_custo) — consumidor
  carimba. Única persistência da frente: regras, faixas, perfis, parâmetros,
  pedidos de aprovação (config + workflow), TODOS WORM ou soft-delete ADR-0031.
- **D-PRC-10 — Simulação fiscal usa `Imposto` vigente da frente #1** (alíquota
  efetiva estimada por regime; PRD §5 já declara "cálculo fiscal exato" non-goal
  — porta fiscal NÃO entra no motor).

## 4. Modelo (domínio)

**Entidades:** `RegraFormacaoPreco` (tenant, item_id, modo PRECO_FIXO|MARGEM_ALVO|COST_PLUS,
preco_fixo?, custo_manual_declarado?, margem_alvo_pct?, margem_piso_pct?,
vigência ADR-0030, versão densa, WORM) · `PerfilComposicaoPreco` (tenant,
item_servico_id, componentes_esperados: tuple[item_id], aviso_texto?, mutável
`deletado_em` ADR-0031) · `FaixaAprovacaoDesconto` (tenant, faixas contíguas
[pct_de, pct_ate, alcada LIVRE|GERENTE|DONO]) · `PedidoAprovacaoDesconto`
(tenant, contexto_consumidor [orcamento_ref opaca], pct_solicitado, alcada_exigida,
estado SOLICITADO→APROVADO|NEGADO one-shot, decisor, justificativa, WORM) ·
`ParametrosPrecificacaoTenant` (custo_km, taxa_parcelamento_mensal,
pct_comissao_prevista, margem_alvo_default, margem_piso_default; versionado).

**VOs:** `Percentual` (0..100, escala 2) · `CalculoPrecoResultado` (frozen:
preco_base PrecoResolvido, preco_final, desconto_pct, semaforo, margem_estimada?,
custo_estimado?, preco_minimo?, origem_custo, componentes_faltantes,
avisos, alcada_exigida, refs probatórias) · fórmulas canônicas do glossário
(`preco_minimo = (custo+desloc)/(1−imp−com−piso)`; sugerido idem com alvo;
denominador ≤ 0 → erro `ParametrosInviaveis` 422, nunca preço negativo).

**Erros:** `CustoRealIndisponivel`, `PrecoMinimoViolado`, `ParametrosInviaveis`,
`FaixasDescontoInvalidas`, `RegraVigenteAusente` (fail-open? NÃO — sem regra,
motor opera só com preço de venda + alçadas; regra é OPCIONAL por item, decisão
de recorte: tabela de venda é obrigatória [ADR-0081], regra de formação é
camada opcional de governança).

## 5. Invariantes candidatas (P7 crava em REGRAS)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-PRC-COSTPLUS-STUB | domínio fail-closed + teste + hook candidato `prc-costplus-stub-check` |
| INV-PRC-REGRA-IMUTAVEL | WORM Padrão B (triggers molde Imposto/PPS) |
| INV-PRC-REGRA-SEM-SOBREPOSICAO | exclusion btree_gist por (tenant, item) WHERE revogado IS NULL |
| INV-PRC-APROVACAO-ONE-SHOT | UPDATE escopado em estado SOLICITADO + trigger one-shot |
| INV-PRC-MINIMO-BLOQUEIO | 422 duro no motor quando mínimo calculável; NUNCA aprovável |
| INV-PRC-CUSTO-EXPLICITO | stub nunca retorna 0; ausência = `CustoIndisponivel` tipado |
| INV-PRC-MARGEM-RBAC | serializer server-side por permissão `precificacao.ver_margem` + teste UNHAPPY |
| INV-PRC-FAIXAS-CONTIGUAS | domínio + CHECK (0 a 100, sem buraco/sobreposição) |
| INV-026 (herdada) | motor não persiste; consumidor carimba snapshot |

## 6. Portas e seams

- **Consome:** `preco_para_os`/`PrecoResolvido` (PPS — preço de venda vigente
  fail-closed); `Imposto`/`RegimeTributario` vigentes (frente #1); authz
  ACTION_MAP + idempotência + eventos canônicos + perfil server-side (F-B/F-C).
- **Expõe:** `calcular_preco` (porta de aplicação — `orcamentos` #5 e wire-in
  OS consumirão); `CustoProvider` Protocol (implementação real = custeio-real N7);
  contrato do evento `Precificacao.PrecoPraticado` (input futuro do histórico
  US-PRC-008 — só contrato agora).
- **Eventos WORM (cadeia, payload hashificado ADR-0029):** `Precificacao.RegraPublicada`,
  `RegraRevogada`, `AprovacaoSolicitada`, `AprovacaoDecidida`, `ParametrosAlterados`,
  `PerfilComposicaoAlterado`, `FaixasDescontoAlteradas`.

## 7. REST (núcleo)

`RegraFormacaoPrecoViewSet`: publicar / revogar / retrieve / `vigente?item_id&em=` ·
`CalculoPrecoView`: POST `calcular` (simulação stateless; SEM Idempotency-Key —
leitura computada, molde `consultar` fiscal) · `AprovacaoDescontoViewSet`:
solicitar / decidir (one-shot) / pendentes · `ConfiguracaoPrecificacaoViewSet`:
faixas-desconto / perfil-composicao / parametros. Ações authz `precificacao.*`
(`configurar`, `calcular`, `ver_margem`, `aprovar_desconto`) + seed migration.

## 8. Non-goals (além dos do PRD §5)

UI/dashboard (frente de telas) · notificação push/e-mail (ADR-0060) · histórico
praticado materializado (GATE) · preço por ponto de calibração (sem PRD; ADR-0077
habilita futuro) · integração comissões real · multi-tabela por contrato/região ·
juros compostos exatos de gateway (taxa simples informativa do tenant).

## 9. GATEs rastreados

GATE-PRC-CUSTEIO-REAL (cost-plus + mínimo real; fecha INV-PRC-COSTPLUS-STUB
virando go) · GATE-PRC-HISTORICO-ORCAMENTOS (US-PRC-008 materializa quando #5
produzir) · GATE-PRC-ALERTA-GESTOR (US-PRC-007 ativo) · GATE-PRC-NOTIFICACAO
(ADR-0060) · GATE-PRC-COMISSAO-REAL · GATE-PRC-TABELA-CONTRATO (precedência
completa AC-005-4) · **GATE-PPS-WIREIN-OS continua da frente #2** (wire-in do
preço na OS consome ESTA frente + KIT-BATCH; bloqueante pré-1º tenant externo).

## 10. Status de revisões (P2)

- [ ] tech-lead-saas-regulado — pendente
- [ ] advogado-saas-regulado (LGPD: pedido de aprovação carrega contexto de
  cliente? eventos hashificados; retenção) — pendente
- Decisões Roldão incorporadas: D-PRC-2 (dois modos), D-PRC-3 (alçadas),
  D-PRC-4 (semáforo RBAC).
