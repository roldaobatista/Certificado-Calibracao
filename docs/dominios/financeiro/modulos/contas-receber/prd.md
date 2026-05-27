---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: contas-receber
dominio: financeiro
diataxis: explanation
audiencia: agente
relacionados:
  - docs/dominios/financeiro/modulos/fiscal/prd.md
  - docs/dominios/comercial/modulos/clientes/prd.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - docs/adr/0015-lifecycle-tenant.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0043-calibracao-faturamento-bloqueio-inadimplencia.md
  - docs/adr/0050-gateway-pagamento-pix-recorrente.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0052-pix-recorrente-bcb-1071.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
historico:
  - 2026-05-23 — versão draft inicial Wave A (US-CR-001..009 + ADRs 0050/0051/0052).
  - 2026-05-27 — Onda PRE-A.3 BATCH B1 saneamento perfil ADR-0067 (AC binário GIVEN-WHEN-THEN + matriz perfil × régua/retenção + emenda ADR-0043 grace D+45/20/30/7 + status promovido para stable).
---

# PRD — Contas a Receber

## 1. O que é

Geração, emissão, cobrança e baixa de títulos a receber do tenant. Recebe gatilho de Operação (`OS.Concluida`) e Metrologia (`Certificado.Emitido` — ADR-0043) e Comercial (contrato recorrente); produz boleto/PIX/cartão via porta `PaymentGatewayProvider`; concilia pagamento; ativa régua de cobrança quando atrasa; bloqueia operação dependente em inadimplência dura (perfil-aware — ADR-0067 + ADR-0043).

## 2. Por que existe

Dor universal #11 (cobrança/inadimplência) — tenant perde 8-15% do faturamento por falta de régua sistemática. Sem este módulo, OP7 (NFS-e) emite mas ninguém cobra; cert metrológico vira "trabalho de graça". Em perfil A (RBC acreditado) bloqueio agressivo é catastrófico (perda janela CGCRE > recuperação de R$); em perfil D bloqueio agressivo é aceito.

## 3. Personas

**Persona dominante:** P-FIN-01 (financeiro do tenant — emite/baixa títulos diariamente).
Outras: P-FIN-02 (dono — vê inadimplência), P-COM-02 (vendedor — vê o que recebeu pra liberar comissão), P-OP-05 (cliente final — paga via portal). Detalhes em `../personas.md`.

## 3.1 Perfil regulatório (ADR-0067)

> **Matriz feature × perfil canônica:** `docs/conformidade/comum/matriz-feature-perfil.md`.
>
> Predicate canônico do módulo: **`grace_period_inadimplencia_por_perfil(tenant_id) -> int`** (declarado pela emenda ADR-0043). Lê `Tenant.perfil_regulatorio` via ContextVar `perfil_tenant_context` (Sprint 2 SAN-PERFIL-TENANT). Fail-closed timeout 50ms.

| Feature | Perfil A — RBC acreditado | Perfil B — Rastreável | Perfil C — Em preparação | Perfil D — Comercial puro |
|---|---|---|---|---|
| **Grace period inadimplência dura (ADR-0043 emenda)** | D+45 (CGCRE risk > recuperação R$) — notificação D+30/D+45 obrigatória | D+20 | D+30 (igual A em vigência, sem CGCRE risk) | D+7 (bloqueio agressivo aceito) |
| **Override A3 do dono Aferê** | Até D+90 com A3 + justificativa ≥100 chars + audit WORM | Até D+90 | Até D+90 | Até D+90 |
| **Régua de cobrança lembrete** (Wave B) | D-7, D-3, D-0, D+3, D+10, D+20, D+30, D+45 | D-3, D-0, D+3, D+10, D+20 | D-7, D-3, D-0, D+3, D+10, D+20, D+30 | D-3, D-0, D+3, D+7 |
| **Retenção registros pagamento (matriz §retenção)** | 25a (preserva contexto ISO 8.4) | 25a recomendado | 25a | 5a (Receita) + anonimização agressiva |
| **Categoria receita `CALIBRACAO_RBC`** | ✅ DISPONÍVEL | ❌ DESABILITADO (uso indevido → fraude documental) | ❌ DESABILITADO | ❌ DESABILITADO |
| **Categoria receita `CALIBRACAO_NAO_RBC`** | ⚪ Opcional | ✅ DISPONÍVEL | ✅ DISPONÍVEL | ⚪ Opcional |
| **Categoria receita `CALIBRACAO_BASICA` (declaração)** | ❌ DESABILITADO | ⚪ Opcional | ⚪ Opcional | ✅ DISPONÍVEL |

## 4. Escopo (Wave A)

- Gerar título a partir de OS concluída, **`AtividadeDaOS` concluída** (ADR-0051) ou contrato OU `Certificado.Emitido` (ADR-0043).
- Emitir boleto + PIX + **PIX recorrente** (BCB 1.071/2024 — ADR-0052) + cartão recorrente via porta `PaymentGatewayProvider` (ADR-0050).
- Parcelamento simples (até N parcelas iguais).
- Aplicação automática de juros + multa + desconto pontualidade conforme regra do tenant.
- Baixa manual + baixa automática via webhook gateway (HMAC + idempotência — INV-FIN-GW-001).
- Listagem com filtro (status, vencimento, cliente, **`categoria_receita`** — A-FIN-002 — válido por perfil §3.1).
- **Reativação de cliente bloqueado** quando última fatura vencida é quitada (INV-FIN-REATIV-001 / GATE-CLI-6).
- **Bloqueio dura por inadimplência perfil-aware** (ADR-0043 emenda — `grace_period_inadimplencia_por_perfil`).
- **Snapshot `perfil_no_evento`** em `ContasReceber` cravado no INSERT (ADR-0067 §3).

### Diferenciação tenant vs cliente do tenant (INV-FIN-INAD-001 / C-FIN-002)

- **Inadimplência do cliente do tenant:** política livre por tenant. Default sugerido perfil-aware (§3.1). Configurável via `tenant_inadimplencia_config`.
- **Inadimplência do tenant Aferê:** módulo `billing-saas` (ADR-0015). NÃO confundir com a anterior.
- Nenhuma policy/código cruza os dois. Hook `policy-tenant-vs-cliente.sh` valida.

## 5. Escopo Wave B (OP11)

- Régua de cobrança configurável completa (lembrete D-7, D-3, D-0, D+3, D+10, D+30 — escalonamento por perfil).
- Disparo via WhatsApp + e-mail (via `OmniChannelProvider` + `EmailTemplateProvider` ADR-0060).
- Aging em faixas.
- Painel inadimplência > 30 dias.
- **Conciliação OFX (A-FIN-003)** — explicitamente Wave B.
- **Marketplace produtor (M-FIN-003)** — receita de marketplace é Wave B.

## 6. Não-objetivos (Wave A — explícitos)

- Antecipação de recebíveis / factoring.
- Conciliação Open Finance bidirecional (Wave B/V2 via Pluggy).
- Múltiplos gateways simultâneos (1 provider ativo por tenant; multi-provider Wave B).
- Negociação automatizada com desconto progressivo.
- DRE / fluxo projetado (vem do OP12 — painel do dono).
- Cobrança judicial / protesto (V2 com integração externa).
- **Antecipação de boleto via banco** — V2 (exige integração Open Banking).
- **Conciliação bancária OFX/CSV** — Wave B.

## 7. User Stories (AC binários GIVEN-WHEN-THEN)

### US-CR-001 — Gerar título a partir de OS concluída ou Certificado emitido

**Persona:** sistema (consumer de `OS.Concluida` + `Certificado.Emitido` — ADR-0043).

- **AC-CR-001-1 (happy OS):** GIVEN evento `OS.Concluida{os_id, valor_centavos, cliente_id, tenant_id}` publicado AND `Tenant.perfil_regulatorio` resolvido via ContextVar, WHEN consumer `criar_titulo_a_partir_de_os_handler` recebe, THEN cria `ContasReceber{titulo_id, valor, vencimento=os.concluida_em + cliente.prazo_dias, status: TituloEmitido, os_id_origem, cliente_id, categoria_receita, perfil_no_evento}` em ≤ 5s AND publica `ContasReceber.TituloEmitido{titulo_id, perfil_no_evento}` AND idempotente por `os_id` (IDEMP-001).
- **AC-CR-001-2 (happy Certificado — ADR-0043):** GIVEN evento `Certificado.Emitido{certificado_id, valor_centavos, cliente_id, tenant_id, perfil_emissor_no_momento}` publicado, WHEN consumer `criar_titulo_a_partir_de_certificado_handler` recebe, THEN cria `ContasReceber` com `categoria_receita` derivada do `perfil_emissor_no_momento` (A → `CALIBRACAO_RBC`; B/C → `CALIBRACAO_NAO_RBC`; D → `CALIBRACAO_BASICA`) AND idempotente por `certificado_id`.
- **AC-CR-001-3 (cross-tenant):** GIVEN consumer recebe evento de tenant A, WHEN tenta criar título referenciando cliente de tenant B, THEN bloqueia hard com 422 anti-oracle (`INV-TENANT-001`).
- **AC-CR-001-4 (snapshot perfil ADR-0067 §3):** GIVEN INSERT em `contas_receber`, WHEN trigger BEFORE INSERT roda, THEN preenche `perfil_no_evento` lendo `current_setting('app.perfil_tenant')` se NULL — cravado e imutável pós-INSERT.
- **Teste:** `tests/test_contas_receber_us_001*.py`.

### US-CR-002 — Emitir boleto/PIX/PIX recorrente em 1 clique (porta PaymentGatewayProvider)

**Persona:** P-FIN-01.

- **AC-CR-002-1 (happy boleto):** GIVEN título em `TituloEmitido` AND tenant tem `PaymentGatewayProvider` configurado (default Asaas — ADR-0050), WHEN usuário POST `/api/v1/contas-receber/{id}/emitir-boleto`, THEN sistema chama porta `provider.emitir_boleto(payload)`, recebe `{boleto_id, linha_digitavel, pdf_url, qr_code_pix}`, persiste, retorna 201 em p95 ≤ 3s AND publica `ContasReceber.BoletoEmitido{titulo_id}`.
- **AC-CR-002-2 (PIX recorrente — ADR-0052 INV-FIN-GW-002):** GIVEN título com `meio=pix_recorrente`, WHEN POST `/api/v1/contas-receber/{id}/emitir-pix-recorrente`, THEN sistema valida `convenio_pix_id NOT NULL` (BCB 1.071/2024) AND chama provider AND retorna 201 com `{pix_recorrente_id, qr_code_estatico, vigencia_inicio, vigencia_fim}`.
- **AC-CR-002-3 (provider down):** GIVEN provider gateway timeout > 5s, WHEN POST, THEN sistema retorna 503 `{erro: "GATEWAY_INDISPONIVEL", retry_em_segundos}` AND publica `ContasReceber.GatewayIndisponivel` (sem criar boleto).
- **Teste:** `tests/test_contas_receber_us_002*.py`.

### US-CR-003 — Pagamento via PIX dispara baixa automática em < 60s

**Persona:** sistema (consumer webhook gateway).

- **AC-CR-003-1 (happy webhook):** GIVEN webhook gateway envia `{evento: "pagamento_confirmado", boleto_id, valor, pago_em}` com header `X-Signature-HMAC`, WHEN consumer `webhook_pagamento_handler` valida HMAC + idempotência `Idempotency-Key: {boleto_id}_{pago_em}` (INV-FIN-GW-001), THEN aplica baixa em ≤ 60s do `pago_em`, atualiza `ContasReceber.status=Pago`, persiste `valor_atualizado_snapshot_em_pagamento` (M-FIN-002), publica `ContasReceber.Pago{titulo_id, valor, pago_em, perfil_no_evento}`.
- **AC-CR-003-2 (HMAC inválido):** GIVEN webhook com HMAC inválido, WHEN consumer valida, THEN rejeita com 401 + log incidente `Seguranca.WebhookHMACInvalido` + publica métrica.
- **AC-CR-003-3 (idempotência replay):** GIVEN mesmo `Idempotency-Key` chega 2x em 24h, WHEN consumer processa, THEN baixa aplicada 1 única vez (segunda chamada retorna 200 sem efeito colateral).
- **Teste:** `tests/test_contas_receber_us_003*.py`.

### US-CR-004 — Título vencido aplica juros/multa + desconto pontualidade

**Persona:** sistema (job diário).

- **AC-CR-004-1 (vencimento + juros):** GIVEN título com `vencimento < today` AND `status=TituloEmitido`, WHEN job `aplicar_juros_multa_diario` roda 03:00 BRT, THEN calcula juros (1% a.m. proporcional) + multa (2% única vez no D+1) conforme `tenant.regra_juros_multa`, atualiza `valor_atualizado`, NÃO altera `valor_original` (INV-026 preço não-retroativo).
- **AC-CR-004-2 (desconto pontualidade — cai após vencimento):** GIVEN título com `desconto_pontualidade_pct > 0` AND `vencimento < today`, WHEN job roda, THEN remove desconto + recalcula `valor_atualizado`.

### US-CR-005 (Wave B) — Régua envia lembrete WhatsApp/e-mail perfil-aware

**Persona:** sistema (consumer régua).

- **AC-CR-005-Wave-B-1:** GIVEN título com `vencimento = today + N_dias` AND `N_dias ∈ régua_do_perfil` (§3.1 — perfil A: -7/-3/0/+3/+10/+20/+30/+45; perfil D: -3/0/+3/+7), WHEN job `régua_cobrança_diário` roda, THEN dispara `OmniChannelProvider.enviar(WhatsApp)` + `EmailTemplateProvider.enviar` (ADR-0060) AND publica `ContasReceber.LembreteEnviado{titulo_id, canal, dia_relativo}`.

### US-CR-006 (C-FIN-001 / GATE-CLI-6) — Desbloqueio de cliente ao quitar última fatura vencida

**Persona:** sistema (consumer `ContasReceber.Pago`).

- **AC-CR-006-1 (happy desbloqueio):** GIVEN cliente com `status_bloqueio=BLOQUEADO_INADIMPLENCIA` AND última fatura vencida acabou de ser paga (`ContasReceber.Pago` consumido) AND nenhuma outra fatura vencida no cliente, WHEN consumer `verificar_desbloqueio_cliente` roda, THEN publica `Cliente.Desbloqueado{cliente_id, motivo: "pagamento_quitou_inadimplencia", titulo_id_quitado, perfil_no_evento}` em ≤5min AND atualiza `status_bloqueio=ATIVO` (INV-FIN-REATIV-001 / GATE-CLI-6).
- **AC-CR-006-2 (ainda há outras vencidas):** GIVEN cliente paga 1 fatura mas há outras vencidas, WHEN consumer roda, THEN NÃO publica desbloqueio.
- **AC-CR-006-3 (idempotência):** GIVEN evento `ContasReceber.Pago` chega 2x, WHEN consumer processa, THEN publica `Cliente.Desbloqueado` apenas 1x.

### US-CR-007 (A-FIN-001) — Emitir cobrança via porta PaymentGatewayProvider

> Coberto por AC-CR-002.

### US-CR-008 (A-FIN-002) — Classificar receita por `categoria_receita` perfil-aware

**Persona:** P-FIN-01 / sistema.

- **AC-CR-008-1 (validação por perfil):** GIVEN tenant `perfil != A`, WHEN tenta criar título com `categoria_receita=CALIBRACAO_RBC`, THEN predicate da matriz §3.1 rejeita com 403 `{erro: "CATEGORIA_RECEITA_EXIGE_PERFIL_A"}` AND publica `ContasReceber.CategoriaReceitaBloqueada` (defesa anti-fraude documental fiscal).
- **AC-CR-008-2 (perfil D + declaração):** GIVEN tenant `perfil=D`, WHEN título derivado de `Certificado.Emitido` com `tipo=RELATORIO_AFERICAO`, THEN categoria automaticamente = `CALIBRACAO_BASICA`.

### US-CR-009 (M-FIN-002) — Pagamento grava `valor_atualizado_snapshot_em_pagamento`

> Coberto por AC-CR-003-1.

### US-CR-010 — Bloqueio dura por inadimplência perfil-aware (ADR-0043 emenda)

**Persona:** sistema (job + composição com `comercial/clientes` US-CLI-bloqueio).

- **AC-CR-010-1 (grace period perfil A):** GIVEN cliente tenant `perfil=A` com fatura `vencimento + 45d ≤ today` AND `status != Pago`, WHEN job `verificar_inadimplencia_dura` roda 03:00 BRT, THEN publica `ContasReceber.InadimplenciaDuraAtingida{cliente_id, titulo_id, dias_vencido, perfil}` AND consumer `comercial/clientes` bloqueia novos orçamentos/OS (INV-CLI-BLOQ-001).
- **AC-CR-010-1b (notificação D+30 e D+45 perfil A):** GIVEN cliente tenant `perfil=A` com fatura `vencimento + 30d ≤ today < vencimento + 45d`, WHEN job roda, THEN dispara aviso preventivo D+30 e D+45 antes do bloqueio efetivo (obrigatório ADR-0043 emenda — CDC art. 6º III/IV).
- **AC-CR-010-2 (perfil B grace D+20):** GIVEN cliente tenant `perfil=B`, WHEN `vencimento + 20d ≤ today`, THEN bloqueio.
- **AC-CR-010-3 (perfil C grace D+30):** análogo perfil A em vigência mas sem notificação CGCRE.
- **AC-CR-010-4 (perfil D grace D+7):** GIVEN tenant `perfil=D`, WHEN `vencimento + 7d ≤ today`, THEN bloqueio agressivo aceito.
- **AC-CR-010-5 (override A3 dono Aferê — qualquer perfil):** GIVEN dono Aferê (Roldão) precisa estender grace caso-a-caso até D+90, WHEN POST `/api/v1/contas-receber/{id}/override-bloqueio` com `justificativa ≥100 chars + A3`, THEN sistema persiste `OverrideBloqueio{titulo_id, novo_prazo_max_dias, justificativa, a3_signature_id, perfil_no_evento}` em audit WORM AND adia bloqueio até `novo_prazo_max_dias`.
- **AC-CR-010-6 (cross-tenant)**: tentativa de override em tenant alheio → 404 anti-oracle.
- **Teste:** `tests/test_contas_receber_us_010*.py`.

## 8. NFR

- Emissão boleto/PIX < 3s p95 (depende do provider gateway).
- Webhook gateway → baixa < 60s p95.
- Idempotência obrigatória (gateway pode reenviar webhook — INV-FIN-GW-001).
- Disponibilidade: 99,9% (receita do tenant depende disso).

## 8.1 Métricas inline (Wave A)

> Detalhe completo em `metricas.md`. Resumo:

- **Taxa de baixa automática (PIX/webhook) ≥ 92%** — alvo Wave A.
- **Tempo médio cert/OS → título emitido ≤ 30s mediana / p95 ≤ 120s** (INV-FIS-CR-001 + ADR-0043).
- **% títulos com bloqueio executado dentro do grace do perfil = 100%** (defesa CGCRE perfil A + CDC art. 39 V perfil-aware).
- **% override A3 ≤ 5% dos bloqueios/mês** (exceção, não bypass).
- **% clientes desbloqueados em ≤5min do pagamento ≥ 99%** (INV-FIN-REATIV-001 / GATE-CLI-6).

## 9. Invariantes

- **INV-026** — preço não-retroativo: alteração de tabela não recalcula títulos já emitidos.
- **INV-008** — toda emissão/baixa registrada em audit log.
- **INV-FIN-REATIV-001** — `ContasReceber.Pago` da última fatura vencida publica `Cliente.Desbloqueado` ≤5min (GATE-CLI-6).
- **INV-FIN-INAD-001** — inadimplência do cliente do tenant ≠ inadimplência do tenant; políticas não cruzam.
- **INV-FIN-GW-001** — webhook gateway exige HMAC + idempotência.
- **INV-FIN-GW-002** — `meio=pix_recorrente` exige `convenio_pix_id` NOT NULL (BCB 1.071/2024 — ADR-0052).
- **INV-FIN-PERFIL-001** (novo Onda PRE-A.3) — `categoria_receita=CALIBRACAO_RBC` só permitido em `Tenant.perfil_regulatorio='A'`; mismatch = 403 + evento.
- **INV-FIN-GRACE-PERFIL-001** (novo Onda PRE-A.3 — ADR-0043 emenda) — grace period inadimplência dura segue matriz §3.1 (45/20/30/7) lido via predicate `grace_period_inadimplencia_por_perfil`; override A3 até D+90.
- **INV-FIN-SNAPSHOT-PERFIL-001** (novo) — `ContasReceber.perfil_no_evento` cravado no INSERT, imutável (ADR-0067 §3).

## 10. Dependências (ADRs + módulos)

**Módulos:**

- `operacao/os` — fornece `OS.Concluida` (US-CR-001 AC-1).
- `metrologia/certificados` — fornece `Certificado.Emitido` (US-CR-001 AC-2 — ADR-0043).
- `comercial/clientes` — consumer downstream de `Cliente.Desbloqueado` (US-CR-006); fornece `cliente.prazo_dias` + `tenant_inadimplencia_config`.
- `financeiro/fiscal` — opcional: emissão de NFS-e junto com boleto (Wave B).
- `infrastructure/tenant` — fornece `Tenant.perfil_regulatorio` via ContextVar (ADR-0067).
- Provider gateway (default Asaas; Iugu / Pagar.me adapters Wave B).

**ADRs aceitas:**

- **ADR-0015** — lifecycle tenant (etapa 0 coleta perfil; tenant suspenso → US-CR mantém leitura, bloqueia emissão de novo título — ADR-0035).
- **ADR-0023** — OS com Atividades.
- **ADR-0033** — bus idempotência consumer (consumer_idempotencia + dead_letter_events).
- **ADR-0043** — `Certificado.Emitido → ContasReceber` + bloqueio inadimplência (emenda 2026-05-27 grace D+45/20/30/7 perfil-aware).
- **ADR-0050** — `PaymentGatewayProvider` (cartão recorrente, PIX recorrente, boleto). Default Asaas; configurável por tenant.
- **ADR-0051** — propagação ADR-0023 (fatura por `AtividadeDaOS`).
- **ADR-0052** — PIX recorrente BCB 1.071/2024.
- **ADR-0054** — `OutboundWebhookProvider` HMAC.
- **ADR-0060** — `EmailTemplateProvider` (régua US-CR-005 Wave B).
- **ADR-0067** — perfil regulatório do tenant entidade temporal (canônico do predicate).

## 11. Glossário

Ver `glossario.md` + `docs/comum/glossario.md`. Termos canônicos adicionados nesta sanação:

- **Perfil regulatório:** `Tenant.perfil_regulatorio` enum `{A_ACREDITADO_RBC, B_RASTREAVEL, C_EM_PREPARACAO, D_COMERCIAL_PURO}` — fonte única do grace period (ADR-0067).
- **Predicate `grace_period_inadimplencia_por_perfil(tenant_id) -> int`:** função canônica que retorna 45/20/30/7 conforme perfil (ADR-0043 emenda). Lê tenant via ContextVar, jamais payload.
- **ContextVar `perfil_tenant_context`:** variável Python isolada por request (Sprint 2 SAN-PERFIL-TENANT).
- **Snapshot `perfil_no_evento`:** coluna `CHAR(1)` cravada no INSERT de `contas_receber` (ADR-0067 §3) — defesa CGCRE retroativa cl. 8.4.
- **PaymentGatewayProvider:** porta ACL (ADR-0050) — abstração de Asaas/Iugu/Pagar.me.
- **PIX recorrente:** modalidade BCB 1.071/2024 — exige `convenio_pix_id` NOT NULL (ADR-0052 + INV-FIN-GW-002).
- **Override A3 do dono Aferê:** mecanismo de exceção auditada — estende grace até D+90 com assinatura A3 + justificativa ≥100 chars + audit WORM. Não confundir com bypass.

## 12. Como este PRD evolui

- US nova → próximo `US-CR-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança no grace do perfil → emenda ADR-0043 + atualização `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator` valida.
