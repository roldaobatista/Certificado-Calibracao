---
owner: agente-ia
revisado-em: 2026-06-11
proximo-review: 2026-09-11
status: stable
diataxis: explanation
audiencia: [agente, auditor]
frente: precificacao
tipo: investigacao-p0
relacionados:
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/dominios/comercial/modulos/precificacao/prd.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - docs/faseamento/produtos-pecas-servicos/matriz-reconciliacao.md
---

# T-PRC-000 — Investigação regra #0 — frente `precificacao` (#3 da cadeia de preço)

> **Pra quê:** ler o estado REAL (código + docs + decisões) antes de escrever spec.
> Molde: `docs/faseamento/produtos-pecas-servicos/T-PPS-000-investigacao.md`.
> Ordem cravada: `plano-dependencia-sistema.md` — #1 configuracoes-sistema ✅ →
> #2 produtos-pecas-servicos ✅ (FECHADA 2026-06-11) → **#3 precificacao (parcial,
> stub custo)** → #4 colaboradores → #5 orcamentos.

## 1. Estado real do código — GREENFIELD TOTAL

- **Zero código:** não existe `src/{domain,application,infrastructure}/precificacao/`
  nem nenhum use case/porta/modelo de margem/desconto/custo no `src/`. Grep por
  `precificacao|margem|desconto|markup|custo_medio` confirma.
- **Delegação explícita já escrita:** `src/domain/produtos_pecas_servicos/value_objects.py:7-8`
  — "cortesia/desconto 100% é responsabilidade da frente `precificacao`, não do catálogo".
- **Preço da OS avulsa HOJE é client-supplied:** `src/infrastructure/ordens_servico/views.py:507`
  (`valor_unitario_snapshot` vem do JSON da request; única validação = `> 0`).
  GATE-PPS-WIREIN-OS (bloqueante pré-1º tenant externo) declara o conserto:
  resolver via porta `preco_para_os` fail-closed. **Condição prévia:**
  GATE-PPS-KIT-BATCH (método em lote `item_id IN (...)` antes do caminho quente).
- **Consumidores de valor existentes (seams a jusante):**
  `ordens_servico/models.py:99-110` (`OS.valor_total`), `fiscal/models.py:50`
  (`amount_centavos` = input do caller, seam declarado "orçamentos diferido"),
  `os/entities.py:68` (`AtividadeSnapshot.valor_unitario_snapshot`).

## 2. Seams prontos (consumir, não recriar)

| Peça | Onde | Uso pela frente |
|------|------|-----------------|
| Porta `preco_para_os` + contrato `PrecoResolvido` (7 campos probatórios, fail-closed 422, kit linha própria) | `infrastructure/produtos_pecas_servicos/query_service.py:46` + `domain/.../entities.py:160` | FONTE do preço de venda vigente; precificacao NÃO refaz resolução — compõe sobre ela (desconto/margem/aprovação) |
| `TabelaPreco`/`LinhaTabelaPreco` WORM + `eh_padrao` UNIQUE parcial (schema já N tabelas) | PPS Fatia 1b (migrations 0001..0004) | multi-tabela por segmento/cliente entra AQUI sem migration de schema |
| `Imposto`/`RegimeTributario` vigentes + `Aliquota` VO | `configuracoes_sistema` (frente #1) | simulação fiscal do preço sugerido (% imposto na fórmula) |
| VO `JanelaVigencia` (ADR-0030) + soft-delete 3 padrões (ADR-0031) + WORM Padrão B molde Imposto | `configuracoes_sistema` + PPS | regra/tabela de preço versionada imutável |
| Moldes de porta cross-módulo: `CoberturaEscopoPort` (Protocol + stub lazy + injeção via view) e `FiscalProvider` | `application/metrologia/calibracao/configurar_calibracao.py:46` / `domain/fiscal/portas.py:19` | molde do `CustoProvider` (stub Wave A) e da porta que `orcamentos` consumirá |
| Idempotência 2 camadas + ACTION_MAP authz + eventos canônicos + perfil server-side + hooks `pps-evento-pii-hash` (payload hashificado ADR-0029) | transversal F-B/F-C + PPS P7 | REST da frente nasce no molde |
| Path raiz achatada `src/{domain,application,infrastructure}/<modulo>/` | PPS (D-PPS-1) | mesmo padrão (módulo comercial, não-metrologia → NÃO aninha) |

## 3. PRD e escopo — PRD EXISTE (draft), recorte Wave A é PARCIAL

- **PRD:** `docs/dominios/comercial/modulos/precificacao/prd.md` (draft) — 8 US:
  US-PRC-001 formação de preço por item (cost-plus / margem-alvo / fixo),
  002 preço mínimo, 003 desconto com aprovação, 004 tabela por região/segmento/
  contrato, 005 simulações (comissão/imposto/deslocamento/parcelamento),
  006 alerta margem baixa, 007/008 histórico de preço praticado.
  + `modelo-de-dominio.md` (7 agregados: RegraFormacaoPreco, TabelaPreco*,
  PedidoAprovacaoDesconto, CalculoPreco read-model, HistoricoPrecoPraticado WORM,
  ParametrosTenant, FaixaAprovacaoDesconto) + `glossario.md` (37 termos + fórmulas
  canônicas de preço mínimo/sugerido/margem líquida).
  *`TabelaPreco` do modelo-de-domínio foi PROMOVIDA e construída na frente #2 —
  reconciliar no P1 (não duplicar agregado).
- **Recorte Wave A cravado** (`plano-dependencia-sistema.md` §4 + gap #6):
  PARCIAL = **preço-fixo + margem-alvo manual**; consome custo via **STUB**
  (`custo_por_item` com fallback configurável); **cost-plus + preço mínimo
  DIFERIDOS** até `custeio-real` (N7) existir; **invariante obrigatória que
  RECUSA publicar regra cost-plus enquanto o provider de custo for stub**
  (não vender abaixo do custo silenciosamente).
- **Conflito de faseamento (emendar no P8, molde PPS):** `faseamento-modulos.md`
  põe precificacao em Wave B, mas PRD de `orcamentos` (stable, Wave A) declara
  **A-ORC-002: precificacao é GATE Wave A**. Alinhar pelo PRD — mesma errata
  aplicada à PPS em 2026-06-11 (linha 95 do faseamento).
- **Dor real (discovery):** "tabela de preço desatualizada → margem errada";
  vendedor esquece deslocamento/hora-técnica/peças/ART; "cliente pede desconto
  e vendedor não sabe até onde pode ir"; dono sem visão de margem por
  serviço/cliente (Dor #12, JTBD-080).

## 4. ADRs e INVs que tocam a frente

| Ref | O que diz pra cá |
|-----|------------------|
| ADR-0081 (aceita) | duas fontes de preço: LISTA imutável × VENDA vigente fail-closed; `PrecoResolvido` probatório; precificacao compõe SOBRE a venda, nunca fallback à lista |
| INV-026 | preço não retroage — orçamento/OS/NF preservam snapshot da emissão |
| INV-PPS-* (9) | catálogo/tabela WORM + sem sobreposição + fail-closed + positivo — a frente HERDA esses contratos |
| ADR-0030/0031 | vigência canônica + soft-delete por padrão de entidade |
| ADR-0013 (proposta) | **FRONTEIRA: é pricing DO SAAS (billing-saas Wave B)** — não confundir com preço dos serviços do tenant (esta frente). Nenhuma dependência |
| ADR-0067 | perfil regulatório server-side — se houver feature de preço perfil-aware, predicate `tenant_perfil_e`; matriz-feature-perfil a emendar |
| ADR-0077 | incerteza POR PONTO já existe no M4 — habilita (futuro) preço de calibração por ponto; HOJE nenhum PRD pede — diferir explícito |
| Discovery comissões (8 formas) | comissão é módulo PRÓPRIO (a jusante); a frente só precisa garantir que o preço carimbado carrega o que comissões precisará (bruto, desconto, % aplicado) |

## 5. Recorte núcleo proposto (startável HOJE, zero dependência inexistente)

**NÚCLEO Wave A (P1 detalha):**
1. `RegraFormacaoPreco` versionada (tipos Wave A: PRECO_FIXO, MARGEM_ALVO) —
   WORM molde Imposto; tipo COST_PLUS existe no enum mas **publicação bloqueada
   sob stub de custo** (invariante candidata INV-PRC-COSTPLUS-STUB, fail-closed).
2. Porta `CustoProvider` (Protocol) + `StubCustoProvider` declarado (retorna
   `custo_indisponivel` explícito — nunca 0 silencioso) — contrato é peça desta
   frente; implementação real vem do `custeio-real` (N7, Wave B).
3. Desconto com alçada: `FaixaAprovacaoDesconto` por tenant + `PedidoAprovacaoDesconto`
   (one-shot, WORM) — destrava US-ORC-004 do consumidor.
4. Cálculo/simulação `calcular_preco` (read-model puro): preço de venda vigente
   (via porta PPS) + desconto proposto + % imposto vigente (configuracoes-sistema)
   → margem ESTIMADA com ressalva explícita "custo stub".
5. Multi-tabela por segmento/cliente (schema PPS já suporta N): regra de matching
   mínima — decisão de recorte no P1/P2.
6. `HistoricoPrecoPraticado` (WORM, alimentado na aprovação do orçamento) —
   avaliar diferir pra quando `orcamentos` existir (quem publica o evento é o
   consumidor; candidato a GATE).

**DIFERIDO (GATE-PRC-*):** cost-plus + preço mínimo real (GATE-PRC-CUSTEIO-REAL);
preço por ponto de calibração (sem PRD — explícito non-goal); simulação de
comissão completa (módulo comissoes); pricing dinâmico (V2); UI (frente de telas).

## 6. Decisões abertas (classificadas por dono)

**PRODUTO — Roldão (rodada batch única no planejamento, com recomendação):**
- D-aberta-1: composição do preço de serviço — monolítico vs decomposição
  obrigatória (deslocamento/hora-técnica/ART como itens do catálogo vs campos
  da regra). *Impacta a dor real "esqueci o deslocamento".*
- D-aberta-2: alçadas default de desconto (ex.: ≤10% vendedor / ≤20% gerente /
  acima = dono) — valores default por tenant.
- D-aberta-3: margem estimada visível ao VENDEDOR no ato (com ressalva stub)
  ou só ao dono em relatório?

**TÉCNICA/ARQUITETURA — subagentes (P2 tech-lead + advogado se LGPD):**
- contrato exato do `CustoProvider` + semântica do stub (fail-closed explícito);
- camada da invariante anti-cost-plus-sob-stub (domínio vs use case — provável
  domínio, molde `metodo_exige_validacao_pendente` M7);
- matching de multi-tabela (precedência cliente > segmento > padrão; empate);
- versionamento de `RegraFormacaoPreco` (molde Imposto completo vs Padrão B já
  provado na PPS);
- reconciliar agregado `TabelaPreco` do PRD com o JÁ construído na frente #2
  (não duplicar; PRD draft precisa emenda).

## 7. Próximos passos do ritual

P1 spec (recorte núcleo §5 sobre PRD draft; reconciliar TabelaPreco) →
P2 revisões `tech-lead` + `advogado` (LGPD: histórico de preço praticado por
cliente é dado comercial sensível? retenção?) → rodada batch Roldão (D-abertas
de produto, com recomendação) → P3 plan/tasks (fatias 1a domínio / 1b schema /
2 use cases+REST / 3 P7) → ... → P9 auditores roteados (INV-RITUAL-003).
