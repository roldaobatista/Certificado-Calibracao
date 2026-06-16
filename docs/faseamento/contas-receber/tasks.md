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

### 3a — Auto-faturamento de OS (GATE-CR-OS-EVENTO) — ✅ DONE 2026-06-15 (13 testes autofatura + 4 fan-out; ruff+mypy limpos)

> **Achado bloqueante resolvido (FAN-OUT do bus):** o registry de consumers era **1-por-ação**
> (`outbox_worker.py` `_REGISTRY: dict[str, Callable]`), mas `os.concluida` JÁ tinha consumer
> (`ordens_servico` saga de anonimização `handle_os_em_estado_terminal`). Registrar o consumer de CR
> seria engolido pelo `try/except ValueError: pass` → auto-fatura nunca rodaria. **Tech-lead Opus
> validou (APROVA C/ CORREÇÕES).** Solução: `_REGISTRY: dict[str, list]` com fan-out; `registrar_consumer`
> ainda levanta `ValueError` p/ MESMO `fn` (preserva os `try/except` dos `apps.py`, não toca módulos
> fechados) e acumula fns DIFERENTES; `dispatch_event` itera todos. **Atomicidade = TUDO-OU-NADA por
> linha** (A1 resolvido por leitura: `run_in_tenant_context` abre `transaction.atomic`, logo cada
> `@consumer_idempotente` é savepoint da MESMA tx). Seguro hoje (saga = stub/log; auto-fatura =
> escrita transacional). **Dívida rastreável:** isolamento por-consumer (tx independente) é re-review
> quando a saga sair do stub OU surgir consumer com efeito externo (HTTP/e-mail) — doc no docstring de
> `dispatch_event`. Ver [[fan-out-bus-consumers-os-concluida]].
>
> **Decisão técnica (valor):** o outbox carrega `valor_total_centavos` (**int**), não string decimal —
> imune ao sanitizador de auditoria (string ≥8 dígitos casaria regex telefone → `[REDACTED]`) e
> consistente com `titulo_emitido` que já publica `valor_centavos` int. Conversor `valor_decimal_str_para_dinheiro`
> permanece p/ a fronteira de gateway/webhook (string externa). **Valor = `valor_total_atualizado`**
> (INV-OS-FAT-001 / CDC art. 39 — não cobra atividade cancelada), NÃO `valor_total` (a menção da spec
> D-CR-12 a `valor_total` é genérica; o invariante absoluto vence). Vencimento = emissão + **30** (ADR-0043;
> `cliente.prazo_dias` não existe no model → diferido).

- [x] **T-CR-040** ✅ Enriquecer payload do **outbox** de `os.concluida` (`ordens_servico/repositories.py:660`, `if acao_bus == "os.concluida"`) com `cliente_atual_id`+`cliente_referencia_hash`+`cliente_key_id`+`valor_total_centavos`; `payload_data` WORM intacto (R3). Skip hook legado justificado no commit. Ref: D-CR-12; TL-CR-03.
- [x] **T-CR-041** ✅ `criar_titulo_a_partir_de_os.py` + `consumers/os_eventos.py` (`handle_os_concluida`/`handle_os_reaberta` `@consumer_idempotente`) — perfil do envelope (R4); valor centavos int (R9); tenant suspenso → `TenantSuspensoEmissaoBloqueada` dead-letter (R11); idempotente por `os_id` soft+UNIQUE+advisory lock (R6); publica `titulo_emitido`+`os.faturada` (R2). `os.reaberta` cancela sem pagamento / mantém com pagamento (AC-CR-006-2). Registrado em `apps.py:ready()`. Ref: D-CR-12; AC-CR-001-1; INV-CR-OS-TITULO-UNICO/FIS-CR-001.
- [x] **T-CR-042** ✅ Baixa manual de título de OS publica `os.paga` (`views.py` baixar_manual, só quando `PAGO`). Webhook já publicava (Fatia 2b). Ref: TL-CR-02.

### 3b — Inadimplência (GATE-CR-INADIMPLENCIA-RECONCILIA)

> **Fatiada em 3b-1 (adapter) + 3b-2 (notificação).** Parecer advogado (Caminho C — APROVA): e-mail D+30/D+45
> vai ao **cliente final com remetente = TENANT** (Aferê = operador técnico do envio), + **aviso paralelo ao admin**;
> **fail-closed** (perfil A NÃO entra na régua de bloqueio enquanto a notificação não constar enviada — prova de
> envio `notificacao_cliente_enviada`+timestamp); e-mail lido de `Cliente.email` só no envio, NUNCA persistido no
> evento (cliente = `ReferenciaPIIAnonimizavel` no WORM — D-CR-16/19); minimização (só título/valor/venc/canal/o
> que será×não-será bloqueado — D-CR-21). Texto do e-mail + RAT CONGELADOS até GATE-LGPD-RAT-CONSOLIDACAO — código
> construído agora, disparo com PF real aguarda o gate. Reusa enquadramento RAT-06 (lembrete WhatsApp).

- [x] **T-CR-043** ✅ (3b-1, 2026-06-16) `inadimplencia_adapter.py` — `TituloVencidoInadimplenciaSource` (PULL — R1) itera `Titulo` vencido por tenant (`processar_em_contexto_tenant`; materializa lista, sem contexto aninhado); `grace_period_inadimplencia_por_perfil(tenant_id)` lê perfil ATUAL do tenant + `grace_period_por_perfil` (45/20/30/7); entra se `data_vencimento+grace<=hoje`; anonimizado (cliente_atual_id NULL) fora. `InadimplenciaItem`+`perfil`/`grace_perfil` Optional default None (PLAN-CR-01 — extensão em `clientes` FECHADO); `SourceListaInterim` atualizado; `get_source()` parametrizado `settings.INADIMPLENCIA_SOURCE_IMPL` (default "interim"). 10 testes (grace fronteira D+44/D+46, perfil D, anonimizado, interim, parametrização) + 15 regressão clientes verdes. **Adapter só ATIVA com `INADIMPLENCIA_SOURCE_IMPL=contas_receber`; NÃO ativar em prod até 3b-2 (fail-closed CDC) + GATE-CR-NOTIF prontos.** Ref: D-CR-9; TL-CR-01/PLAN-CR-01; INV-FIN-GRACE-PERFIL-001.
- [x] **T-CR-044** ✅ (3b-2, 2026-06-16) `notificar_inadimplencia.py` (use case puro: `marco_de_dias_vencido` D30/D45 + `montar_aviso` texto provisório) + `job_notificar_inadimplencia.py` (command): `send_mail` D+30/D+45 **perfil A** com **remetente = tenant** (Caminho C); e-mail lido de `Cliente.email` só no envio, NUNCA no evento (minimização D-CR-19); evento `contas_receber.inadimplencia_dura_atingida` com payload rico (`titulos_vencidos[]`+`data_bloqueio_prevista`+`canal_regularizacao_url`, cliente como hash) = **aviso ao admin/tenant** (RLS `upt_self_select` impede job-sistema de listar admins por query → evento é o canal); resiliente a falha SMTP. Config `EMAIL_*` via env (`test`=locmem) + `CANAL_REGULARIZACAO_URL` + `INADIMPLENCIA_SOURCE_IMPL` em `base.py`. Template minuta CONGELADA em `docs/conformidade/comum/template-notificacao-inadimplencia-d30.md`. 7 testes (D30/D45 cliente, minimização, perfil B não envia, fora-marco, payload rico, resiliência SMTP). **GATE-CR-NOTIF-D30-PERFIL-A**. Ref: D-CR-9; AC-CR-010-1b; parecer advogado Caminho C.
- [x] **T-CR-044b** ✅ (3b-3, 2026-06-16 — FAIL-CLOSED CDC) Model `NotificacaoInadimplencia` (INSERT-only — RLS v2 + WORM block-update/delete + grants, migration 0007) = prova de envio. Job grava prova SÓ se e-mail enviado com sucesso (prova = aviso REAL); idempotência por `UNIQUE(tenant,titulo,marco)`; marco por JANELA (`>=30`/`>=45` — re-disparo robusto, não perde marco se job falhar 1 dia). Fail-closed no adapter: perfil A NÃO entra na régua de bloqueio sem prova de aviso (demais perfis comunicam via evento — D-CR-22). 22 testes Fatia 3b verdes (10 adapter + 12 notificação/prova/fail-closed/INSERT-only). **`INADIMPLENCIA_SOURCE_IMPL=contas_receber` agora seguro p/ ativar** (fail-closed CDC pronto). Ref: parecer advogado Caminho C (item 3); INV-CR-NOTIF-WORM.

### 3c — Desbloqueio (GATE-CLI-6 — toca clientes — R14/R5) — ✅ DONE 2026-06-16 (9 testes; ruff+mypy limpos)
- [x] **T-CR-045** ✅ `contas_receber/queries_desbloqueio.py` (read-only expostas por CR — `cliente_atual_id_do_titulo` + `tem_outra_vencida_em_aberto`, RLS+filtro tenant defensivo) + `clientes/consumers/contas_receber_eventos.py` (`handle_contas_receber_pago` `@consumer_idempotente`, registrado em `clientes/apps.py:ready()`). Régua: resolve cliente via CR (anonimizado/inexistente → no-op); ainda há vencida em aberto → mantém (AC-CR-006-2; `parcialmente_pago` vencido CONTA); encerra **só** bloqueio `automatico_inadimplencia_90d` (manual não cede a pagamento); publica `cliente.desbloqueado{cliente_id,motivo,titulo_id_quitado,bloqueio_id}`; idempotente (replay + sem bloqueio ativo). **Débito P9 (T-CR-060):** régua de desbloqueio é SEM grace (espelha nome da spec); adapter de bloqueio (3b) aplica grace → assimetria a reconciliar. 9 testes (queries; happy; outra-vencida mantém; parcial mantém; manual não-desfaz; anonimizado no-op; sem-bloqueio no-op; replay idempotente). Toca `clientes` FECHADO (R14 — só `apps.py:ready()` + arquivos NOVOS). Ref: D-CR-11; AC-CR-006; TL-CR-05; INV-FIN-REATIV-001.

### 3d — INVs + hooks (família INV-FIN-* volta ao mestre) — ✅ DONE 2026-06-16
- [x] **T-CR-046** ✅ Cravada seção `## INV-FIN-*` em `REGRAS-INEGOCIAVEIS.md` (molde INV-ORC): GW-001/002, PERFIL-001, GRACE-PERFIL-001, SNAPSHOT-PERFIL-001, REATIV-001, INAD-001 + INV-CR-OS-TITULO-UNICO/PAGAMENTO-WORM/OVERRIDE-WORM/OVERRIDE-ANTI-PII/WEBHOOK-PAYLOAD-MINIMO + INV-FIS-CR-001 (reconciliada) — 6 colunas (ID/regra/base/hook/perfil/consequência), enforcement REAL (migrations/hooks/testes nomeados) + bloco Reusadas/GATEs. Placeholder linha ~789 → "CRAVADA"; `invariantes-futuras.md` → ponteiro histórico (não duplicar). Ref: spec §5; R14.
- [x] **T-CR-047** ✅ 3 hooks (molde fiscal/orc): `cr-perfil-server-side-check.sh` (INV-FIN-PERFIL-001 — perfil nunca do payload), `cr-provider-import-fronteira-check.sh` (INV-FIN-GW-001 — SDK gateway só em infra/contas_receber), `policy-tenant-vs-cliente.sh` (INV-FIN-INAD-001 — operacional cliente não acopla billing-saas). Registrados em `pre-commit-manifest.tsv`; 23 casos no `_test-runner.sh` (8+7+8) verdes; gate anti-órfão + contagens OK. Ref: spec §5; INV-FIN-INAD-001.
- [~] **T-CR-048** PARCIAL — `tests/test_contas_receber_autofatura_fatia3.py` ✅ (13 testes: `os.concluida` cria título A/B, idempotência por `os_id`, tenant suspenso dead-letter, perfil None fail-closed, valor 0 no-op, publica `titulo_emitido`+`os.faturada`, `os.reaberta` cancela/mantém, enriquecimento outbox + INV-OS-FAT-001 valor atualizado, `os.paga` na baixa) + fan-out no `tests/test_outbox_worker_t_cli_110.py` ✅ (4 testes). **Falta** `tests/test_contas_receber_inadimplencia_fatia3.py` (3b): grace por perfil na fronteira (D+44 não entra / D+46 entra); notificação D+30/D+45; desbloqueio happy+parcial (R5); hooks novos. **Verificação 3** completa + `_test-runner.sh` no fim da Fatia 3.

## P8/P9 — fechamento

- [ ] **T-CR-060** P8: ADR reconciliação (molde ADR-0083 — Titulo×Fatura + gatilho OS×Certificado.Emitido, emenda ADR-0043/INV-CAL-FIN-001) + `matriz-reconciliacao.md` (AC↔código↔teste; INV↔teste; ata P9) + `STATUS-GERADO` (`status-projeto.sh --check`) + frontmatters `stable` + atualizar `plano-dependencia-sistema.md` (nível 5 CR FECHA receita). Ref: plan §6; GATE-CR-CERT-RECONCILIA.
- [ ] **T-CR-061** P9: mutirão auditores roteados (seguranca/qualidade/llm-correctness/performance/observabilidade/idempotencia + conformidade-lgpd; produto no merge). MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial. Ref: plan §6.

## Pré-condições antes de iniciar T-CR-040+ (Fatia 3 — cross-módulo)

- 🔲 Revisão do plan (plan §7): tech-lead confirma sequenciamento 3a/3b/3c + flag canônica + namespace eventos OS.
- 🔲 consultor-rbc confirma inexistência de certificado faturável fora de OS (TL-CR-08) — antes do P8.
