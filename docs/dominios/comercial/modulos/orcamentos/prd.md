---
owner: roldao
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: stable
modulo: orcamentos
dominio: comercial
diataxis: explanation
audiencia: agente
relacionados:
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0050-gateway-pagamento-pix-recorrente.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0066-cmc-procedimento-predicate-fail-open-lazy.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - docs/adr/0082-os-multi-equipamento-equipamento-por-atividade.md
  - docs/adr/0083-orcamento-preco-resolvido-reconcilia-vo-preco-prd.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - REGRAS-INEGOCIAVEIS.md
historico:
  - 2026-05-27 — saneamento Onda 3 Batch B4 pré-Wave A: declara perfil ADR-0067, US-ORC-009 análise crítica cl. 7.1 ISO 17025, VO `Preco` canônico substitui snapshot vago (INV-026 retrofit), AC binários GIVEN-WHEN-THEN com ID `AC-ORC-NNN-N`, deps ADR 0007/0023/0024/0030/0031/0032/0033/0034/0050/0051/0066/0067, persona inline, vocabulário Wave A, matriz feature × perfil, métricas inline, status `draft` → `stable`.
  - 2026-06-15 — emenda pontual P8 (Onda 2f): reconcilia VO `Preco` → `PrecoResolvido` (ADR-0083); não toca UX/telas.
---

<!-- prd-ux-states: skip -- emenda pontual P8 (ADR-0083) reconcilia o snapshot de preco; a secao 'UX dos estados nao-felizes' e debito proprio do modulo (telas diferidas em Wave A — orcamentos ainda nao tem telas) rastreado a parte em GATE-ORC-PRD-UX-STATES, nao introduzido por esta emenda -->

# PRD — Módulo Orçamentos

## 1. O que este módulo é

Criação, versionamento, envio digital, aprovação e conversão de **orçamentos comerciais em OS** (com N `AtividadeDaOS` — ADR-0023 + ADR-0051). Estilo "carrinho" com itens do catálogo, cálculo automático de impostos/comissão, envio via link WhatsApp/e-mail com tracking de leitura, e — quando há item de tipo `calibracao` — **análise crítica de pedido cl. 7.1 ISO 17025** prévia obrigatória/parcial conforme perfil regulatório do tenant (ADR-0067).

## 2. Por que existe

JTBD-041 (mandar proposta profissional em < 5 min) + JTBD-020 (não copiar info 3 vezes: chamado → orçamento → OS) + JTBD-075 (vendedor ver impacto do desconto na própria comissão antes de fechar) + obrigação regulatória de **análise crítica de pedido cl. 7.1** para tenants A/B/C que ofertam calibração. Custo do status quo: Word + e-mail + impressão + caneta = 30-60 min/orçamento + perda de versão + zero tracking + nenhuma análise crítica documentada (NC certa em auditoria CGCRE). Gap defensável #8 (CRM + calibração integrados).

## 3. Personas (inline)

- **P-COM-02 Vendedor** (dominante) — fecha proposta em até 5 min do contato; precisa preço/desconto/comissão na mesma tela; opera no smartphone fora do escritório.
- **P-COM-03 Cliente final** (aprovador) — abre link, vê PDF/web, aprova com 1 clique sem cadastrar senha.
- **P-COM-05 Dono / Gestor comercial** (configurador) — define templates, regras de desconto e aprovação interna escalada.
- **P-OP-01 RT / Gestor de qualidade (perfil A/B/C)** — recebe alerta quando item `tipo=calibracao` cai em grandeza sem CMC/procedimento vigente ou RT competente (análise crítica cl. 7.1).

Detalhe operacional em `personas.md` deste módulo + `../../personas.md` (domínio).

## 4. Escopo (Wave A)

**Wave A (MVP-1 — dogfooding Balanças Solution):**
- Criação de orçamento (header + itens + descontos + impostos + condições).
- Templates pré-configurados pelo tenant.
- **Análise crítica de pedido cl. 7.1 ISO 17025** quando há item `tipo_atividade_alvo=calibracao` (US-ORC-009).
- Conversão em **1 OS com N `AtividadeDaOS`** (ADR-0023 + ADR-0051) ao aprovar.
- PDF exportável + link público com aprovação 1-clique.
- Snapshot de preço do item = `PrecoResolvido` (reuso `produtos-pecas-servicos`) + valor em `Dinheiro`; vigência comercial no agregado `Orcamento.validade` (`JanelaVigencia`). **O VO `Preco` proposto foi reconciliado para `PrecoResolvido` — ver ADR-0083** (substitui INV-026 vago).

**Wave B (expansão):**
- Versionamento + comparação V1/V2/V3.
- Tracking de leitura (cliente abriu o link).
- Assinatura eletrônica simples (não-ICP — V2 considera ICP-Br).
- Aprovação interna escalada (se desconto > X%, pede aprovação dono).

## 5. Non-goals

- **Assinatura digital ICP-Brasil** (Wave B → V2).
- **Negociação multi-rodada com tracking de chat** (Wave B — só comentário simples na Wave A).
- **Orçamento sem cliente cadastrado** — cliente deve existir (US-CLI-001 pré-requisito).
- **Catálogo de serviços/produtos** — pertence ao módulo `suporte-plataforma/catalogo` (GATE Wave A A-ORC-001: módulo `catalogo` é bloqueante; orçamento só consome).
- **Pricing dinâmico por margem** — Wave B.
- **Tabela de preço por cliente** — GATE Wave A A-ORC-002: depende do módulo `comercial/precificacao` (Wave A); orçamento consome via `tabela_preco_id`.
- **Orçamento internacional / multi-moeda** — fora do MVP (ADR-0039 cliente exterior só atinge cadastro).
- **Geração de NFS-e** — pertence ao `financeiro` (após OS concluída).
- **Re-precificação retroativa após aprovação** — proibida pela imutabilidade do `PrecoResolvido` carimbado + `VersaoOrcamento` WORM (ADR-0083 / INV-ORC-PRECO-001).
- **Portal cliente full** (M-ORC-003) — pertence ao módulo `comercial/portal-cliente` (Wave A); orçamento publica link.
- **Cobrança recorrente do orçamento** — quem cobra é `contas-receber` via porta `PaymentGatewayProvider` (ADR-0050).

## 6. Perfil regulatório (ADR-0067)

Este módulo participa da matriz feature × perfil (`docs/conformidade/comum/matriz-feature-perfil.md`):

| Comportamento | A — Acreditado RBC | B — Rastreável | C — Em preparação | D — Comercial puro |
|---|---|---|---|---|
| **Análise crítica cl. 7.1** (US-ORC-009) quando item `tipo=calibracao` | ✅ OBRIGATÓRIO (predicates `cmc_cobre` + `procedimento_vigente_para` + `rt_competencia_cobre` + `padrao_disponivel` — fail-closed) | ✅ OBRIGATÓRIO (mesmos predicates, com aviso quando CMC não declarada — fail-open por ADR-0066 lazy) | 🟡 OBRIGATÓRIO_PARCIAL (predicates rodam em modo warning — gate trilha D→A) | ❌ DESABILITADO (orçamento de calibração comercial pura não passa por cl. 7.1) |
| **Selo RBC / referência ILAC-MRA no orçamento** | ✅ permitido | ❌ proibido (hook bloqueia template com selo CGCRE) | ❌ proibido | ❌ proibido |
| **Análise crítica registrada como evento WORM** com `perfil_no_evento` snapshot | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO (registro mesmo em warning) | ⚪ OPCIONAL |

Predicate canônico invocado: `tenant_perfil_e(["A", "B", "C"])` para ligar US-ORC-009. Default fail-closed: se perfil indeterminado, sistema **rejeita** aprovação de orçamento com item de calibração.

## 7. User Stories

### US-ORC-001 — Criar orçamento em < 5 min (JTBD-041)

**Como** vendedor, **quero** abrir tela tipo carrinho, escolher cliente, adicionar serviços do catálogo, **para** mandar proposta antes do cliente esquecer.

- **AC-ORC-001-1**: GIVEN cliente selecionado e item do catálogo escolhido com `tabela_preco_id` vigente, WHEN o vendedor adiciona o item, THEN o sistema carimba `PrecoResolvido` (via `calcular_precos`/`preco_para_os`) + valor em `Dinheiro` no item + preenche alíquota fiscal + comissão prevista, e o `PrecoResolvido` carimbado fica imutável na linha (não retroage — ADR-0083).
- **AC-ORC-001-2**: GIVEN orçamento com ao menos 1 item e total > 0, WHEN o vendedor clica "enviar", THEN o sistema gera PDF + link público com token expirável e envia por WhatsApp/e-mail conforme `canal_preferido` do cliente (ADR-0032 `ReferenciaPIIAnonimizavel` aplica em e-mail/telefone).
- **AC-ORC-001-3**: GIVEN tentativa de salvar orçamento com tabela de preço expirada na `data_referencia` (`PrecoResolvido` sem linha vigente), WHEN salva, THEN sistema rejeita com mensagem "tabela de preço expirada — atualize antes de salvar" (ADR-0030 vigência canônica; ADR-0081 fail-closed).
- **INV:** INV-ORC-PRECO-001 (`PrecoResolvido` imutável após criação — ADR-0083), INV-TENANT-001.

### US-ORC-002 — Cliente aprova orçamento em 1 clique

**Como** cliente final, **quero** abrir link, ver PDF/visualização web, clicar "Aprovar", **para** não ter que imprimir/assinar.

- **AC-ORC-002-1**: GIVEN link público com token válido e orçamento estado `enviado`, WHEN cliente abre URL, THEN sistema serve visualização web sem exigir login (token = autorização) e PDF download (validade do orçamento como `JanelaVigencia` — ADR-0030).
- **AC-ORC-002-2**: GIVEN cliente clica "Aprovar", WHEN confirma, THEN sistema registra IP + user-agent + carimbo de tempo + aceite LGPD (RAT-06) e emite evento `Orcamento.Aprovado` com `idempotency_key=orcamento_id` (ADR-0033 idempotência consumer).
- **AC-ORC-002-3**: GIVEN evento `Orcamento.Aprovado` consumido pelo módulo `operacao/os`, WHEN consumer roda, THEN cria 1 OS rascunho com N `AtividadeDaOS` (ADR-0051 §1). Compensação saga: se OS-creation falha, evento entra em `dead_letter_events` (ADR-0033/0034) e orçamento volta a `aprovado_pendente_os` (não-terminal).
- **INV:** INV-001 (WORM aceite), ADR-0033, ADR-0034.

### US-ORC-003 — Versionar e comparar (Wave B)

**Como** vendedor, **quero** revisar orçamento (V2) sem perder V1, **para** mostrar ao cliente o que mudou.

- **AC-ORC-003-1**: GIVEN orçamento V1 já enviado, WHEN vendedor edita, THEN sistema cria V2 mantendo V1 imutável (padrão B soft-delete ADR-0031 — `revogado_em` em V1 ao enviar V2).
- **AC-ORC-003-2**: GIVEN V1 e V2 existem, WHEN vendedor abre comparação, THEN sistema mostra itens adicionados/removidos/alterados lado a lado.
- **AC-ORC-003-3**: GIVEN V2 enviada, WHEN cliente aprova, THEN sistema marca V1 como `revogado_em=now()` com `motivo_revogacao="substituida_por_v2"` e V2 vira `aprovada`; só V2 pode disparar `Orcamento.Aprovado`.

### US-ORC-004 — Ver impacto de desconto na comissão (JTBD-075)

**Como** vendedor, **quero** que ao digitar desconto X% apareça quanto perco de comissão, **para** decidir conscientemente.

- **AC-ORC-004-1**: GIVEN orçamento aberto, WHEN vendedor altera campo `desconto_percentual`, THEN sistema recalcula `comissao_prevista_centavos` em tempo real (< 200ms p95) e exibe diff vs comissão base.
- **AC-ORC-004-2**: GIVEN regra do dono `desconto_max_sem_aprovacao_percentual=10`, WHEN vendedor digita `desconto=15`, THEN sistema bloqueia salvamento com mensagem "desconto > 10% exige aprovação interna" (Wave B abre fluxo escalado).

### US-ORC-005 — Templates por tipo de serviço

**Como** dono, **quero** configurar templates (calibração padrão, manutenção, instalação), **para** vendedor não recriar tudo toda vez.

- **AC-ORC-005-1**: GIVEN dono na tela "Templates", WHEN cria template "Calibração balança 1kg" com itens pré-marcados (`tipo_atividade_alvo=calibracao` + grandeza=massa), THEN sistema salva e exibe em dropdown ao criar orçamento.
- **AC-ORC-005-2**: GIVEN tenant `perfil != "A"`, WHEN dono tenta salvar template com `selo_rbc=true`, THEN hook bloqueia: "selo RBC restrito a tenant perfil A" (matriz feature × perfil ADR-0067).

### US-ORC-006 — Tracking de leitura (Wave B)

**Como** vendedor, **quero** ver "cliente abriu o link há 2h, não respondeu", **para** fazer follow-up no momento certo.

- **AC-ORC-006-1**: GIVEN link aberto pelo cliente, WHEN página carrega, THEN sistema registra evento `Orcamento.LinkAberto` com `aberto_em`, `ip_hash`, `user_agent_canonico` (Wave B).

### US-ORC-007 — Conversão de orçamento aprovado em OS com atividades (ADR-0023 + ADR-0051)

**Como** sistema, **quero** que orçamento aprovado gere 1 OS com N `AtividadeDaOS` mapeadas 1:1 dos itens com `tipo_atividade_alvo` setado, **para** suportar caso combinado (manutenção + calibração).

- **AC-ORC-007-1**: GIVEN orçamento aprovado com 2 itens (1 `tipo_atividade_alvo=manutencao` + 1 `tipo_atividade_alvo=calibracao`), WHEN consumer `operacao/os` processa `Orcamento.Aprovado`, THEN cria 1 OS com 2 `AtividadeDaOS` (1 por tipo) com FK `atividade.origem_item_id` apontando pro item do orçamento.
- **AC-ORC-007-2**: GIVEN itens sem `tipo_atividade_alvo` (deslocamento, taxa), WHEN OS é criada, THEN viram linhas comerciais na OS mas **não** geram `AtividadeDaOS`.
- **INV:** ADR-0023, ADR-0051.

### US-ORC-008 — Bloquear cancelamento de orçamento convertido

**Como** sistema, **quero** impedir cancelamento de orçamento já convertido em OS, **para** preservar rastreabilidade (A-ORC-003).

- **AC-ORC-008-1**: GIVEN orçamento estado `convertido`, WHEN comando `cancelar` é tentado, THEN sistema retorna 409 com mensagem "orçamento convertido — cancele a OS resultante pelo fluxo próprio".
- **AC-ORC-008-2**: GIVEN OS resultante é cancelada (US-OS-007), WHEN evento `OS.Cancelada` chega, THEN orçamento permanece `convertido` (terminal — não reabre).

### US-ORC-009 — Análise crítica de pedido cl. 7.1 ISO 17025 quando há item de calibração (achado L3 #2 — saneamento 2026-05-27)

**Como** sistema (perfil A/B/C), **quero** rodar análise crítica formal antes de aprovar orçamento com item `tipo_atividade_alvo=calibracao`, **para** atender ISO 17025 cl. 7.1 + evitar NC CGCRE + evitar gerar OS impossível de executar.

- **AC-ORC-009-1**: GIVEN orçamento com `>=1` item `tipo_atividade_alvo=calibracao` e tenant com `tenant_perfil_e(["A","B","C"])`, WHEN comando `aprovar_orcamento` é disparado, THEN sistema executa análise crítica avaliando 4 predicates por item: `cmc_cobre(tenant_id, grandeza, faixa)` + `procedimento_vigente_para(tenant_id, grandeza, equipamento)` + `rt_competencia_cobre(tenant_id, grandeza)` + `padrao_disponivel(tenant_id, grandeza, faixa, prazo)`.
- **AC-ORC-009-2**: GIVEN perfil A, WHEN qualquer um dos 4 predicates retorna `False`, THEN sistema rejeita aprovação com 422 + lista os predicates reprovados + grava evento `Orcamento.AnaliseCriticaReprovada` (WORM, `perfil_no_evento='A'`).
- **AC-ORC-009-3**: GIVEN perfil B, WHEN `cmc_cobre` retorna `unknown` (ADR-0066 fail-open lazy — escopos-cmc ainda não plugado), THEN sistema aprova com warning + grava evento `Orcamento.AnaliseCriticaComRessalva` (fica visível em dashboard).
- **AC-ORC-009-4**: GIVEN perfil C, WHEN qualquer predicate reprova, THEN sistema aprova com warning + grava ressalva (modo gate trilha D→A — Wave A bloqueia em promoção C→B).
- **AC-ORC-009-5**: GIVEN perfil D, WHEN item `tipo_atividade_alvo=calibracao` está presente, THEN sistema aprova sem rodar predicates (cl. 7.1 desabilitada para D — matriz feature × perfil).
- **AC-ORC-009-6**: GIVEN análise crítica concluída (qualquer veredito), WHEN sistema grava evento, THEN payload contém: `tenant_id`, `orcamento_id`, `itens_avaliados[]` (item_id, grandeza, faixa, veredito_4_predicates), `perfil_no_evento` (snapshot ADR-0067 §3), `analise_critica_id`, `timestamp_utc`.
- **INV:** INV-ORC-CL71-001 (perfil A/B/C com calibração obriga análise crítica), ADR-0066, ADR-0067.

### US-ORC-010 — Aprovação de orçamento dispara cobrança via `PaymentGatewayProvider`

**Como** sistema, **quero** que aprovação de orçamento que disparou OS gere cobrança preliminar pelo gateway configurado, **para** parar de orquestrar cobrança em planilha.

- **AC-ORC-010-1**: GIVEN orçamento aprovado com `condicoes_pagamento.modo ∈ {boleto, pix_recorrente, cartao_recorrente}` (ADR-0050), WHEN evento `Orcamento.Aprovado` é consumido por `financeiro/contas-receber`, THEN consumer chama `PaymentGatewayProvider.criar_cobranca(...)` com `idempotency_key=orcamento_id`.
- **AC-ORC-010-2**: GIVEN gateway retorna erro temporário, WHEN consumer reenfileira, THEN respeita backoff exponencial 5min→30min→4h→24h e finalmente vai pra `dead_letter_events` (ADR-0033).
- **INV:** ADR-0050, ADR-0033.

## 8. Métricas (inline)

**Primárias:**
- Tempo médio criação de orçamento (do clicar "novo" até "enviar"): **p50 < 5 min**, **p95 < 12 min**.
- Taxa de conversão `orçamento enviado → OS criada`: **> 40%**.
- Taxa de orçamentos com `tipo_atividade_alvo=calibracao` reprovados por análise crítica cl. 7.1 (US-ORC-009): **medida**, sem meta — sinaliza saúde regulatória do tenant; alto = lab ofertando fora do escopo.

Detalhe completo em `metricas.md`.

## 9. NFR

- **Performance:** criação salva p95 < 1s; geração PDF < 3s; análise crítica US-ORC-009 com 4 predicates p95 < 500ms.
- **Disponibilidade:** 99,5%.
- **LGPD:** aprovação digital registra consentimento (RAT-06). E-mail/telefone do cliente trafegam via `ReferenciaPIIAnonimizavel` (ADR-0032).
- **Imutabilidade:** versão aprovada é snapshot via `PrecoResolvido` carimbado + `VersaoOrcamento` WORM (INV-ORC-PRECO-001 substitui INV-026; reconciliação ADR-0083).
- **Acessibilidade:** WCAG 2.1 AA na tela pública de aprovação (link cliente).

## 10. Glossário

- **`PrecoResolvido`** — snapshot de preço canônico no item do orçamento (reuso `produtos-pecas-servicos`): `(item_id, item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia, origem_preco)`. Imutável (item frozen + `VersaoOrcamento` WORM). **Reconcilia o VO `Preco` originalmente proposto neste PRD — ver ADR-0083** (o `Preco` não foi criado). Valor monetário usa o VO `Dinheiro`; vigência comercial = `Orcamento.validade` (`JanelaVigencia`, ADR-0030).
- **`tipo_atividade_alvo`** — enum em `ItemOrcamento`: `calibracao | manutencao | instalacao | verificacao_inmetro | vistoria | OUTRO`. Itens com este campo viram `AtividadeDaOS` (ADR-0051).
- **Análise crítica cl. 7.1** — avaliação ISO 17025 antes de aceitar contrato/orçamento de calibração: lab tem CMC declarado? procedimento vigente? RT competente? padrão disponível no prazo?
- **`perfil_no_evento`** — snapshot do perfil regulatório do tenant no momento do evento WORM (ADR-0067 §3).

Demais termos em `glossario.md` deste módulo.

## 11. Matriz feature × perfil

Ver `docs/conformidade/comum/matriz-feature-perfil.md` linhas de "Análise crítica cl. 7.1", "Template certificado com selo CGCRE + RBC" e "Snapshot RT competência por grandeza".

## 12. Como este PRD evolui

- US nova → próximo `US-ORC-NNN` livre (não renumerar existentes).
- Mudança em AC já implementado → ADR + novo teste.
- Mudança de matriz feature × perfil → editar `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator.sh` revalida.
