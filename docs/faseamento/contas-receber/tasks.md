---
owner: agente-ia
revisado-em: 2026-06-15
proximo-review: 2026-09-15
status: draft
diataxis: reference
audiencia: [agente, auditor]
frente: contas-receber
tipo: tasks
relacionados:
  - docs/faseamento/contas-receber/plan.md
  - docs/faseamento/contas-receber/spec.md
---

# Tasks — frente `contas-receber` (T-CR-NNN, derivado do plan)

> Status em tempo real: `[ ]` pendente · `[x]` feito (com data/onda/testes). Numeração em dezenas por fatia,
> com saltos para inserir tarefas intermediárias (molde orçamentos). Refs apontam para D-CR-N / INV / AC / R / TL-CR.

## Fatia 1a — domínio puro (`src/domain/contas_receber/`) — ✅ DONE 2026-06-15 (81 testes; ruff+mypy limpos; revisão crítica Opus)

> **Achado da revisão (resolver na Fatia 2):** `calcular_valor_atualizado` NÃO aplica o desconto-pontualidade
> ANTES do vencimento (AC-CR-004-2) — a fórmula do desconto não foi especificada na spec. O job só REMOVE o
> desconto após o vencimento; a aplicação do desconto na leitura pré-vencimento fica para o use case da Fatia 2
> (cravar a fórmula: sobre valor_original? até N dias antes? — decidir com o caso de uso de emissão/leitura).

- [x] **T-CR-010** ✅ `enums.py` — `EstadoTitulo`/`MeioCobranca`/`CategoriaReceita`/`OrigemTitulo`/`OrigemPagamento` (`str,Enum`). Ref: D-CR-3/5.
- [x] **T-CR-011** `entities.py` — `Titulo`/`Parcela`/`Pagamento`/`OverrideBloqueio` (`frozen+slots`). Ref: D-CR-2; spec §4.
- [x] **T-CR-012** `transicoes.py` — `_TRANSICOES` Mapping + `validar_transicao` + `pode_cancelar(titulo, pagamentos)`. Ref: D-CR-3.
- [x] **T-CR-013** `juros.py` — `calcular_valor_atualizado(titulo, pagamentos, data, regra)` sobre **saldo** (`valor_original - sum(pagamentos)`). Ref: D-CR-4; TL-CR-10/R12; INV-026.
- [x] **T-CR-014** `grace.py` + `categoria.py` + `conversao.py` — `grace_period_por_perfil` (45/20/30/7); `categoria_por_perfil_evento`/`categoria_permitida` (RBC só A); `valor_decimal_str_para_dinheiro` (conversor único — R9). Ref: D-CR-5/9/23.
- [x] **T-CR-015** `portas.py` + `mock_provider.py` + `value_objects.py` + `erros.py` — `PaymentGatewayProvider`/`TituloRepository` Protocols; `MockPaymentGatewayProvider` (4 modos, `gateway_id` determinístico); VOs de resultado; hierarquia de erros. Ref: D-CR-7; spec §4.
- [x] **T-CR-016** `tests/test_contas_receber_dominio_fatia1a.py` — máquina estados (happy+unhappy), juros sobre saldo (parcial), grace por perfil, conversão (bordas `"0.10"`/`"100.005"`/zero), categoria mismatch, Mock 4 modos, Protocol runtime_checkable. **Verificação 1a** (`--no-cov`).

## Fatia 1b — schema PG (`src/infrastructure/contas_receber/`) — ✅ DONE 2026-06-15 (22 testes; drill 41/41 PASS; ruff+mypy limpos)

- [x] **T-CR-020** ✅ `apps.py` (`label=contas_receber`; `ready()` com `# TODO Fatia 3: registrar consumers cross-módulo` — PLAN-CR-02) + `models.py` (4 models achatados; `_choices(enum)`; `revision`; `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado` — R6; CHECK convenio_pix — INV-FIN-GW-002). Ref: D-CR-1/17; spec §4.
- [x] **T-CR-021** ✅ `mappers.py` + `repositories.py` (`DjangoTituloRepository` implementa Protocol). Ref: D-CR-1.
- [x] **T-CR-022** ✅ migration `0001_initial` (CreateModel + constraints + índices). Ref: D-CR-17.
- [x] **T-CR-023** ✅ migration `0002_rls_policies` (ENABLE+FORCE+4 policies padrão v2). Ref: D-CR-17; INV-TENANT-*.
- [x] **T-CR-024** ✅ migration `0003_triggers_worm` (block-delete + worm_check; `Pagamento`/`OverrideBloqueio` INSERT-only; `data_baixa`/`cancelado_em` one-shot; trigger `perfil_no_evento` fallback `COALESCE` — R4). Ref: D-CR-6/17; INV-CR-PAGAMENTO-WORM.
- [x] **T-CR-025** ✅ migration `0004_grants_app_user` + `0005_seed_authz` (ações `contas_receber.*` × papéis). Ref: D-CR-13/17.
- [x] **T-CR-025b** ✅ `audit/acoes_canonicas.py` — bloco `ACOES_CONTAS_RECEBER` (8 slugs lowercase) + união `ACOES_CANONICAS` + `os.faturada`/`os.paga` em `ACOES_OS` (R2). **Sem migration de CHECK** (sintático). Ref: D-CR-14; TL-CR-02/11.
- [x] **T-CR-026** ✅ `management/commands/validar_contas_receber.py` — drill estrutural 41/41 PASS (RLS, policies, UNIQUE, triggers, grants). Ref: plan §3.
- [x] **T-CR-027** ✅ `tests/test_contas_receber_schema_fatia1b.py` — 22 testes PASS: RLS+FORCE+4 policies, cross-tenant, block-delete, probatório imutável, `Pagamento` INSERT-only, UNIQUE os_id, CHECK convenio. **Verificação 1b** (`--reuse-db transaction=True`).

## Fatia 2 — use cases + REST (núcleo autossuficiente; NÃO toca módulo fechado)

> **Fatiada em 2a (manual) + 2b (gateway/webhook/override).** **2a ✅ DONE** — 13 testes API; reconciliou
> Protocol↔adapter, removeu DRF dos use cases. **2b ✅ DONE 2026-06-15** — 15 testes (webhook+gateway);
> emitir-boleto/pix Mock + webhook público (SECURITY DEFINER `resolver_cr_titulo_por_gateway` migration 0006 +
> HMAC + idempotência dupla + anti-oráculo 401) + override (anti-PII 4 regex, 5/mês, WORM). Revisão Opus
> corrigiu slug não-canônico do incidente HMAC (`contas_receber.webhook_hmac_rejeitado` — antes falhava silencioso).
> Débitos p/ P9: snapshot webhook usa valor_original (sem juros); desconto-pontualidade pré-vencimento sem fórmula.

- [x] **T-CR-030** ✅ (2a) `criar_titulo_manual.py` — cliente+valor+vencimento+categoria perfil-aware (validação no use case — ADR-0073); perfil síncrono. Ref: D-CR-5/6/13; AC-CR-001 (manual); INV-FIN-PERFIL-001.
- [x] **T-CR-031** ✅ (2b) `emitir_boleto.py` + `emitir_pix_recorrente.py` — `provider.criar_cobranca`/`criar_recorrencia`; valida convenio (recorrente); 503+`gateway_indisponivel`; recorrente só 1º título. Ref: D-CR-7; AC-CR-002; TL-CR-09; INV-FIN-GW-002.
- [x] **T-CR-032** ✅ (2a) `baixar_titulo_manual.py` — `Pagamento` + snapshot M-FIN-002 + transição + `contas_receber.pago`. Ref: D-CR-3/4; AC-CR-003/009.
- [x] **T-CR-033** ✅ (2b) `processar_webhook_pagamento.py` — HMAC + idempotência dupla (`gateway_event_id` + estado); baixa ≤60s; tudo em 1 `transaction.atomic` (R10). Ref: D-CR-8; AC-CR-003; INV-FIN-GW-001.
- [x] **T-CR-034** ✅ `cancelar_titulo.py` ✅ (2a, 409 se parcial) + `override_bloqueio.py` (2b — papel gerente; justificativa≥100 anti-PII — R13; contador 5%/mês; WORM). Ref: D-CR-3/10; AC-CR-010-5; INV-CR-OVERRIDE-*.
- [x] **T-CR-035** ✅ `serializers.py` + `views.py` (`ContasReceberViewSet`) — ✅ (2a) actions criar/baixar-manual/cancelar/retrieve/list (idempotência REST, advisory lock, ACTION_MAP, perfil server-side); 2b adiciona emitir/override/webhook. Ref: D-CR-13.
- [x] **T-CR-036** ✅ (2b) `views.py` (`ContasReceberWebhookView` público) + `urls.py` — tenant via `SECURITY DEFINER`/índice + anti-oráculo (R7); molde D-ORC-19. Ref: D-CR-8; R-CR-NOVO-1.
- [x] **T-CR-037** ✅ (2a+2b: fatia2a + webhook_fatia2b + gateway_fatia2b) — criar A+RBC(201)/B+RBC(403)/atendente(403); Idempotency-Key; emitir boleto mock; pix sem convenio(422); timeout(503); webhook HMAC ok/inválido(401)/replay(200 sem 2º Pagamento); cancelar parcial(409); override sem papel(403)/curto(422); cross-tenant(404). **Verificação 2**.

## Fatia 3 — integrações cross-módulo (toca OS/clientes FECHADOS — R14) + auto-faturamento + INVs

### 3a — Auto-faturamento de OS (GATE-CR-OS-EVENTO)
- [ ] **T-CR-040** Enriquecer payload do **outbox** de `os.concluida` (`ordens_servico/repositories.py:660`) com cliente (`ReferenciaPIIAnonimizavel`)+`valor_total`; `payload_data` WORM intacto (R3). Skip hook legado justificado. Ref: D-CR-12; TL-CR-03.
- [ ] **T-CR-041** `criar_titulo_a_partir_de_os.py` + consumer `@consumer_idempotente` — perfil do envelope (R4); conversão valor (R9); tenant suspenso não cria (R11); idempotente por `os_id` (R6); publica `titulo_emitido`+`os.faturada` (R2). Consumer `os.reaberta` cancela título sem pagamento. Ref: D-CR-12; AC-CR-001-1; INV-CR-OS-TITULO-UNICO/FIS-CR-001.
- [ ] **T-CR-042** Baixa de título de OS publica `os.paga` (R2). Ref: TL-CR-02.

### 3b — Inadimplência (GATE-CR-INADIMPLENCIA-RECONCILIA)
- [ ] **T-CR-043** `inadimplencia_adapter.py` — implementa `InadimplenciaSource` (PULL — R1); aplica `grace_period_inadimplencia_por_perfil`; `InadimplenciaItem`+`perfil`/`grace_perfil` **como Optional com default seguro** (PLAN-CR-01 — extensão do dataclass em `clientes` é toque em módulo fechado; atualizar `SourceListaInterim` para entregar os campos, senão job quebra em deploy parcial). Substitui source interino no wiring `clientes` (`inadimplencia.py:get_source()`, parametrizar via settings) — toca clientes (R14). Ref: D-CR-9; TL-CR-01/PLAN-CR-01; INV-FIN-GRACE-PERFIL-001.
- [ ] **T-CR-044** `notificar_inadimplencia.py` — `send_mail` D+30/D+45 perfil A (R8); payload rico (`titulos_vencidos[]`+`data_bloqueio_prevista`+`canal_regularizacao_url` — ADV-CR-01); job. **GATE-CR-NOTIF-D30-PERFIL-A** (gate de ativação da flag). Ref: D-CR-9; AC-CR-010-1b; RBC-CR-01.

### 3c — Desbloqueio (GATE-CLI-6 — toca clientes — R14/R5)
- [ ] **T-CR-045** Query `tem_outra_vencida_em_aberto(cliente_id)` exposta por CR + consumer novo em `clientes` de `contas_receber.pago` → encerra `ClienteBloqueio` + publica `cliente.desbloqueado` (idempotente; parcial mantém). Ref: D-CR-11; AC-CR-006; TL-CR-05; INV-FIN-REATIV-001.

### 3d — INVs + hooks (família INV-FIN-* volta ao mestre)
- [ ] **T-CR-046** Cravar em `REGRAS-INEGOCIAVEIS.md` (seção `## INV-FIN-*`): GW-001/002, PERFIL-001, GRACE-PERFIL-001, SNAPSHOT-PERFIL-001, REATIV-001, INAD-001 + INV-CR-OS-TITULO-UNICO/PAGAMENTO-WORM/OVERRIDE-WORM/OVERRIDE-ANTI-PII/WEBHOOK-PAYLOAD-MINIMO; reconciliar INV-FIS-CR-001/INV-CAL-FIN-001. Atualizar `invariantes-futuras.md` (ponteiro histórico). Ref: spec §5; R14.
- [ ] **T-CR-047** Hooks: `policy-tenant-vs-cliente.sh` (INV-FIN-INAD-001), `cr-provider-import-fronteira-check.sh`, `cr-perfil-server-side-check.sh` (molde fiscal). Registrar em `pre-commit-manifest.tsv`. Ref: spec §5; INV-FIN-INAD-001.
- [ ] **T-CR-048** `tests/test_contas_receber_autofatura_fatia3.py` + `tests/test_contas_receber_inadimplencia_fatia3.py` — auto-fatura `os.concluida` enriquecida (perfil do envelope; perfil-mudou→snapshot do evento — R4); replay+os.reaberta (R6); tenant suspenso (R11); grace por perfil; notificação; desbloqueio happy+parcial (R5); hooks verdes. **Verificação 3** + `_test-runner.sh`.

## P8/P9 — fechamento

- [ ] **T-CR-060** P8: ADR reconciliação (molde ADR-0083 — Titulo×Fatura + gatilho OS×Certificado.Emitido, emenda ADR-0043/INV-CAL-FIN-001) + `matriz-reconciliacao.md` (AC↔código↔teste; INV↔teste; ata P9) + `STATUS-GERADO` (`status-projeto.sh --check`) + frontmatters `stable` + atualizar `plano-dependencia-sistema.md` (nível 5 CR FECHA receita). Ref: plan §6; GATE-CR-CERT-RECONCILIA.
- [ ] **T-CR-061** P9: mutirão auditores roteados (seguranca/qualidade/llm-correctness/performance/observabilidade/idempotencia + conformidade-lgpd; produto no merge). MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial. Ref: plan §6.

## Pré-condições antes de iniciar T-CR-040+ (Fatia 3 — cross-módulo)

- 🔲 Revisão do plan (plan §7): tech-lead confirma sequenciamento 3a/3b/3c + flag canônica + namespace eventos OS.
- 🔲 consultor-rbc confirma inexistência de certificado faturável fora de OS (TL-CR-08) — antes do P8.
