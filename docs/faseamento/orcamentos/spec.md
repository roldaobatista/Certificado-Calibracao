---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: orcamentos
tipo: spec
versao: 1
relacionados:
  - docs/faseamento/orcamentos/T-ORC-000-investigacao.md
  - docs/dominios/comercial/modulos/orcamentos/prd.md
  - docs/dominios/comercial/modulos/orcamentos/modelo-de-dominio.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# Spec v1 — frente `orcamentos` (1ª ponta de receita, Wave A)

> Recorte sobre o PRD `docs/dominios/comercial/modulos/orcamentos/prd.md` (US-ORC-001..010,
> stable) + Família 0. Frente #5 da cadeia. Greenfield do módulo (T-ORC-000 §1), mas a OUTRA
> ponta (consumer `Orcamento.Aprovado` + `abrir_os_via_orcamento`) JÁ existe na OS.
> **v1 (2026-06-13):** insumo para P2 (tech-lead + advogado) + batch Roldão (D-aberta-1).

## 1. Tese e fronteira

`orcamentos` é o **documento comercial que vira OS**: carrinho de itens do catálogo → cálculo
(preço+desconto+imposto+comissão) → envio com link de aprovação → aprovação → **análise crítica
cl. 7.1 ISO 17025** (quando há calibração) → publica `Orcamento.Aprovado` → a OS (consumer já
pronto) cria 1 OS com N atividades. É o **Passo 1 da Saga 1** (ADR-0034).

**O que NÃO é (fronteiras):**
- **Não faz catálogo nem preço** — consome `produtos_pecas_servicos` (catálogo) + `precificacao`
  (`calcular_precos`). A-ORC-001/002 já fechados.
- **Não emite NF** (fiscal) **nem cobra** (contas-receber via `PaymentGatewayProvider` — US-ORC-010
  diferido; o consumer é de contas-receber, futuro).
- **Não cria a OS** — só PUBLICA `Orcamento.Aprovado` (envelope exato); a OS já consome (ADR-0023/0051).
- **Preço não retroage** — snapshot imutável via `PrecoResolvido` carimbado (INV-026 / INV-ORC-PRECO-001).
- **Não é a tela** — UI/PDF diferidos (frente de telas / GATE-ORC-PDF). O backend serve a lógica + dados.

## 2. Recorte núcleo vs diferido (por US do PRD)

| US | Núcleo Wave A | Diferido (GATE/Wave B) |
|----|---------------|------------------------|
| US-ORC-001 criar < 5 min | criar/editar/adicionar item; snapshot `PrecoResolvido` por item (via `calcular_precos`); imposto+comissão; rejeita tabela expirada (ADR-0030) | tela carrinho (telas) |
| US-ORC-002 aprovar 1-clique | transição aprovar (interno + endpoint público token) + registra ip_hash/user_agent/aceite WORM + publica `Orcamento.Aprovado` (envelope §6) idempotente | PDF (GATE-ORC-PDF) · TELA HTML pública (telas) |
| US-ORC-003 versionar V1/V2 | `VersaoOrcamento` Padrão B (V1 ao enviar; snapshot) | comparação V1/V2/V3 (Wave B) |
| US-ORC-004 desconto→comissão | `calcular_precos` devolve comissão prevista + semáforo (server-side) | bloqueio escalado desconto>X% (Wave B; alçadas já em precificacao) |
| US-ORC-005 templates | `Template` (Padrão C) + gate selo RBC perfil A (hook) | tela templates (telas) |
| US-ORC-006 tracking leitura | — | `Orcamento.LinkAberto` + EventoLeitura (Wave B) |
| US-ORC-007 conversão OS c/ atividades | publica envelope com `itens[{tipo_atividade_alvo→tipo, sequencia, valor_unitario}]`; OS já cria | `origem_item_id` na OS (GATE-ORC-ORIGEM-ITEM) |
| US-ORC-008 bloquear cancel convertido | 409 se estado=convertido (terminal) | — |
| US-ORC-009 análise crítica cl. 7.1 | via PORTAS metrologia (ADR-0073), perfil-aware (A fail-closed / B fail-open / C warning / D off); evento WORM | `padrao_disponivel` real (GATE-ORC-PADRAO; stub fail-open) |
| US-ORC-010 cobrança gateway | — | consumer de `contas-receber` (futuro) |

## 3. Decisões cravadas (D-ORC-1..14)

- **D-ORC-1 — Snapshot de preço = `PrecoResolvido`, NÃO VO `Preco` novo (T-ORC-000 §2):** o item do
  orçamento carimba `PrecoResolvido` (item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia,
  origem_preco) — fonte probatória completa (INV-026). O `Preco(valor_centavos, moeda, vigencia,
  fonte_tabela_id)` do PRD é **reconciliado** para isso (emenda PRD/modelo no P8). VO `Dinheiro`/`Desconto`/
  `CondicoesPagamento` do modelo permanecem.
- **D-ORC-2 — Path aninhado comercial:** `src/domain/comercial/orcamentos/` +
  `src/application/comercial/orcamentos/` + `src/infrastructure/orcamentos/` (infra flat, `app_label
  orcamentos`; molde `clientes`). *Revisão tech-lead P2.*
- **D-ORC-3 — Máquina de estados (Padrão A) com `aprovado_pendente_os`:** `rascunho→enviado→aprovado→
  convertido`; `enviado→recusado|expirado`; `rascunho→cancelado`. Aprovação publica evento e entra em
  `aprovado_pendente_os`; vira `convertido` ao confirmar criação da OS (idempotência). `convertido` =
  terminal (INV-ORC-CONVERTIDO-TERMINAL). Transições proibidas: aprovado→rascunho; convertido→qualquer.
- **D-ORC-4 — Cliente via `ReferenciaPIIAnonimizavel` (ADR-0032):** `cliente_atual_id` (FK SET_NULL) +
  `cliente_referencia_hash` (HMAC NOT NULL) + `cliente_key_id`. Consumer `Cliente.Anonimizado` revoga/
  bloqueia. Cliente obrigatório e ativo/não-bloqueado para criar (US-CLI-001).
- **D-ORC-5 — Análise crítica cl. 7.1 via PORTAS, perfil-aware (T-ORC-000 §3, ADR-0073/0067):** o use case
  `aprovar_orcamento` chama, por item `tipo_atividade_alvo=calibracao`, as portas `escopos_cmc.query_service.
  cobre` (M6) + `procedimentos.query_service` (M7) + `rt_competencia_cobre` (real) + `padrao_disponivel`
  (stub fail-open, GATE-ORC-PADRAO). `tenant_perfil_e(["A","B","C"])` gate; **A=fail-closed** (reprova →
  422 + `Orcamento.AnaliseCriticaReprovada` WORM), **B=fail-open lazy** (unknown → aprova + ressalva
  `Orcamento.AnaliseCriticaComRessalva`), **C=parcial/warning**, **D=desabilitado**. Perfil indeterminado →
  fail-closed. NÃO usar os predicates ABAC NO-OP (`cmc_cobre`/`procedimento_vigente_para` deprecados).
- **D-ORC-6 — `Orcamento.Aprovado` com ENVELOPE EXATO da OS (T-ORC-000 §1):** payload `{orcamento_id,
  tenant_id, cliente_id, cliente_referencia_hash, cliente_key_id, equipamento_id, equipamento_recebimento_id?,
  analise_critica_id?, analise_critica_snapshot_hash, regra_decisao_acordada, valor_total, abertura_at,
  criada_por_user_id?, itens[{tipo, sequencia, valor_unitario, requer_recebimento}]}`. `outbox=True`,
  `idempotency_key=orcamento_id` (ADR-0033). O consumer OS já deduplicapor `causation_id+acao`.
- **D-ORC-7 — Endpoint público de aprovação (US-ORC-002):** `POST /v1/public/orcamentos/{token}/aprovar`
  SEM auth (token opaco = autorização), rate-limit (30 req/min/IP + alerta `aprovacao-suspeita` >5/min/IP),
  registra `nome_aprovador`+`email_aprovador`+`ip_hash`+`user_agent`+`lgpd_aceite` em `Aprovacao` WORM
  (INV-001 / INV-ORC-APROVACAO-WORM). PII via apontador (congelado). **TELA HTML pública = frente de telas.**
- **D-ORC-8 — `VersaoOrcamento` Padrão B (imutável):** V1 criada ao enviar; `snapshot` jsonb (itens+
  condições+totais). V2/V3 + comparação = Wave B (US-ORC-003). Revogação V1 = `revogado_em`+motivo.
- **D-ORC-9 — PDF DIFERIDO (GATE-ORC-PDF):** WeasyPrint disponível (molde `services_etiqueta`). PDF cliente
  (sem margem/custo/comissão) e interno (com margem RBAC) entram quando a frente de telas/exports rodar.
- **D-ORC-10 — Cálculo via `calcular_precos` server-side (T-ORC-000 §2):** monta `CalcularPrecosInput`
  (cesta + cliente_id→tabela + desconto + km + parcelas), resolve preço/imposto/comissão/semáforo.
  Margem/custo NUNCA no PDF/visão cliente (choke-point perfil server-side, molde precificacao).
- **D-ORC-11 — Conversão idempotente; rastro item↔atividade por `sequencia` (T-ORC-000 §2):**
  `AtividadeSnapshot.origem_item_id` não existe na OS — Wave A usa `sequencia` (1:1); campo aditivo =
  GATE-ORC-ORIGEM-ITEM. Itens sem `tipo_atividade_alvo` (deslocamento/taxa) = linhas comerciais sem atividade.
- **D-ORC-12 — REST molde precificacao:** idempotência 2 camadas (Idempotency-Key em escrita), ACTION_MAP
  authz `orcamento.*`, `publicar_evento(outbox=True)`, perfil/visão server-side.
- **D-ORC-13 — Templates com gate selo RBC por perfil (ADR-0067 / US-ORC-005-2):** salvar template com
  `selo_rbc=true` em perfil≠A → hook bloqueia (matriz feature×perfil). Linha matriz (P8).
- **D-ORC-14 — Saga: estado + idempotência agora; saga-manager DLQ diferido (T-ORC-000 §4):** Wave A entrega
  `aprovado_pendente_os` + idempotência (não duplica OS); a auto-reabertura via `dead_letter_events`
  (US-ORC-002 AC-3) = GATE-ORC-SAGA-DLQ. Tabela saga `comercial_saga_orcamento_os` = diferida.

## 4. Modelo (domínio)

**Path:** `src/domain/comercial/orcamentos/` (D-ORC-2).

**Agregado raiz `Orcamento`:** `id`, `tenant_id` (NOT NULL), `cliente_atual_id`/`cliente_referencia_hash`/
`cliente_key_id` (D-ORC-4), `numero` (sequencial por tenant — molde SerieDocumento/sequence), `estado`
(enum máquina D-ORC-3), `validade_ate` (`JanelaVigencia` ADR-0030), `total_bruto/descontos/impostos/liquido`,
`comissao_prevista`, `template_id?`, `tabela_preco_id?`, `condicoes_pagamento` (VO), `observacoes?`,
`responsavel_id?`, `chamado_origem_id?`, `criado_em/por`.

**Entidades filhas:**
- `VersaoOrcamento` (`orcamento_id`, `numero_versao`, `snapshot` jsonb, `revogado_em?`; Padrão B imutável).
- `ItemOrcamento` (`versao_id`, `catalogo_item_id`, `preco_resolvido` carimbado (D-ORC-1), `descricao_snapshot`,
  `quantidade`, `desconto_valor`, `total`, `tipo_atividade_alvo?` enum, `sequencia`).
- `LinkPublico` (`orcamento_id`, `token` URL-safe random, `expira_em`, `revogado_em?`; 1 ativo por orçamento).
- `Aprovacao` (`orcamento_id`, `versao_id`, `aprovado_em`, `aprovado_por`, `canal`, `ip_hash`, `user_agent`,
  `nome_aprovador`/`email_aprovador` (anonimizável), `lgpd_aceite`; WORM Padrão B).

**Entidade standalone:** `Template` (`tenant_id`, `nome`, `tipo`, `itens_default` jsonb, `condicoes_default`,
`selo_rbc` bool; Padrão C soft-delete).

**VOs:** `Dinheiro`, `Desconto`, `CondicoesPagamento` (modelo) + `PrecoResolvido` (carimbo, reuso pps) +
`JanelaVigencia` (validade).

**Erros:** `ClienteBloqueado` (422), `TabelaPrecoExpirada` (422), `AnaliseCriticaReprovada` (422),
`EstadoInvalido`/`TransicaoProibida` (409), `OrcamentoConvertido` (409), `TokenInvalidoOuExpirado` (404/410),
`PerfilIndeterminado` (422 fail-closed).

## 5. Invariantes candidatas (P7 crava em REGRAS + hook)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-ORC-PRECO-001 | snapshot `PrecoResolvido` imutável pós-criação do item (não retroage — INV-026); trigger/teste |
| INV-ORC-CL71-001 | perfil A/B/C com item calibração obriga análise crítica antes de aprovar; A fail-closed; domínio + teste UNHAPPY por perfil |
| INV-ORC-CONVERTIDO-TERMINAL | estado convertido não transiciona; CHECK/trigger + 409 |
| INV-ORC-APROVACAO-WORM | `Aprovacao` INSERT-only (ip_hash+aceite); trigger PG anti-mutação (INV-001) |
| INV-ORC-LINK-TOKEN | 1 link ativo por orçamento (partial unique WHERE revogado IS NULL); token opaco |
| INV-ORC-EXP-001 (já em invariantes-futuras) | job expiração idempotente por orcamento_id + timezone tenant |
| INV-ORC-APROVADO-ENVELOPE | `Orcamento.Aprovado` carrega envelope EXATO esperado pela OS (D-ORC-6); teste de contrato |
| INV-TENANT-001/002/003 · INV-001 · INV-016 (herdadas) | tenant_id+RLS; WORM aprovação; WCAG tela pública (frente telas) |

## 6. Portas, eventos e seams

- **Consome:** `calcular_precos` (precificacao); `PrecoResolvido`/`preco_para_os` (pps); `ImpostoRepository`
  (config); portas análise crítica `escopos_cmc`/`procedimentos`/`padroes` query_service + `rt_competencia_cobre`;
  `tenant_perfil_e` (authz); `Cliente` (FK + ReferenciaPIIAnonimizavel); idempotência + eventos + perfil server-side.
- **Expõe/publica (catálogo; outbox):**

| Evento | Quando | Payload-chave | Consumer |
|--------|--------|---------------|----------|
| `Orcamento.Enviado` | enviar | orcamento_id, cliente_ref, canal, valor | crm |
| `Orcamento.Aprovado` | aprovar | **envelope exato §3 D-ORC-6** | operacao/os (cria OS), financeiro, crm |
| `Orcamento.Recusado` | recusar | orcamento_id, motivo? | crm |
| `Orcamento.Expirado` | job | orcamento_id | crm |
| `Orcamento.Convertido` | OS criada | orcamento_id, os_id | crm |
| `Orcamento.AnaliseCriticaReprovada`/`ComRessalva` (NOVOS — criar) | análise crítica | orcamento_id, itens_avaliados[], perfil_no_evento, analise_critica_id | qualidade/dashboard |

## 7. REST (núcleo)

`OrcamentoViewSet` (autenticado): criar / adicionar-item / enviar (gera token + V1 + evento) / aprovar
(interno: análise crítica + evento) / recusar / cancelar / retrieve / list. `OrcamentoPublicoView`
(sem auth): GET `{token}` (serve dados não-sensíveis) + POST `{token}/aprovar` (rate-limit + WORM).
`TemplateViewSet`: CRUD (gate selo RBC perfil). Ações authz `orcamento.*`: `criar`, `editar`, `enviar`,
`aprovar`, `recusar`, `cancelar`, `ver`, `gerir_template`, `ver_margem` (comissão/margem só com isto).
Idempotency-Key em escrita; público com `idempotency_key=orcamento_id` na aprovação.

## 8. Non-goals (além dos do PRD §5)

PDF (GATE-ORC-PDF) · telas (frente telas) · versionamento V2/V3 + comparação + tracking + aprovação
escalada (Wave B) · assinatura eletrônica · multi-moeda · NF (fiscal) · cobrança/gateway (contas-receber) ·
catálogo (pps) · régua de preço (precificacao) · saga-manager DLQ auto-reabertura (GATE-ORC-SAGA-DLQ) ·
`origem_item_id` na OS (GATE-ORC-ORIGEM-ITEM) · `padrao_disponivel` real (GATE-ORC-PADRAO).

## 9. GATEs rastreados

GATE-ORC-PDF (PDF cliente/interno) · GATE-ORC-TELA-PUBLICA (tela HTML de aprovação, WCAG INV-016) ·
GATE-ORC-PADRAO (`padrao_disponivel` real — porta metrologia/padroes) · GATE-ORC-SAGA-DLQ (auto-reabertura
`aprovado_pendente_os` via dead_letter) · GATE-ORC-ORIGEM-ITEM (campo aditivo na OS) · GATE-CAL-CMC-PREDICATE
+ GATE-CAL-PROC-VIGENTE-PREDICATE (herdados — análise crítica vira fail-closed p/ 1º tenant A externo) ·
**GATE-LGPD-RAT-CONSOLIDACAO** (CONGELADO — RAT aprovação digital · retenção orçamento · DPIA tela pública;
apontador-PII na spec; `[OAB-PRE-PROD]` base legal aceite público) · GATE-ORC-US010 (cobrança quando contas-receber existir).

## 10. Log de revisões (P2 — 2026-06-13) — spec PAUSADA em v1; v2 após frente `os-multi-equipamento`

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES** (TL-ORC-01..11). Detalhe: `reviews-consolidado.md`.
- ✅ `advogado-saas-regulado` — **APROVA COM CORREÇÕES** (ADV-ORC-01..10; congelamento respeitado).
- ✅ batch Roldão: **R-ORC-1** equipamento no orçamento · **R-ORC-2** aprovação lógica-agora/PDF-depois ·
  **R-ORC-3 (estrutural)** N equipamentos por orçamento E OS + itens compartilhados.
- ⛔ **DEPENDÊNCIA DURA descoberta:** R-ORC-3 exige retrofit da OS (1→N equipamentos). **Frente
  `os-multi-equipamento` (ADR + retrofit cirúrgico) deve vir ANTES.** Esta spec sobe para v2 (envelope
  por item + correções TL/ADV) só depois — senão nasce com contrato errado (`reviews-consolidado.md`).
