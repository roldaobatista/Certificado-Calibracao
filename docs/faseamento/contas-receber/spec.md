---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: contas-receber
tipo: spec
versao: 2
relacionados:
  - docs/faseamento/contas-receber/T-CR-000-investigacao.md
  - docs/faseamento/contas-receber/reviews-consolidado.md
  - docs/dominios/financeiro/modulos/contas-receber/prd.md
  - docs/dominios/financeiro/modulos/contas-receber/modelo-de-dominio.md
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0050-gateway-pagamento-pix-recorrente.md
  - docs/adr/0052-pix-recorrente-bcb-1071.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0032-fk-cross-modulo-referencia-pii-anonimizavel.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0080-numeracao-serie-documento-dois-regimes.md
  - docs/faseamento/orcamentos/spec.md
---

# Spec v2 — frente `contas-receber` (última peça do ciclo de receita, Wave A)

> Recorte sobre o PRD (US-CR-001..010, **stable**) + modelo-de-dominio + Família 0. **Frente #5 /
> nível 5** do `plano-dependencia-sistema.md` — FECHA a receita ponta a ponta. Greenfield de código
> (T-CR-000 §1); a cadeia de preço a montante (`configuracoes → pps → precificacao → orcamentos`) está
> COMPLETA — o bloqueio que travava esta frente em jun/09 caiu.
> **v2 (2026-06-15):** incorpora as correções P2 (tech-lead TL-CR-01..13 + advogado ADV-CR-01..07 +
> consultor-rbc RBC-CR-01..06 — `reviews-consolidado.md`). Os 3 CRIT do tech-lead revelaram contratos
> de módulos JÁ FECHADOS que a v1 ignorava: `clientes` tem bloqueio **PULL** (`InadimplenciaSource`); a
> OS já consome `os.faturada`/`os.paga` dangling; `os.concluida` é gravado no WORM da OS antes do outbox.
> Molde técnico = `fiscal` (NFS-e); molde de ritual/estilo = `orcamentos` (spec v2). Pronta para P3.

## 1. Tese e fronteira

`contas-receber` é o **título a receber do tenant**: nasce de um fato gerador (OS concluída,
NF-e emitida, contrato recorrente OU lançamento manual) → carimba valor + cliente + vencimento +
`categoria_receita` perfil-aware → emite cobrança (boleto/PIX/PIX-recorrente/cartão) via porta
`PaymentGatewayProvider` → concilia o pagamento (webhook HMAC idempotente OU baixa manual) →
quando atrasa, aplica juros/multa na leitura e, ultrapassado o **grace do perfil**, alimenta o
bloqueio de operação dependente; quando a última fatura vencida é quitada, dispara o desbloqueio.

**O que NÃO é (fronteiras):**
- **Não calcula preço** — fatura pelo valor **já carimbado** no fato gerador (INV-026; não reconsulta
  `precificacao`/catálogo). O preço nasceu em `orcamentos`/OS (cadeia de preço a montante).
- **Não emite NF-e** (`fiscal`) — consome `fiscal.nfse_emitida` (anexar NF à fatura = GATE Wave B).
- **Não é o gateway** — `PaymentGatewayProvider` é porta ACL (ADR-0050); Wave A roda com **Mock**;
  adapter Asaas real + HMAC real = GATE pré-produção (molde fiscal).
- **Não é dono do bloqueio do cliente** (TL-CR-01/05) — o estado `ClienteBloqueio` vive em `clientes`
  (modelo **PULL** já existente). CR alimenta o source de inadimplência e publica os fatos; quem bloqueia
  e desbloqueia é o `clientes`.
- **O bloqueio por inadimplência NÃO alcança o que já foi entregue** (ADV-CR-02/RBC-CR-06): afeta só
  **abertura de nova OS + aprovação de novo orçamento**. NÃO impede: emissão de certificado de OS **já em
  andamento** (reter seria NC ISO 17025 cl. 7.8), download de certificados/títulos pagos, leitura histórica
  (CDC art. 39 V — sem recusa de serviço já contratado).
- **Não confunde inadimplência do cliente com a do tenant** — `billing-saas` (ADR-0015) é outra coisa
  (INV-FIN-INAD-001). Nada cruza.
- **Não é a tela** — UI/portal de pagamento diferidos (frente de telas). O backend serve lógica + dados.

## 2. Recorte núcleo vs diferido (por US do PRD)

| US | Núcleo Wave A | Diferido (GATE/Wave B) |
|----|---------------|------------------------|
| US-CR-001 gerar título de OS/Certificado | consumer idempotente cria `Titulo` a partir de **`os.concluida` enriquecido** (gatilho canônico — D-CR-12) com cliente(`ReferenciaPIIAnonimizavel`)+valor+vencimento+`categoria_receita`+`perfil_no_evento` (do envelope); publica `os.faturada` (TL-CR-02); **lançamento MANUAL**; 1 OS→1 título ativo | gatilho `Certificado.Emitido` (reconciliado — GATE-CR-CERT-RECONCILIA); faturamento parcial por `AtividadeDaOS` (ADR-0051) |
| US-CR-002 emitir boleto/PIX/PIX-recorrente | porta `PaymentGatewayProvider` + **Mock** + `emitir-boleto`/`emitir-pix-recorrente`; `convenio_pix_id` NOT NULL recorrente (INV-FIN-GW-002); recorrente emite só o **1º título** + registra convênio; 503 em provider down | adapter **Asaas real** (GATE-CR-ASAAS) · cartão recorrente PCI · geração dos títulos recorrentes subsequentes (TL-CR-09 — precisa agrupador) |
| US-CR-003 baixa automática via webhook | webhook **HMAC + idempotência dupla** (`gateway_event_id` + estado do título — TL-CR-12); baixa ≤60s + `Pagamento` INSERT-only + snapshot `valor_atualizado_snapshot_em_pagamento`; publica `contas_receber.pago` + `os.paga`; tudo na MESMA `transaction.atomic` | HMAC real do Asaas + pentest anti-oráculo do endpoint público (GATE-CR-ASAAS / R-CR-NOVO-1) |
| US-CR-004 juros/multa + desconto pontualidade | cálculo **na leitura** `calcular_valor_atualizado(titulo, pagamentos, data, regra)` sobre **saldo** (TL-CR-10) + job diário transiciona `vencido` + remove desconto (INV-026 — não persiste valor inflado) | régua de lembrete (Wave B) |
| US-CR-005 régua lembrete WhatsApp/e-mail | — | lembretes ricos D-7/D-3/D-0 = Wave B (GATE-CR-REGUA; `OmniChannelProvider`) |
| US-CR-006 desbloqueio ao quitar | CR publica `contas_receber.pago` + expõe query `tem_outra_vencida_em_aberto(cliente_id)`; **consumer em `clientes`** encerra `ClienteBloqueio` + publica `cliente.desbloqueado` ≤5min (TL-CR-05); parcial mantém bloqueio | — |
| US-CR-007 cobrança via porta | coberto por US-CR-002 | — |
| US-CR-008 categoria receita perfil-aware | `categoria_receita` enum; predicate matriz §3.1 (A→RBC; demais 403); derivação automática pelo `perfil_no_evento`; validação no use case (ADR-0073) | — |
| US-CR-009 snapshot no pagamento | coberto por US-CR-003 (M-FIN-002) | — |
| US-CR-010 bloqueio dura perfil-aware + override A3 | adapter `InadimplenciaSource` aplica grace 45/20/30/7 (D-CR-9); **notificação D+30/D+45 perfil A via `send_mail` simples em Wave A** (CDC — RBC-CR-01/ADV-CR-01); payload rico (títulos vencidos + data bloqueio + canal); `OverrideBloqueio` WORM (justificativa≥100 anti-PII) | **assinatura A3 real** do override (Lacuna — GATE-CR-A3); lembretes ricos (Wave B) |

## 3. Decisões cravadas (D-CR-1..17 + P2 D-CR-18..23)

- **D-CR-1 — Path FLAT (molde fiscal) [TL-CR-04].** `src/domain/contas_receber/` +
  `src/application/contas_receber/` + `src/infrastructure/contas_receber/` (`app_label = contas_receber`).
  Consistente com o irmão financeiro `fiscal` (também flat); `financeiro/` só se criaria movendo fiscal+
  billing-saas juntos no futuro (não agora).
- **D-CR-2 — Agregado raiz = `Titulo` (= "ContasReceber" do PRD); `Fatura` DIFERIDA [TL-CR-09 OK].**
  Núcleo = `Titulo` raiz + `Parcela` (sub) + `Pagamento` (evento imutável); **1 fato gerador → 1 título**.
  `Fatura` agrupadora (N títulos / consolidação) = **Wave B**. Reconcilia PRD×modelo (ADR no P8, molde
  ADR-0083). Recorrência PIX/cartão Wave A emite só o 1º título.
- **D-CR-3 — Máquina de estados (Padrão A), `Mapping[Estado, frozenset]` em `transicoes.py` [TL-CR-10 OK].**
  `emitido → pago | parcialmente_pago | vencido | cancelado`; `vencido → pago | parcialmente_pago |
  cancelado`; `parcialmente_pago → pago | vencido | cancelado`. Terminais: `pago`, `cancelado`.
  `cobranca_emitida` = **derivado** de `gateway_externo_id NOT NULL` (não estado). `em_disputa` = Wave B.
  `cancelado` só sem pagamento parcial.
- **D-CR-4 — Juros/multa/desconto na LEITURA (INV-026) [TL-CR-10].** Função pura
  `calcular_valor_atualizado(titulo, pagamentos: list[Pagamento], data, regra) -> Dinheiro` — juros (1% a.m.
  proporcional) + multa (2% one-shot D+1) incidem sobre o **saldo** (`valor_original - sum(pagamentos)`),
  remove desconto pontualidade após vencimento. **NÃO persiste valor inflado** — persiste a REGRA. Job diário
  `aplicar_juros_multa_diario` só (a) transiciona `emitido→vencido` e (b) remove flag de desconto; o ÚNICO
  snapshot materializado é `valor_atualizado_snapshot_em_pagamento` na baixa (M-FIN-002).
- **D-CR-5 — `categoria_receita` perfil-aware (INV-FIN-PERFIL-001 + ADR-0067) [ADV-CR-06/RBC-CR-02 OK].**
  Enum `{CALIBRACAO_RBC, CALIBRACAO_NAO_RBC, CALIBRACAO_BASICA, MANUTENCAO_CORRETIVA, MANUTENCAO_PREVENTIVA,
  PECA_REVENDA, DESLOCAMENTO, OUTROS}`. Predicate da matriz §3.1: `CALIBRACAO_RBC` exige `perfil='A'`
  (mismatch → 403 `CATEGORIA_RECEITA_EXIGE_PERFIL_A` + evento `contas_receber.categoria_receita_bloqueada`);
  `CALIBRACAO_BASICA` = default perfil D. Derivação automática pelo `perfil_no_evento` (A→RBC; B/C→NAO_RBC;
  D→BASICA). **Validação no use case (ADR-0073), nunca no DRF.** O payload `titulo_emitido` carrega o enum;
  **dependência cruzada (RBC-CR-02):** `fiscal` mapeia `CALIBRACAO_BASICA` para descrição sem "ISO 17025"/"RBC".
- **D-CR-6 — `perfil_no_evento` cravado no INSERT, imutável (INV-FIN-SNAPSHOT-PERFIL-001 / ADR-0067 §3)
  [TL-CR-07 + RBC-CR-03].** `CHAR(1)`. **Dois caminhos distintos:**
  - **Síncrono (REST, lançamento manual):** resolvido na borda via `obter_perfil_tenant_corrente()` (ContextVar,
    fail-closed 50ms) e passado explícito ao use case (molde fiscal).
  - **Assíncrono (consumer de `os.concluida`/`fiscal.nfse_emitida`):** vem de `envelope["perfil_no_evento"]`
    (INT-03, já no envelope v10 — perfil do momento da publicação do fato gerador). **PROIBIDO** reler
    `obter_perfil_tenant_corrente()` no worker (pegaria o perfil ATUAL, furando a defesa CGCRE cl. 8.4 se o
    tenant mudou de perfil). `None` → fail-closed `PerfilIndeterminado`.
  - Trigger fallback `BEFORE INSERT` só via `COALESCE(NEW.perfil_no_evento, current_setting('app.perfil_tenant'))`
    — ativa apenas quando chega NULL, **nunca sobrescreve** valor já preenchido.
- **D-CR-7 — Porta `PaymentGatewayProvider` (ADR-0050) com Mock no domínio (molde `MockFiscalProvider`).**
  `Protocol` + `@runtime_checkable` em `src/domain/contas_receber/portas.py`. Operações: `criar_cobranca`,
  `cancelar_cobranca`, `criar_recorrencia`, `cancelar_recorrencia`, `verificar_webhook(payload, signature) ->
  EventoNormalizado` (HMAC). `MockPaymentGatewayProvider` (modos `always_confirm`/`pending_then_confirm`/
  `always_reject`/`network_timeout`; `gateway_id` determinístico não-PII). Adapter Asaas = **GATE-CR-ASAAS**.
  Import de SDK confinado a `infrastructure/contas_receber/` (hook `cr-provider-import-fronteira-check.sh`,
  molde `fiscal-provider-import-fronteira-check`).
- **D-CR-8 — Webhook de baixa: HMAC + idempotência DUPLA + atomicidade [TL-CR-12 + R-CR-NOVO-1].** Endpoint
  público `ContasReceberWebhookView` (sem auth de usuário). **Net-new** — molde = endpoint público de orçamentos
  (D-ORC-19), NÃO fiscal (que não tem webhook). Resolve tenant via função `SECURITY DEFINER`/índice ANTES de
  `run_in_tenant_context`; **anti-oráculo**: `gateway_id` inexistente ≡ HMAC inválido = 401 indistinguível (sem
  diferença de timing — validação real = pentest GATE-CR-ASAAS). Valida HMAC → 401 + incidente
  `seguranca.webhook_hmac_invalido` se inválido. Idempotência **dupla**: `INSERT ... ON CONFLICT DO NOTHING` em
  `gateway_events` por `gateway_event_id` (replay exato → 200 sem efeito) **E** estado (título já `pago` → 200
  sem re-gravar `Pagamento`). Baixa + INSERT `gateway_events` + `publicar_evento` na MESMA `transaction.atomic`.
- **D-CR-9 — Inadimplência dura perfil-aware via ADAPTER do `InadimplenciaSource` existente (PULL) [TL-CR-01 +
  ADV-CR-01 + RBC-CR-01].** **NÃO é PUSH.** O `clientes` já tem: Protocol
  `InadimplenciaSource.iter_inadimplentes_90d()` (`domain/comercial/clientes/inadimplencia_source.py`), job
  `job_inadimplencia_alertas` que cria `ClienteBloqueio` + publica `cliente.bloqueado`, e flag
  `Tenant.bloqueio_automatico_inadimplencia_habilitado` (`tenant/models.py:68`, default `false`). CR implementa o
  **adapter real** em `infrastructure/contas_receber/` substituindo o interino: itera `TituloVencido` aplicando o
  predicate canônico **`grace_period_inadimplencia_por_perfil(tenant_id) -> int`** (A=45, B=20, C=30, D=7; lê
  perfil via ContextVar, fail-closed 50ms) — só entra na lista o título com `vencimento + grace_do_perfil <=
  today`. `InadimplenciaItem` ganha `perfil`/`grace_perfil`. A flag canônica é a existente (não criar nova).
  **Notificação D+30/D+45 perfil A em Wave A via `send_mail` Django simples** (cumpre CDC art. 6º III/IV + Lei
  14.181/2021; lembretes ricos D-7/D-3/D-0 = Wave B). Payload do aviso D+30 e do evento
  `contas_receber.inadimplencia_dura_atingida` carrega obrigatoriamente `titulos_vencidos[{titulo_id,
  valor_original, data_vencimento, dias_vencido}]` + `data_bloqueio_prevista` + `canal_regularizacao_url`
  (config do tenant). **GATE-CR-NOTIF-D30-PERFIL-A** bloqueante: tenant A só ativa a flag com canal operacional.
- **D-CR-10 — Override A3 do dono, anti-PII (AC-CR-010-5) [ADV-CR-04].** `OverrideBloqueio{titulo_id, cliente_id,
  novo_prazo_max_dias (≤90), justificativa (≥100, anti-PII via `INV-CAL-TXT-001` — existe em
  `calibracao/models.py` + REGRAS), a3_signature_id, usuario_id, perfil_no_evento}` em audit WORM (Padrão B,
  INSERT-only). Estende grace até D+90; limite 5%/mês dos bloqueios por tenant (contador por query mensal no use
  case; estouro → alerta P1 + bloqueia novos — ADR-0043 §3 / R-CR-NOVO-4). **A3 real (Lacuna) = GATE-CR-A3**
  (Wave A grava `a3_signature_id` como referência sem verificação). Endpoint exige papel `gerente_financeiro`/
  `admin_tenant`.
- **D-CR-11 — Desbloqueio: CR publica, `clientes` desbloqueia (INV-FIN-REATIV-001 / GATE-CLI-6) [TL-CR-05].**
  CR publica `contas_receber.pago` + expõe query read-only `tem_outra_vencida_em_aberto(cliente_id) -> bool`. O
  módulo `clientes` ganha **consumer novo** de `contas_receber.pago` que, se o cliente estava bloqueado por
  inadimplência e não há outra vencida em aberto, encerra o `ClienteBloqueio` (`desbloqueado_em`) e publica
  `cliente.desbloqueado{cliente_id, motivo:"pagamento_quitou_inadimplencia", titulo_id_quitado}` ≤5min. Idempotente.
  Pagamento parcial com outra vencida → NÃO desbloqueia (AC-CR-006-2).
- **D-CR-12 — GATILHO DE AUTO-FATURAMENTO = `os.concluida` enriquecido no OUTBOX [TL-CR-03/06/08 + RBC-CR-05].**
  - **Gatilho canônico = `os.concluida`** — momento correto (serviço entregue, valor carimbado em
    `OSSnapshot.valor_total`; cobrar na aprovação do orçamento quebraria B2B). Enriquecer o payload do **OUTBOX**
    (montado em `repositories.py:660` ao cruzar pro bus, lendo da `OS`/`OSSnapshot`): adicionar
    `cliente_referencia_hash`+`cliente_key_id`+`valor_total` (+`perfil_no_evento` já no envelope). **NUNCA** injetar
    no `EventoDeOS.payload_data` (cadeia WORM 25a imutável — proibido por `sanitizar_payload_evento_os`); o
    payload_data WORM segue minimalista. Cliente vai como `ReferenciaPIIAnonimizavel` (hash+key_id), não id raw.
    Toca módulo OS (fechado) → fatia própria com skip de hooks legado justificado. **GATE-CR-OS-EVENTO.**
  - **`os.faturada`/`os.paga` publicados por CR (TL-CR-02):** a OS já tem consumers dangling
    (`ordens_servico/apps.py:131-132`); CR publica `os.faturada` (payload `{os_id}`) ao criar título de OS e
    `os.paga` ao dar baixa — em `ACOES_OS` (namespace do agregado dono do estado).
  - **Idempotência de negócio (TL-CR-06):** `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado` (1 OS → 1
    título ativo). `os.reaberta` → título cancelável só sem pagamento parcial (consumer ou non-goal explícito).
  - **Gatilho secundário = `fiscal.nfse_emitida`** (tem `valor_centavos`; cliente via `cliente_referencia_hash`)
    para "anexar NF / receita órfã" (INV-FIS-CR-001) — **GATE-CR-NFSE** (resolver hash→id; Wave B).
  - **`Certificado.Emitido` RECONCILIADO, não construído (RBC-CR-05 confirma):** certificado nasce dentro da OS
    (ADR-0023/0082); faturar cert E OS = dupla cobrança. Certificado NÃO é unidade de cobrança independente; cert
    de padrão interno = não-faturável. ADR de reconciliação no P8 (emenda ADR-0043/INV-CAL-FIN-001, molde ADR-0083).
    **GATE-CR-CERT-RECONCILIA.**
  - **Conversão de valor (R-CR-NOVO-2):** `valor_total` chega string decimal (`"1234.56"`); CR padroniza em centavos
    (`Dinheiro`) num único ponto na borda + teste de borda.
  - **Tenant suspenso (R-CR-NOVO-3 — PRD §10 já decide):** consumer NÃO cria título quando tenant suspenso (mantém
    leitura, bloqueia emissão — ADR-0035); manda pra dead-letter / reprocessa ao reativar.
  - **Sempre disponível = lançamento MANUAL** (financeiro digita) — piso garantido do núcleo (T-CR-000 §5).
- **D-CR-13 — REST molde fiscal/precificacao.** `ContasReceberViewSet` (autenticado) + `ContasReceberWebhookView`
  (público). Idempotência 2 camadas (`Idempotency-Key` em escrita + idempotência de negócio por `os_id`/
  `gateway_event_id`). ACTION_MAP authz `contas_receber.*`. `publicar_evento(outbox=True)` no `transaction.atomic`.
  Perfil/categoria server-side. Advisory lock por `(tenant_id, fato_gerador_id)`.
- **D-CR-14 — Eventos `contas_receber.*` lowercase no outbox [TL-CR-11].** Criar bloco `ACOES_CONTAS_RECEBER` em
  `audit/acoes_canonicas.py` + adicioná-lo à união `ACOES_CANONICAS` (senão `assert_acao_canonica` faz todo
  publish falhar). NÃO precisa migration de CHECK (CHECK é sintático). Adicionar `os.faturada`/`os.paga` a
  `ACOES_OS`. Slugs: `contas_receber.titulo_emitido`, `.boleto_emitido`, `.pago`, `.titulo_vencido`,
  `.titulo_cancelado`, `.inadimplencia_dura_atingida`, `.categoria_receita_bloqueada`, `.gateway_indisponivel`.
- **D-CR-15 — Parcelamento simples (núcleo).** `Parcela` sub (`titulo_id, numero, valor, vencimento, status`); N
  parcelas iguais na emissão. Baixa parcial com título sucessor = Wave B.
- **D-CR-16 — Cliente via `ReferenciaPIIAnonimizavel` (ADR-0032; molde orçamento D-ORC-4) [ADV-CR-03].**
  `cliente_atual_id` (FK SET_NULL) + `cliente_referencia_hash` (HMAC NOT NULL) + `cliente_key_id`. Consumer
  `Cliente.Anonimizado` zera o id, mantém o hash (rastro fiscal/contábil 5-25a perfil-aware — base legal por
  perfil no GATE-LGPD-RAT-CR). Cliente obrigatório p/ criar título.
- **D-CR-17 — WORM/RLS, 5 migrations (molde fiscal) [RBC-CR-04].** `0001_initial` → `0002_rls_policies`
  (ENABLE+FORCE+4 policies v2) → `0003_triggers_worm` (block-delete + worm_check: probatórios congelados;
  `status`/timestamps mutáveis; `data_baixa`/`cancelado_em` one-shot) → `0004_grants_app_user` → `0005_seed_authz`.
  **`Pagamento` INSERT-only.** Numeração: título = documento fiscal-adjacente = **GAP_LESS** (ADR-0080,
  `regime_numeracao_do_tipo` — não é decisão aberta; ver D-CR-18). Retenção perfil-aware (25a A/B/C; 5a D — matriz
  §3.1): anonimização do `Pagamento` perfil D preserva `valor`/`data`/`origem`/`titulo_id` (RF 5a), zera
  `comprovante_url`; `cliente_referencia_hash` já é anonimizado por design.

### Decisões adicionadas no P2 (correções dos revisores — v2)

- **D-CR-18 — Numeração GAP_LESS via ADR-0080 [TL-CR-13].** GATE-CR-SERIE-REGIME **FECHADO**: o regime é DERIVADO
  do tipo de documento (`application/configuracoes_sistema/serie.py` — fatura/certificado = GAP_LESS), nunca do
  caller. **A confirmar na fatia:** se o `numero_sequencial_tenant` do título é exigência contábil/fiscal real
  (então usa `reservar_numero`/`confirmar_numero` GAP_LESS) ou se o id interno + número do boleto (do gateway)
  bastam — neste caso remover a dependência `SerieDocumento`. Default: usar `SerieDocumento` GAP_LESS só se houver
  requisito de fatura numerada sequencial.
- **D-CR-19 — INV-CR-WEBHOOK-PAYLOAD-MINIMO [ADV-CR-05].** O handler do webhook extrai só os campos que `Pagamento`
  precisa; NÃO loga payload bruto com PII do pagador (`customer.name`/`cpf_cnpj`/`email`). Enforçado no
  GATE-CR-ASAAS (adapter real); Wave A (Mock) documenta a regra.
- **D-CR-20 — INV-CR-OVERRIDE-ANTI-PII [ADV-CR-04].** Campo `justificativa` do override passa por filtro anti-PII
  (`INV-CAL-TXT-001` ou validação equivalente) antes de gravar em WORM. Retenção do `OverrideBloqueio` = 5a (ato
  gerencial / fiscal).
- **D-CR-21 — Bloqueio só de operação futura, nunca do entregue [ADV-CR-02/RBC-CR-06].** `INV-CLI-BLOQ-001`
  complementada: bloqueio dura atinge abertura de nova OS + aprovação de novo orçamento; NÃO impede emissão de
  certificado de OS já em andamento, nem download/leitura histórica. AC de teste para a janela "cliente fica
  inadimplente durante a execução da OS → certificado é emitido ao concluir".
- **D-CR-22 — Notificação CDC para todos os perfis via payload do evento [ADV-CR-07].** `contas_receber.titulo_vencido`
  carrega payload suficiente para o tenant notificar o cliente final em qualquer perfil; termos de uso atribuem ao
  tenant (controlador) a comunicação prévia (Aferê = operador). Item de GATE-LGPD-RAT-CR + termos de uso.
- **D-CR-23 — Conversão de valor centralizada [R-CR-NOVO-2].** CR opera internamente em centavos (`Dinheiro`);
  `valor_total` string decimal → centavos num único conversor de borda, com teste de borda (`"0.10"`, `"100.005"`,
  zero, arredondamento).

## 4. Modelo (domínio)

**Path:** `src/domain/contas_receber/` (D-CR-1).

**Agregado raiz `Titulo`** (= `ContasReceber` do PRD): `id`, `tenant_id` (NOT NULL),
`cliente_atual_id`/`cliente_referencia_hash`/`cliente_key_id` (D-CR-16), `numero_sequencial_tenant?`
(GAP_LESS — D-CR-18), `valor_original` (`Dinheiro`), `data_emissao`, `data_vencimento`, `data_baixa?`,
`estado` (enum máquina D-CR-3), `meio` (`boleto|pix|pix_recorrente|cartao|cartao_recorrente`),
`categoria_receita` (D-CR-5), `perfil_no_evento` (CHAR(1) — D-CR-6), `origem` (`os|nfse|contrato|manual`),
`os_id_origem?`, `nfse_id_origem?`, `gateway_externo_id?`, `convenio_pix_id?` (NOT NULL se
`meio=pix_recorrente`), `linha_digitavel?`/`qr_code?`/`tx_id?`, `regra_juros_id?`/`regra_multa_id?`/
`regra_desconto_id?`, `desconto_pontualidade_pct?`, `revision`, `criado_em`.
Constraint: `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado` (TL-CR-06).

**Entidades filhas:**
- `Parcela` (`titulo_id`, `numero`, `valor`, `vencimento`, `status`; D-CR-15).
- `Pagamento` (`titulo_id`, `valor`, `data`, `origem` (`webhook_gateway|manual|pix_direto`), `gateway_event_id?`,
  `comprovante_url?`, `valor_atualizado_snapshot_em_pagamento` (`Dinheiro` — M-FIN-002), `criado_em`; **INSERT-only**).
- `OverrideBloqueio` (`titulo_id`, `cliente_id`, `novo_prazo_max_dias` (≤90), `justificativa` (≥100, anti-PII),
  `a3_signature_id`, `usuario_id`, `perfil_no_evento`, `criado_em`; WORM Padrão B — D-CR-10).

**VOs:** `Dinheiro` (centavos+moeda, reuso `shared`), `RegraJurosMulta`, `CobrancaCriada`/`CobrancaCancelada`/
`RecorrenciaCriada`/`EventoNormalizado` (resultados da porta), `ReferenciaPIIAnonimizavel` (reuso `shared`).

**Erros:** `ClienteObrigatorio` (422), `CategoriaReceitaExigePerfilA` (403), `GatewayIndisponivel` (503),
`ConvenioPixAusente` (422), `TransicaoProibida`/`EstadoInvalido` (409), `TituloComPagamentoParcial` (409),
`WebhookHMACInvalido` (401), `PerfilIndeterminado` (422 fail-closed), `OverrideForaDeAlcada`/
`JustificativaInsuficiente` (422/403), `TenantSuspensoEmissaoBloqueada` (deadletter — R-CR-NOVO-3).

**Máquina de estados (D-CR-3):**
```
emitido            → pago | parcialmente_pago | vencido | cancelado
vencido            → pago | parcialmente_pago | cancelado
parcialmente_pago  → pago | vencido | cancelado
pago               → (terminal)
cancelado          → (terminal)
```

## 5. Invariantes candidatas (P7 crava em REGRAS + hook)

> Família **INV-FIN-*** vive em `docs/faseamento/invariantes-futuras.md`; pelo critério de retorno R14
> volta ao mestre `REGRAS-INEGOCIAVEIS.md` na fatia que cria os hooks (P3/plan). INV-FIS-CR-001 e
> INV-CAL-FIN-001/002 idem (reconciliadas — GATE-CR-CERT-RECONCILIA).

| INV candidata | Enforcement |
|---------------|-------------|
| INV-FIN-GW-001 | webhook exige HMAC + idempotência por `gateway_event_id`; replay→200, inválido→401+incidente; auditor-idempotencia/seguranca + teste |
| INV-FIN-GW-002 | `meio=pix_recorrente` exige `convenio_pix_id NOT NULL`; CHECK + teste |
| INV-FIN-PERFIL-001 | `categoria_receita=CALIBRACAO_RBC` só `perfil='A'`; mismatch→403+evento; predicate no use case + hook + teste UNHAPPY por perfil |
| INV-FIN-GRACE-PERFIL-001 | grace 45/20/30/7 via `grace_period_inadimplencia_por_perfil` no adapter `InadimplenciaSource`; override A3 até D+90; teste por perfil |
| INV-FIN-SNAPSHOT-PERFIL-001 | `perfil_no_evento` cravado no INSERT, imutável; consumer lê do envelope (não current_setting); teste anti-mutação + teste perfil-mudou |
| INV-FIN-REATIV-001 | `contas_receber.pago` da última vencida → `clientes` publica `cliente.desbloqueado` ≤5min; idempotente; teste GATE-CLI-6 (happy + parcial) |
| INV-FIN-INAD-001 | inadimplência cliente (`Cliente.bloqueado`) ≠ tenant (`billing-saas`); hook `policy-tenant-vs-cliente.sh` |
| INV-026 (herdada) | título não recalcula por mudança de tabela; valor na leitura (sobre saldo), regra persistida; teste regressão dura |
| INV-CR-OS-TITULO-UNICO (nova) | `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado`; consumer idempotente por `os_id`; teste replay + os.reaberta |
| INV-CR-PAGAMENTO-WORM (nova) | `Pagamento` INSERT-only (trigger block-update/delete); teste anti-mutação |
| INV-CR-OVERRIDE-WORM (nova) | `OverrideBloqueio` INSERT-only + justificativa≥100 anti-PII + limite 5%/mês; trigger + teste |
| INV-CR-OVERRIDE-ANTI-PII (nova — D-CR-20) | `justificativa` filtrada anti-PII (INV-CAL-TXT-001) antes do WORM; teste |
| INV-CR-WEBHOOK-PAYLOAD-MINIMO (nova — D-CR-19) | handler não persiste/loga PII do pagador além do que `Pagamento` exige; revisão + teste no GATE-CR-ASAAS |
| INV-FIS-CR-001 (reconciliada) | gatilho de faturamento = `os.concluida` (não `Fiscal.NFSeEmitida` único); NF anexa = GATE; consumer + teste latência |
| INV-TENANT-001/002/003 · INV-008 (herdadas) | tenant_id + RLS ENABLE+FORCE; cross-tenant 404/422 anti-oracle; audit WORM de emissão/baixa |

## 6. Portas, eventos e seams

- **Consome (portas/seams):** `PaymentGatewayProvider` (Mock — D-CR-7); `obter_perfil_tenant_corrente`/
  `tenant_perfil_e` (authz); `grace_period_inadimplencia_por_perfil` (predicate — criar neste módulo);
  `InadimplenciaSource` (Protocol de `clientes` — implementar adapter, TL-CR-01); `Cliente` (FK +
  `ReferenciaPIIAnonimizavel`) + `cliente.prazo_dias`; `SerieDocumento` (GAP_LESS — se D-CR-18 confirmar);
  idempotência REST + consumer (ADR-0033) + `publicar_evento` outbox; HMAC PII stub (`calibracao/lgpd.py`);
  `INV-CAL-TXT-001` (anti-PII).
- **Consome (eventos / fatos geradores):** `os.concluida` (enriquecido — D-CR-12); `fiscal.nfse_emitida`
  (secundário — GATE); `os.reaberta` (cancelar título sem pagamento); `Cliente.Anonimizado`; auto-consome
  `contas_receber.pago`? **NÃO** — quem desbloqueia é `clientes` (D-CR-11).
- **Publica (catálogo; outbox lowercase — D-CR-14):**

| Evento (slug bus) | Quando | Payload-chave | Consumer |
|--------|--------|---------------|----------|
| `contas_receber.titulo_emitido` | criar título | titulo_id, cliente_ref, valor, vencimento, categoria, perfil_no_evento | crm, comissoes (Wave B) |
| `os.faturada` (ACOES_OS) | criar título de OS | os_id | **ordens_servico** (handle_os_faturada — já existe) |
| `contas_receber.boleto_emitido` | emitir cobrança | titulo_id, linha_digitavel?/qr_code? | crm, portal |
| `contas_receber.pago` | baixa | titulo_id, valor, pago_em, origem, perfil_no_evento | **clientes** (desbloqueio), crm, comissoes |
| `os.paga` (ACOES_OS) | baixa de título de OS | os_id | **ordens_servico** (handle_os_paga — já existe) |
| `contas_receber.titulo_vencido` | job | titulo_id, dias_atraso, **+payload p/ notificação CDC (D-CR-22)** | régua (Wave B), portal |
| `contas_receber.titulo_cancelado` | cancelar | titulo_id, razao | crm, auditoria |
| `contas_receber.inadimplencia_dura_atingida` | adapter/job | cliente_id, **titulos_vencidos[], data_bloqueio_prevista, canal_regularizacao_url** (ADV-CR-01), perfil | comercial/clientes (bloqueia) |
| `contas_receber.categoria_receita_bloqueada` | use case (403) | titulo_id?, categoria, perfil | auditoria (anti-fraude fiscal) |
| `contas_receber.gateway_indisponivel` | provider down | titulo_id, retry_em_segundos | observabilidade |

## 7. REST (núcleo)

`ContasReceberViewSet` (autenticado): `criar` (manual) / `emitir-boleto` / `emitir-pix-recorrente` /
`baixa-manual` / `cancelar` / `override-bloqueio` (papel gerente) / `retrieve` / `list` (filtro status,
vencimento, cliente, `categoria_receita`). `ContasReceberWebhookView` (sem auth de usuário): POST webhook
gateway (HMAC + idempotência dupla + tenant server-side + anti-oráculo). Ações authz `contas_receber.*`:
`criar`, `emitir`, `baixar`, `cancelar`, `override_bloqueio`, `ver`. `Idempotency-Key` em escrita; webhook
idempotente por `gateway_event_id`. Advisory lock `pg_advisory_xact_lock(hashtext("cr:{op}:{tenant}:{fato}"))`.

## 8. Non-goals (além dos do PRD §6)

`Fatura` agrupadora multi-título (Wave B) · régua de lembrete WhatsApp/e-mail rica (Wave B; só notificação CDC
D+30/D+45 perfil A via send_mail em Wave A) · adapter Asaas real + HMAC real (GATE-CR-ASAAS) · A3 real do
override (GATE-CR-A3) · gatilho `Certificado.Emitido` (reconciliado — GATE-CR-CERT-RECONCILIA) · faturamento
parcial por `AtividadeDaOS` (Wave B) · baixa parcial com título sucessor · cartão recorrente PCI (Wave B) ·
geração de títulos recorrentes subsequentes (Wave B — precisa agrupador) · conciliação OFX (Wave B) · `em_disputa`
(Wave B) · factoring/antecipação · Open Finance · multi-gateway · cobrança judicial/protesto · DRE/fluxo projetado
· marketplace · telas/portal de pagamento.

## 9. GATEs rastreados

- **GATE-CR-INADIMPLENCIA-RECONCILIA** (TL-CR-01) — CR implementa adapter real do `InadimplenciaSource` (PULL);
  flag canônica = `bloqueio_automatico_inadimplencia_habilitado`. Decidido antes da fatia de inadimplência.
- **GATE-CR-NOTIF-D30-PERFIL-A** (RBC-CR-01/ADV-CR-01) — bloqueante: tenant perfil A só ativa a flag de bloqueio
  com canal de notificação D+30/D+45 operacional (Wave A = `send_mail`).
- **GATE-CR-OS-EVENTO** (TL-CR-03) — enriquecer payload do OUTBOX de `os.concluida` (cliente+valor+perfil), nunca o
  WORM da OS; toca módulo OS (fechado), fatia própria com skip de hooks legado justificado.
- **GATE-CR-CERT-RECONCILIA** (TL-CR-08/RBC-CR-05) — ADR no P8 reconcilia ADR-0043/INV-CAL-FIN-001 (certificado não
  é unidade de cobrança; cert de padrão interno = não-faturável) — molde ADR-0083.
- **GATE-CR-ASAAS** (`[SEC-PRE-PROD]`) — adapter Asaas real + webhook HMAC real + pentest anti-oráculo/timing do
  endpoint público (R-CR-NOVO-1) + INV-CR-WEBHOOK-PAYLOAD-MINIMO real.
- **GATE-CR-A3** (`[SEC-PRE-PROD]`) — assinatura A3 real (Web PKI Lacuna) do override; hoje só HMAC stub (junto de
  GATE-CAL-KMS-MRK / GATE-ORC-KMS-APROVADOR).
- **GATE-CR-NFSE** — anexar NF-e à fatura / resolver `cliente_referencia_hash→id` (INV-FIS-CR-001; Wave B).
- **GATE-CR-REGUA** (Wave B) — lembretes ricos via `OmniChannelProvider`/`EmailTemplateProvider` (ADR-0060).
- **GATE-LGPD-RAT-CR** (CONGELADO até GATE-LGPD-RAT-CONSOLIDACAO) — base legal do bloqueio (CC art. 476 / CDC art.
  39 V / Lei 14.181) + notificação CDC conteúdo mínimo + retenção perfil-aware do hash (ISO 8.4 / CTN art. 195) +
  override anti-PII + webhook payload mínimo + termos de uso controlador×operador (ADV-CR-01/03/04/05/07; RBC-CR-04).
- **GATE-CR-SERIE-REGIME** — **FECHADO** por ADR-0080 (título = GAP_LESS derivado do tipo); só confirmar na fatia se
  `numero_sequencial_tenant` é exigência real (D-CR-18).

## 10. Log de revisões

### v2 (2026-06-15) — P2 incorporado, pronta para P3
- ✅ `tech-lead-saas-regulado` (Opus) — **APROVA COM CORREÇÕES** (TL-CR-01..13 + R-CR-NOVO-1..4). 3 CRIT
  (clientes PULL / os.faturada-paga dangling / WORM da OS) incorporados.
- ✅ `advogado-saas-regulado` — **APROVA COM CORREÇÕES** (ADV-CR-01..07; congelamento RAT respeitado).
- ✅ `consultor-rbc-iso17025` — **APROVA COM CORREÇÕES** (RBC-CR-01..06; grace D+45 e categoria RBC validados).
- ✅ Detalhe item-a-item em `reviews-consolidado.md`. Decisões novas D-CR-18..23; GATEs novos (INADIMPLENCIA,
  NOTIF-D30, OS-EVENTO); GATE-SERIE fechado.
- **PRÓXIMO: P3 (plan + tasks).** O plan será revisado nos pontos de inadimplência/perfil (tech-lead) antes de
  codar. Família INV-FIN-* volta ao mestre na fatia que cria os hooks. Frontmatter sobe a `stable` no fechamento.

### v1 (2026-06-15) — spec inicial, pausada em P2
- ✅ T-CR-000 §7 — re-rastreamento de gatilhos pós-orçamentos (D-CR-12). Recorte + D-CR-1..17 + modelo + INV.

## 11. Seams verificados no código (2026-06-15 — base do plan)

| Seam | Path | Assinatura/contrato |
|------|------|---------------------|
| Molde técnico completo | `src/domain/fiscal/`, `src/application/fiscal/`, `src/infrastructure/fiscal/` | domínio frozen+slots, máquina `Mapping` em `transicoes.py`, Protocol `@runtime_checkable`, Mock no domínio, 5 migrations, ViewSet+advisory lock+idempotência+publicar_evento |
| Bloqueio inadimplência PULL (existente) | `domain/comercial/clientes/inadimplencia_source.py:17-33`; `infrastructure/clientes/inadimplencia.py:38-39`; `clientes/management/commands/job_inadimplencia_alertas.py:53-120` | Protocol `iter_inadimplentes_90d()`; CR implementa adapter real (TL-CR-01) |
| Flag de bloqueio (existente) | `src/infrastructure/tenant/models.py:68` | `bloqueio_automatico_inadimplencia_habilitado` (default false) — flag canônica, não criar nova |
| Consumers OS dangling | `ordens_servico/apps.py:131-132`; `ordens_servico/consumers/financeiro.py:1-12` | `handle_os_faturada`/`handle_os_paga` esperam `os.faturada`/`os.paga` (CR publica — TL-CR-02) |
| `os.concluida` (a enriquecer no OUTBOX) | `value_objects.py:143`; `concluir_atividade.py:219-225`; `repositories.py:660-665` | payload WORM minimalista; enriquecer só o payload do outbox ao cruzar (TL-CR-03) |
| Sanitizadores (distintos) | `audit/services.py:120-142` (genérico, não bloqueia cliente_id, preserva UUID) vs `ordens_servico/event_helpers.py:42-65` (de OS, bloqueia cliente_id no WORM) | enriquecer outbox usa o caminho genérico; WORM da OS continua protegido |
| Preço carimbado na OS | `domain/operacao/os/entities.py:45-46,70`; `repositories.py:85-86` | `OSSnapshot.valor_total`; `AtividadeSnapshot.valor_unitario_snapshot` (banco, não evento) |
| Envelope `orcamento.aprovado` (molde PII-safe) | `domain/comercial/orcamentos/transicoes.py:190-318` | publica `cliente_id`+`cliente_referencia_hash`+`cliente_key_id`+`valor_total` (string decimal) |
| Evento `fiscal.nfse_emitida` | `fiscal/views.py:268-281`; `acoes_canonicas.py:321-326` | `{nfse_id, valor_centavos, perfil_no_evento, cliente_referencia_hash, ...}` — valor sim, cliente é hash |
| Perfil no envelope (INT-03) | `audit/event_helpers.py:188,245-269` | `envelope["perfil_no_evento"]` lido na publicação; consumer lê daí, não de current_setting (TL-CR-07) |
| Perfil regulatório (síncrono) | `src/infrastructure/authz/perfil_tenant_helper.py:44,106` | `obter_perfil_tenant_corrente() -> str`; `tenant_perfil_e(perfis) -> (bool, reason)` (fail-closed 50ms) |
| Idempotência REST | `src/infrastructure/idempotencia/services_idempotencia.py:122` | `avaliar_chave_idempotencia(...)` + helper `_aplicar_idempotencia(request, *, payload_fingerprint)` |
| Idempotência consumer (bus) | `src/infrastructure/bus/consumer_base.py:110-155` (`@consumer_idempotente`) | INSERT ON CONFLICT em `consumer_idempotencia` por `(consumer_id, event_id)` + side-effect na mesma tx |
| Evento outbox + enum canônico | `audit/event_helpers.py:71,112`; `acoes_canonicas.py:462-473`; `audit/migrations/0011_bus_outbox.py:31-35` | `publicar_evento(... outbox=True)`; `assert_acao_canonica` exige ação em `ACOES_CANONICAS`; CHECK só sintático lowercase |
| Numeração GAP_LESS | `application/configuracoes_sistema/serie.py`; `infrastructure/.../repositories.py:195,287` | `regime_numeracao_do_tipo` (fatura=GAP_LESS); `reservar_numero`+`confirmar_numero` advisory lock |
| ReferenciaPIIAnonimizavel | `src/domain/shared/value_objects.py:258` | `{uuid_atual_id?, hash_original (HMAC), key_id}` |
| Endpoint público (molde webhook) | orçamentos D-ORC-19 + `equipamentos/views_qr_publico.py` | token/id resolve tenant SEM RLS (`SECURITY DEFINER`/índice), depois `run_in_tenant_context`; fiscal NÃO tem webhook |
| HMAC PII / anti-PII texto | `src/infrastructure/calibracao/lgpd.py`; `INV-CAL-TXT-001` (`calibracao/models.py` + REGRAS) | `derivar_*_hash(...)`; validação anti-PII existente; KMS/A3 real = GATE |
| Hook fronteira de provider (molde) | `.claude/hooks/fiscal-provider-import-fronteira-check.sh` | bloqueia import de SDK fora de `infrastructure/<modulo>/` |
