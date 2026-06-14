---
owner: agente-ia
revisado-em: 2026-06-14
proximo-review: 2026-09-14
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: orcamentos
tipo: spec
versao: 2
relacionados:
  - docs/faseamento/orcamentos/T-ORC-000-investigacao.md
  - docs/faseamento/orcamentos/reviews-consolidado.md
  - docs/dominios/comercial/modulos/orcamentos/prd.md
  - docs/dominios/comercial/modulos/orcamentos/modelo-de-dominio.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0082-os-multi-equipamento.md
---

# Spec v2 — frente `orcamentos` (1ª ponta de receita, Wave A)

> Recorte sobre o PRD `docs/dominios/comercial/modulos/orcamentos/prd.md` (US-ORC-001..010,
> stable) + Família 0. Frente #5 da cadeia. Greenfield do módulo (T-ORC-000 §1), mas a OUTRA
> ponta (consumer `Orcamento.Aprovado` + `abrir_os_via_orcamento`) JÁ existe na OS.
> **v2 (2026-06-14):** desbloqueada — a dependência dura `os-multi-equipamento` FECHOU (ADR-0082).
> Incorpora correções P2 (tech-lead TL-ORC-01..11 + advogado ADV-ORC-01..10), o envelope
> `Orcamento.Aprovado` POR ITEM (equipamento na atividade, não no header) e os seams reais
> verificados no código (ver §11). Pronta para P3 (plan + tasks).

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
- **D-ORC-5 — Análise crítica cl. 7.1 via PORTAS, perfil-aware (T-ORC-000 §3, ADR-0073/0067; emendado
  TL-ORC-02/10):** o use case `aprovar_orcamento` avalia, por item de calibração (com equipamento
  identificado — R-ORC-1), a viabilidade técnica usando **grandeza/faixa/unidade do EQUIPAMENTO do item**:
  `escopos_cmc.query_service.cobre(tenant_id, grandeza, faixa_min, faixa_max, unidade, data)→(bool,str)` (M6)
  + `procedimentos_calibracao.query_service.cobre_procedimento(...)→(bool, dict|None)` (M7; `vigente_em`).
  **`rt_competencia_cobre` SAI da análise do orçamento (TL-ORC-02):** não há executor designado na fase
  comercial; competência de RT é da atribuição da OS (eventual variante "existe ALGUM RT competente no tenant"
  é Wave B). **`padrao_disponivel` NÃO é consultado** (porta inexistente — verificado §11): **GATE-ORC-PADRAO**
  (perfil A registra ressalva forte explícita, nunca silêncio — TL-ORC-10). Gate de perfil via
  `tenant_perfil_e(["A","B","C"])` (`authz/perfil_tenant_helper`): **A=fail-closed** (reprova → 422 +
  `Orcamento.AnaliseCriticaReprovada` WORM), **B=fail-open lazy** (unknown → aprova + ressalva
  `Orcamento.AnaliseCriticaComRessalva`), **C=parcial/warning**, **D=desabilitado**. Perfil indeterminado →
  fail-closed. NÃO usar os predicates ABAC NO-OP (`cmc_cobre`/`procedimento_vigente_para` deprecados).
  **Ressalva de padrão (consultor-rbc C4):** texto verbatim em constante de domínio
  `TEXTO_RESSALVA_PADRAO_INDISPONIVEL` (cita grandeza/faixa + "o RT deve confirmar disponibilidade do padrão
  de referência antes de agendar a calibração" + ref. cl. 7.1.1-b; `severidade=media`,
  `acao_obrigatoria=confirmacao_rt_antes_agendamento`) — registrada só em perfil A; B/C/D não geram.
  **Diferenciação C×B (C7):** C = `com_ressalva` `severidade=baixa` (log interno, sem confirmação do cliente);
  B = `com_ressalva` `severidade=media` (ressalva apresentada e confirmada pelo cliente — D-ORC-7/C2).
- **D-ORC-6 — `Orcamento.Aprovado` com ENVELOPE EXATO da OS, equipamento POR ITEM (ADR-0082; verificado §11):**
  header `{orcamento_id, tenant_id, cliente_id, cliente_referencia_hash, cliente_key_id, equipamento_id=null
  (header é fallback legado v1 — orçamento v2 NÃO usa), equipamento_recebimento_id?, analise_critica_id?,
  analise_critica_snapshot_hash, regra_decisao_acordada, valor_total, abertura_at, criada_por_user_id?}` +
  `itens[{tipo, sequencia, valor_unitario, requer_recebimento, equipamento_id}]`. **Item COM `equipamento_id`
  (calibração) → vira `AtividadeDaOS` daquele equipamento; item SEM `equipamento_id` (deslocamento/taxa) → vira
  `ItemComercialOS` na OS (D-OSME-3, `tipo=OUTRO`).** `tipo` da atividade segue a tabela de tradução D-ORC-16.
  Publicação via `audit.event_helpers.publicar_evento(acao="orcamento.aprovado", outbox=True,
  causation_id=orcamento_id)` — **ação lowercase `orcamento.*` (TL-ORC CRIT-1): eventos com `outbox=True`
  exigem slug minúsculo em `ACOES_CANONICAS` (`CHECK bus_outbox_acao_enum_semantico`), molde `os.aberta`.
  Criar bloco `ACOES_ORCAMENTOS` em `audit/acoes_canonicas.py` + migration que emenda o CHECK (Fatia 1b).**
  TL-ORC-04: dedup do outbox por `(causation_id, acao)` UNIQUE; o consumer OS deduplica por `event_id`.
  Contrato testado (INV-ORC-APROVADO-ENVELOPE).
- **D-ORC-7 — Endpoint público de aprovação (US-ORC-002; emendado consultor-rbc C2/C3):** `POST
  /v1/public/orcamentos/{token}/aprovar` SEM auth (token opaco = autorização), rate-limit (30 req/min/IP +
  alerta `aprovacao-suspeita` >5/min/IP), registra `nome_aprovador_hash`+`email_aprovador_hash`+`ip_hash`+
  `user_agent`+aceite rico (`versao_termo`+`texto_hash`) em `Aprovacao` WORM (INV-001 / INV-ORC-APROVACAO-WORM).
  **cl. 7.1.1-d (resolver diferença pedido×proposta): quando a análise crítica retorna `com_ressalva`, o
  `GET {token}` DEVOLVE as ressalvas (dado não-sensível, allowlist) e o `POST {token}/aprovar` EXIGE
  confirmação explícita (`ressalvas_confirmadas: bool` no payload) — sem confirmação → 422; a `Aprovacao` WORM
  grava `ressalvas_aceitas` (prova do consentido). Lógica backend-only — a TELA bonita é diferida.** PII via
  apontador (congelado). **TELA HTML pública = frente de telas.**
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
  (US-ORC-002 AC-3) = GATE-ORC-SAGA-DLQ. Tabela saga `comercial_saga_orcamento_os` = diferida. **Fechamento
  `aprovado_pendente_os→convertido` (TL-ORC-03): a OS já publica `OS.Aberta` no bus (frente os-multi-equipamento
  confirmou INT-01 — `os.aberta` cruza o bus via `MAPA_TIPO_EVENTO_OS_PARA_ACAO_BUS`); orcamentos ganha um
  consumer `handle_os_aberta` que casa `orcamento_id`/`os_origem` e transiciona p/ `convertido` (idempotente).**

### Decisões adicionadas no P2 (correções tech-lead/advogado — v2)

- **D-ORC-15 — Entidade `AnaliseCriticaOrcamento` WORM (TL-ORC-11; emendado consultor-rbc C1/C5/C6):** a análise
  crítica gera o `analise_critica_id` + `analise_critica_snapshot_hash` que o envelope exige. Padrão B imutável:
  `id, tenant_id, orcamento_id, versao_id, perfil_no_evento (A/B/C/D snapshot), veredito (aprovada/reprovada/
  com_ressalva/desabilitada), norma_referencia ("ISO/IEC 17025:2017 cl. 7.1.1" — C6), itens_avaliados jsonb,
  snapshot_hash (canonicalização ADR-0029, molde `append_evento_calibracao`), avaliada_em (server-side),
  avaliada_por`. **`avaliada_por` (C5):** aprovação interna = `user_id` do aprovador; aprovação pública =
  `"SISTEMA/AUTO"` + `aprovacao_id` (referência cruzada — cl. 7.5.1-b). **`itens_avaliados[n]` (C1 — registro
  probatório cl. 7.1.1-a, NÃO só booleano):** `{equipamento_id, grandeza, faixa_min, faixa_max, unidade,
  cobre_cmc: bool, cmc_codigo_ref?, procedimento_ok: bool, procedimento_id?, procedimento_codigo?
  (ex: "POP-CAL-0042 rev.3"), procedimento_versao?, ressalvas[]}` — o `dict` que `cobre_procedimento` já
  retorna (`ProcedimentoSnapshot`) alimenta esses campos. Trigger anti-mutação; `snapshot_hash` no envelope
  prova o que foi avaliado.
- **D-ORC-16 — Tabela de tradução `tipo_atividade_alvo` → `TipoAtividade` (TL-ORC-05):** o enum do orçamento
  (comercial) ≠ enum da OS (`TipoAtividade`: `calibracao`/`manutencao_corretiva`/`manutencao_preventiva`/
  `instalacao`/`verificacao_inmetro`/`vistoria`, FECHADO — INV-OS-ATIV-003). Mapa cravado:
  `calibracao→calibracao`, `manutencao→manutencao_corretiva` (default), `instalacao→instalacao`,
  `verificacao→verificacao_inmetro`, `vistoria→vistoria`. **Itens comerciais (deslocamento/taxa) NÃO têm
  `tipo_atividade_alvo`** (viram `ItemComercialOS`, sem tipo de atividade). NÃO existe `OUTRO` no alvo de atividade.
- **D-ORC-17 — PII do aprovador: HMAC Wave A + GATE-ORC-KMS-APROVADOR (ADV-ORC-05b vs realidade §11):** a
  cifragem KMS-tenant que permitiria EXIBIR "quem aprovou" **não existe no código** (só HMAC stub Wave A —
  `calibracao/lgpd.py`). Wave A: `Aprovacao` grava `nome_aprovador_hash`/`email_aprovador_hash` (HMAC) +
  `lgpd_aceite` rico (`versao_termo`+`texto_hash` — ADV-ORC-04), NÃO texto em claro. A **exibição** do nome
  do aprovador ao tenant fica **DIFERIDA** ao `GATE-ORC-KMS-APROVADOR` (encrypt/decrypt boto3 KMS-MRK, junto
  do GATE-CAL-KMS-MRK). `ip_hash` + `user_agent` gravados (forense). Item a confirmar com advogado no review do plan.
- **D-ORC-18 — Numeração densa por tenant, advisory lock (TL-ORC-08; molde ADR-0080):** orçamento é doc
  comercial — cliente espera sequencial limpo (sem buracos). Reusar motor `SerieDocumento`
  (`configuracoes_sistema`): `reservar_numero` + `confirmar_numero(tenant_id, reserva_id)` dentro do
  `transaction.atomic` da criação. Regime gap-less (não o de buracos-aceitos da OS).
- **D-ORC-19 — Endpoint público: token resolve tenant server-side (TL-ORC-07 + ADV-ORC-08a):** o `LinkPublico`
  não recebe `X-Tenant-ID` (galinha-ovo). Token = `secrets.token_urlsafe(32)` (≥128 bits, ADV-ORC-08a);
  lookup `token → (tenant_id, orcamento_id)` resolvido SEM RLS (tabela de índice de token ou função
  `SECURITY DEFINER` escopada), então o resto roda em `run_in_tenant_context`. Expiração checada no GET **e**
  no POST. Rate-limit molde `services_ratelimit` (30 req/min/IP + alerta `aprovacao-suspeita` >5/min/IP).
  Cross-tenant e pentest pré-tenant-pago (`[SEC-PRE-PROD]`).

## 4. Modelo (domínio)

**Path:** `src/domain/comercial/orcamentos/` (D-ORC-2).

**Agregado raiz `Orcamento`:** `id`, `tenant_id` (NOT NULL), `cliente_atual_id`/`cliente_referencia_hash`/
`cliente_key_id` (D-ORC-4), `numero` (sequencial por tenant — molde SerieDocumento/sequence), `estado`
(enum máquina D-ORC-3), `validade_ate` (`JanelaVigencia` ADR-0030), `total_bruto/descontos/impostos/liquido`,
`comissao_prevista`, `template_id?`, `tabela_preco_id?`, `condicoes_pagamento` (VO), `observacoes?`,
`responsavel_id?`, `chamado_origem_id?`, `criado_em/por`.

**Entidades filhas:**
- `VersaoOrcamento` (`orcamento_id`, `numero_versao`, `snapshot` jsonb, `revogado_em?`; Padrão B imutável).
- `ItemOrcamento` (`versao_id`, `catalogo_item_id`, `equipamento_id?` (UUID|null — R-ORC-1; calibração tem,
  item comercial não), `preco_resolvido` carimbado (D-ORC-1), `preco_final`, `desconto_pct`, `semaforo`
  (**NUNCA margem/custo — TL-ORC-06**), `descricao_snapshot`, `quantidade`, `desconto_valor`, `total`,
  `tipo_atividade_alvo?` enum (D-ORC-16), `sequencia`).
- `LinkPublico` (`orcamento_id`, `token` URL-safe random ≥128 bits, `expira_em`, `revogado_em?`; 1 ativo por
  orçamento — partial unique).
- `Aprovacao` (`orcamento_id`, `versao_id`, `aprovado_em`, `aprovado_por?`, `canal`, `ip_hash`, `user_agent`,
  `nome_aprovador_hash`/`email_aprovador_hash` (HMAC Wave A — D-ORC-17; exibição = GATE-ORC-KMS-APROVADOR),
  `lgpd_aceite_versao_termo`+`lgpd_aceite_texto_hash` (ADV-ORC-04 — prova do consentido, não boolean);
  WORM Padrão B).
- `AnaliseCriticaOrcamento` (`orcamento_id`, `versao_id`, `perfil_no_evento`, `veredito`, `itens_avaliados`
  jsonb, `snapshot_hash`, `avaliada_em`, `avaliada_por`; WORM Padrão B — D-ORC-15).

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
| INV-ORC-APROVADO-ENVELOPE | `Orcamento.Aprovado` carrega envelope EXATO esperado pela OS (D-ORC-6, equip. por item); teste de contrato |
| INV-ORC-ANALISE-WORM | `AnaliseCriticaOrcamento` INSERT-only (trigger PG); `snapshot_hash` carimbado no envelope == hash da análise persistida (D-ORC-15); teste |
| INV-ORC-EQUIP-ITEM | item de calibração tem `equipamento_id` (vira atividade); item comercial NÃO tem (vira `ItemComercialOS`); domínio + teste das duas pontas |
| INV-ORC-MARGEM-OFF | snapshot do `ItemOrcamento` NUNCA persiste margem/custo (TL-ORC-06); serializer público allowlist (ADV-ORC-09); teste anti-vazamento |
| INV-TENANT-001/002/003 · INV-001 · INV-016 (herdadas) | tenant_id+RLS; WORM aprovação; WCAG tela pública (frente telas) |

## 6. Portas, eventos e seams

- **Consome:** `calcular_precos` (precificacao); `PrecoResolvido`/`preco_para_os` (pps); `ImpostoRepository`
  (config); portas análise crítica `escopos_cmc`/`procedimentos`/`padroes` query_service + `rt_competencia_cobre`;
  `tenant_perfil_e` (authz); `Cliente` (FK + ReferenciaPIIAnonimizavel); idempotência + eventos + perfil server-side.
- **Expõe/publica (catálogo; outbox):**

> **Nomenclatura (TL-ORC CRIT-1):** ações com `outbox=True` usam slug **lowercase** `orcamento.*` (molde
> `os.aberta`) — exigência do `CHECK bus_outbox_acao_enum_semantico`. Criar bloco `ACOES_ORCAMENTOS` em
> `audit/acoes_canonicas.py` + migration que emenda o CHECK (Fatia 1b, T-ORC-025b).

| Evento | Quando | Payload-chave | Consumer |
|--------|--------|---------------|----------|
| `orcamento.enviado` | enviar | orcamento_id, cliente_ref, canal, valor | crm |
| `orcamento.aprovado` | aprovar | **envelope exato §3 D-ORC-6 (equip. por item)** | operacao/os (cria OS), financeiro, crm |
| `orcamento.recusado` | recusar | orcamento_id, motivo? | crm |
| `orcamento.expirado` | job | orcamento_id | crm |
| `orcamento.convertido` | consumer `os.aberta` casa orcamento_id | orcamento_id, os_id | crm |
| `orcamento.analise_critica_reprovada`/`orcamento.analise_critica_com_ressalva` (NOVOS) | análise crítica | orcamento_id, itens_avaliados[], perfil_no_evento, analise_critica_id, severidade | qualidade/dashboard |

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
apontador-PII na spec; `[OAB-PRE-PROD]` base legal aceite público) · GATE-ORC-US010 (cobrança quando
contas-receber existir) · **GATE-ORC-KMS-APROVADOR** (cifragem KMS-tenant p/ EXIBIR nome do aprovador — hoje só
HMAC; D-ORC-17; junto de GATE-CAL-KMS-MRK) · **GATE-ORC-CMC-PREENCHIDO** (`[RBC-PRE-PROD]` onboarding —
tenant perfil A precisa ≥1 escopo CMC cadastrado antes de aprovar orçamento de calibração; senão fail-closed
reprova tudo — consultor-rbc C8) · **GATE-ORC-RT-MINIMO** (Wave B — checar ≥1 RT com competência declarada
p/ a grandeza antes de aprovar em perfil A; evita prometer o inexecutável — consultor-rbc C9).

## 10. Log de revisões

### v2 (2026-06-14) — DEPENDÊNCIA RESOLVIDA, spec desbloqueada para P3
- ✅ Frente `os-multi-equipamento` **FECHADA** (ADR-0082): OS aceita N equipamentos por atividade +
  `ItemComercialOS`; envelope `Orcamento.Aprovado` por item disponível e testado. R-ORC-3 viabilizado.
- ✅ Incorporadas as correções P2: D-ORC-6 (envelope por item), D-ORC-5 (rt_competencia sai TL-ORC-02 /
  padrao_disponivel = GATE TL-ORC-10), D-ORC-15 (`AnaliseCriticaOrcamento` TL-ORC-11), D-ORC-16 (tradução
  enum TL-ORC-05), D-ORC-17 (HMAC aprovador + GATE KMS ADV-ORC-05b), D-ORC-18 (numeração densa TL-ORC-08),
  D-ORC-19 (token resolve tenant TL-ORC-07/ADV-ORC-08a), D-ORC-14 (consumer `OS.Aberta` TL-ORC-03).
- ✅ Seams verificados no código (§11) — assinaturas reais conferidas; correção: `padrao_disponivel` e
  cifragem KMS-tenant NÃO existem → viraram GATE.
- **PRÓXIMO: P3 (plan + tasks).** O plan será revisado pelos subagentes (tech-lead + consultor-rbc nos pontos
  de análise crítica; advogado confirma D-ORC-17). Frontmatter sobe a `stable` no fechamento.

### v1 (2026-06-13) — PAUSADA em P2
- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES** (TL-ORC-01..11). Detalhe: `reviews-consolidado.md`.
- ✅ `advogado-saas-regulado` — **APROVA COM CORREÇÕES** (ADV-ORC-01..10; congelamento respeitado).
- ✅ batch Roldão: **R-ORC-1** equipamento no orçamento · **R-ORC-2** aprovação lógica-agora/PDF-depois ·
  **R-ORC-3 (estrutural)** N equipamentos por orçamento E OS + itens compartilhados.
- ⛔ **DEPENDÊNCIA DURA descoberta** (resolvida na v2): R-ORC-3 exigia retrofit da OS (1→N equipamentos).

## 11. Seams verificados no código (2026-06-14 — base do plan)

| Seam | Path | Assinatura/contrato |
|------|------|---------------------|
| Cálculo de preço | `src/application/precificacao/calculo.py` | `calcular_precos(CalcularPrecosInput, *, repos…, resolver_preco_fn, aliquota_imposto_fn) -> CalculoPrecoResultado`; `ItemCalculado{preco_base: PrecoResolvido, preco_final, desconto_pct, semaforo, margem/custo (só ver_margem)}` |
| Preço resolvido | `src/domain/produtos_pecas_servicos/entities.py:161` + `infrastructure/produtos_pecas_servicos/query_service.py:47` | `PrecoResolvido{item_id, item_versao_n, linha_tabela_id, tabela_id, preco, data_referencia, origem_preco}`; `preco_para_os(*, tenant_id, item_id, data_referencia, tabela_id?, …) -> PrecoResolvido` |
| Análise crítica CMC | `src/infrastructure/metrologia/escopos_cmc/query_service.py:45` | `cobre(*, tenant_id, grandeza, faixa_min, faixa_max, unidade, data) -> (bool, str)` fail-closed |
| Análise crítica proc. | `src/infrastructure/metrologia/procedimentos_calibracao/query_service.py:53,93` | `vigente_em(...) -> ProcedimentoSnapshot|None`; `cobre_procedimento(...) -> (bool, dict|None)` |
| Perfil regulatório | `src/infrastructure/authz/perfil_tenant_helper.py:44,106` | `obter_perfil_tenant_corrente() -> str`; `tenant_perfil_e(perfis) -> (bool, reason)` |
| Envelope OS (consumer) | `src/infrastructure/ordens_servico/consumers/orcamento.py:147,221` | header + `itens[{tipo, sequencia, valor_unitario, requer_recebimento, equipamento_id}]` (§D-ORC-6) |
| Numeração densa | `src/application/configuracoes_sistema/serie.py` + `infrastructure/.../repositories.py:195,287` | `reservar_numero(...)` + `confirmar_numero(*, tenant_id, reserva_id) -> bool` (advisory lock, gap-less) |
| ReferenciaPIIAnonimizavel | `src/domain/shared/value_objects.py:258` | `{uuid_atual_id?, hash_original (HMAC), key_id}` — par de campos no model |
| WORM hash-chain | `src/application/metrologia/calibracao/append_evento_calibracao.py` | `executar(AppendEventoInput, repo)`; dentro de `transaction.atomic`; advisory lock por agregado |
| Idempotência REST | `src/infrastructure/idempotencia/services_idempotencia.py:122` + `precificacao/_views_suporte.py:85` | `avaliar_chave_idempotencia(...)`; helper `_aplicar_idempotencia(request, *, …, payload_fingerprint)` reusável |
| Evento outbox | `src/infrastructure/audit/event_helpers.py:71` | `publicar_evento(*, acao, payload, causation_id, tenant_id, outbox=True, …)` — INSERT no `transaction.atomic` do caller |
| Rate-limit público | `src/infrastructure/equipamentos/services_ratelimit.py` + `views_qr_publico.py` | `avaliar_limite_ip(ip_hash)`; cache Redis DB2; molde de endpoint público |
| HMAC PII (Wave A) | `src/infrastructure/calibracao/lgpd.py` | `derivar_*_hash(...)`; KMS real = GATE (não existe boto3/KMS no código) |
| Path/molde módulo novo | `src/{domain,application}/comercial/` existem (clientes); `infrastructure/orcamentos/` a criar | `apps.py` label=`orcamentos`; migrations 0001_initial→0006_seed_authz; predicate authz no `ready()` |
