---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-16
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: contas-receber
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/contas-receber/spec.md
  - docs/faseamento/contas-receber/plan.md
  - docs/faseamento/contas-receber/tasks.md
  - docs/adr/0084-contas-receber-titulo-reconcilia-prd-gatilho-os-concluida.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `contas-receber` (Fatias 1a–3d / P8)

> Rastreabilidade US→código→teste + INV→teste→enforcement (TST-004) + reconciliação PRD
> (ADR-0084). Fonte do mapeamento: varredura do código real (`src/{domain,application,
> infrastructure}/contas_receber/` + `src/infrastructure/clientes/consumers/`) em 2026-06-16.
> Frente financeira **nível 5** da cadeia — **FECHA a receita ponta a ponta** (ADR-0084).

## 1. Rastreabilidade US ↔ código ↔ teste

| US / entidade | Núcleo Wave A | INV | Arquivo de código (símbolo) | Status |
|---|---|---|---|---|
| US-CR-001 gerar título de OS + manual | consumer `os.concluida` enriquecido cria `Titulo`; lançamento manual; 1 OS→1 título | INV-CR-OS-TITULO-UNICO, INV-FIN-PERFIL-001, INV-FIN-SNAPSHOT-PERFIL-001 | `consumers/os_eventos.py` (`handle_os_concluida`) · `application/.../criar_titulo_a_partir_de_os.py` · `criar_titulo_manual.py` · `domain/.../entities.py` (`Titulo`) | ✅ |
| US-CR-002 emitir boleto/PIX/PIX-recorrente | porta `PaymentGatewayProvider` + Mock; convênio NOT NULL recorrente | INV-FIN-GW-001/002 | `domain/.../portas.py` · `mock_provider.py` · `application/.../emitir_boleto.py`/`emitir_pix_recorrente.py` | ✅ (Asaas real = GATE-CR-ASAAS) |
| US-CR-003 baixa automática via webhook | webhook HMAC + idempotência dupla; baixa ≤60s; `Pagamento` INSERT-only | INV-FIN-GW-001, INV-CR-PAGAMENTO-WORM, INV-CR-WEBHOOK-PAYLOAD-MINIMO | `application/.../processar_webhook_pagamento.py` · `infrastructure/.../views_webhook.py` · migration `0006` (SECURITY DEFINER) | ✅ |
| US-CR-004 juros/multa + desconto na leitura | `calcular_valor_atualizado` sobre saldo; job transiciona `vencido` | INV-026 (herdada) | `domain/.../juros.py` · `transicoes.py` · `application/.../baixar_titulo_manual.py` | ✅ (desconto-pontualidade pré-venc sem fórmula = débito P9) |
| US-CR-005 régua lembrete WhatsApp/e-mail | — | — | — | ⏭️ Wave B (GATE-CR-REGUA) |
| US-CR-006 desbloqueio ao quitar | consumer em `clientes` encerra `ClienteBloqueio` + publica `cliente.desbloqueado`; parcial mantém | INV-FIN-REATIV-001 | `infrastructure/clientes/consumers/contas_receber_eventos.py` (`handle_contas_receber_pago`) · `contas_receber/queries_desbloqueio.py` | ✅ |
| US-CR-007 cobrança via porta | coberto por US-CR-002 | INV-FIN-GW-001/002 | idem US-CR-002 | ✅ |
| US-CR-008 categoria receita perfil-aware | `categoria_receita` derivada do `perfil_no_evento`; RBC só A | INV-FIN-PERFIL-001 | `domain/.../categoria.py` (`categoria_por_perfil_evento`, `categoria_permitida`) · `enums.py` (`CategoriaReceita`) | ✅ |
| US-CR-009 snapshot no pagamento | `valor_atualizado_snapshot_em_pagamento` carimbado na baixa (M-FIN-002) | INV-CR-PAGAMENTO-WORM | coberto por US-CR-003 + `baixar_titulo_manual.py` · `entities.py` (`Pagamento`) | ✅ |
| US-CR-010 bloqueio dura perfil-aware + notificação + override | adapter grace 45/20/30/7; notificação D+30/D+45 perfil A (Caminho C, prova fail-closed); override WORM anti-PII 5%/mês | INV-FIN-GRACE-PERFIL-001, INV-FIN-INAD-001, INV-CR-OVERRIDE-WORM, INV-CR-OVERRIDE-ANTI-PII | `infrastructure/.../inadimplencia_adapter.py` · `application/.../notificar_inadimplencia.py` + `management/commands/job_notificar_inadimplencia.py` · `override_bloqueio.py` · model `NotificacaoInadimplencia` (migration 0007) | ✅ (A3 real = GATE-CR-A3; disparo PF real = GATE-LGPD-RAT) |
| Reconciliação PRD `ContasReceber`→`Titulo` (ADR-0084) | `Titulo`=raiz; `Fatura` Wave B; gatilho `os.concluida`≠`Certificado.Emitido` | — | `domain/.../entities.py` (`Titulo` frozen) + ADR-0084 (emenda ADR-0043 §1) | ✅ |

## 2. INV ↔ enforcement real ↔ teste nomeado (TST-004)

> Cada INV crítica tem ≥1 teste de regressão cujo **nome cita o ID** em
> `tests/regressao/test_inv_fin_contas_receber.py` (Fatia 3d/P8 — fecha TST-004), além dos
> testes comportamentais por fatia (`tests/test_contas_receber_*_fatia*.py`).

| INV | Enforcement real | Teste comportamental (fatia) | Teste-com-ID (regressão) |
|---|---|---|---|
| INV-FIN-GW-001 | `existe_gateway_event()` + idempotência dupla (event_id + estado); HMAC; tudo na mesma `atomic` | `test_contas_receber_webhook_fatia2b.py` (replay sem 2º Pagamento; HMAC inválido 401) | `test_inv_fin_gw_001_*` |
| INV-FIN-GW-002 | CHECK `chk_cr_titulo_pix_recorrente_convenio` (migration 0001) + guard no use case | `test_contas_receber_schema_fatia1b.py` + `..._gateway_fatia2b.py` (422 sem convênio) | `test_inv_fin_gw_002_*` |
| INV-FIN-PERFIL-001 | `categoria_permitida()` no domínio + validação no use case (ADR-0073) + hook `cr-perfil-server-side-check` | `test_contas_receber_api_fatia2a.py` (B+RBC 403) · `..._dominio_fatia1a.py` | `test_inv_fin_perfil_001_*` |
| INV-FIN-GRACE-PERFIL-001 | `grace_period_por_perfil` no adapter `TituloVencidoInadimplenciaSource` | `test_contas_receber_inadimplencia_fatia3.py` (fronteira D+44/D+46 por perfil) | `test_inv_fin_grace_perfil_001_*` |
| INV-FIN-SNAPSHOT-PERFIL-001 | trigger `titulo_receber_perfil_fallback` (COALESCE INSERT) + `worm_check` bloqueia UPDATE | `test_contas_receber_schema_fatia1b.py` (perfil imutável) | `test_inv_fin_snapshot_perfil_001_*` |
| INV-FIN-REATIV-001 | consumer `handle_contas_receber_pago` (só bloqueio automático; parcial mantém) | `test_contas_receber_desbloqueio_fatia3.py` (happy + parcial + manual + idempotente) | `test_inv_fin_reativ_001_*` |
| INV-FIN-INAD-001 | hook `policy-tenant-vs-cliente.sh` (operacional cliente ≠ billing-saas) | casos PTVC no `_test-runner.sh` | `test_inv_fin_inad_001_*` |
| INV-CR-OS-TITULO-UNICO | UNIQUE parcial `uq_cr_titulo_os_ativo` (0001) + soft-check + advisory lock | `test_contas_receber_schema_fatia1b.py` + `..._autofatura_fatia3.py` (idempotente por os_id) | `test_inv_cr_os_titulo_unico_*` |
| INV-CR-PAGAMENTO-WORM | triggers `pagamento_titulo_block_update/delete` (0003); `Pagamento` frozen | `test_contas_receber_schema_fatia1b.py` (UPDATE/DELETE → raise) | `test_inv_cr_pagamento_worm_*` |
| INV-CR-OVERRIDE-WORM | triggers `override_bloqueio_block_update/delete` (0003); contador 5%/mês no use case | `test_contas_receber_gateway_fatia2b.py` (override sem papel 403; limite mês) | `test_inv_cr_override_worm_*` |
| INV-CR-OVERRIDE-ANTI-PII | validação anti-PII (regex CPF/CNPJ/e-mail/tel) no `override_bloqueio.py`; ≥100 chars | `test_contas_receber_gateway_fatia2b.py` (justificativa com CPF → 422) | `test_inv_cr_override_anti_pii_*` |
| INV-CR-WEBHOOK-PAYLOAD-MINIMO | `EventoNormalizado` campos mínimos; model `Pagamento` sem PII do pagador | `test_contas_receber_inadimplencia_fatia3.py` (evento sem e-mail) | `test_inv_cr_webhook_payload_minimo_*` |
| INV-FIS-CR-001 (reconciliada) | consumer `handle_os_concluida` registrado para `os.concluida` (não `certificado.emitido`) — ADR-0084 | `test_contas_receber_autofatura_fatia3.py` (publica `titulo_emitido`+`os.faturada`) | `test_inv_fis_cr_001_*` |

> **Reusadas (transversais):** INV-TENANT-001..003 + INV-008 (RLS v2 FORCE — migration 0002;
> cross-tenant 404 anti-oráculo), INV-BUS-001 (`@consumer_idempotente` os.concluida/os.reaberta/
> contas_receber.pago — fan-out), INV-026 (juros não persiste valor inflado), INV-ANON-001..004
> (`cliente` via `ReferenciaPIIAnonimizavel`), IDEMP-001 (Idempotency-Key nos POST).

## 3. Reconciliação PRD (ADR-0084)

| Conceito do PRD | Destino canônico | Estado |
|---|---|---|
| `ContasReceber` (agregado) | `Titulo` (raiz) + `Parcela` + `Pagamento` | ✅ construído |
| `Fatura` agrupadora | Wave B (GATE-CR-FATURA) | ⏭️ diferido |
| gatilho de geração | `os.concluida` enriquecido (não `Certificado.Emitido`) | ✅ ADR-0084 emenda ADR-0043 §1 |
| certificado faturável | só de OS (`AtividadeDaOS.tipo=calibracao`); padrão interno não-faturável | ✅ parecer RBC P1 |

## 4. Migrations da frente (`src/infrastructure/contas_receber/migrations/`)

| # | O que faz |
|---|---|
| 0001 | CreateModel (4 tabelas) + UNIQUE parcial os_id + CHECK convênio PIX + índices |
| 0002 | RLS ENABLE+FORCE + 4 policies padrão v2 |
| 0003 | Triggers WORM: block-delete + worm_check (probatórios/one-shot) + Pagamento/Override INSERT-only + perfil fallback COALESCE |
| 0004 | GRANTs `app_user` |
| 0005 | Seed authz (6 ações × papéis) |
| 0006 | Policy webhook + `resolver_cr_titulo_por_gateway` (SECURITY DEFINER, anti-oráculo) |
| 0007 | `NotificacaoInadimplencia` (prova de envio) + RLS + WORM + grants + UNIQUE(tenant,titulo,marco) |

## 8. P9 — ritual de auditores roteados (INV-RITUAL-003)

> Esperados sempre: segurança · qualidade · llm-correctness · performance · observabilidade ·
> idempotência. Condicionais: conformidade-lgpd (toca PII — SIM); supplychain (não tocou
> pyproject/lock — N/A). Produto no merge. MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada
> escopada + adversarial (R5/R6).

| Passada | Resultado |
|---|---|
| **1ª** | **7 PASS** (segurança · qualidade · llm-correctness · performance · observabilidade · conformidade-lgpd · supplychain) + **1 MÉDIO** — IDEMPOTÊNCIA: **MÉDIO-1 TOCTOU na idempotência do webhook** (`existe_gateway_event` é check-then-act sob READ COMMITTED; `gateway_event_id` só tinha `Index`, sem `UniqueConstraint`; webhook sem advisory lock → 2 webhooks paralelos com mesmo `gateway_event_id` duplicariam `Pagamento` WORM + `contas_receber.pago` 2×). **Verificação adversarial (R6) confirmou real.** CONCERN BAIXO registrados (não bloqueiam): qualidade — `# type: ignore[attr-defined]` sem razão inline em `inadimplencia_adapter.py:73` (ignore narrado sobre param `object`); observabilidade — OBS-003 métrica pré-F-C + logs de no-op em consumers sem `extra` explícito (mitigado por GUC de contexto); performance — N+1 em jobs batch (adapter inadimplência + job notificação). |
| **conserto causa-raiz** | `UniqueConstraint(tenant, gateway_event_id)` PARCIAL `WHERE gateway_event_id != ''` (`models.py` + migration `0008`, aplicada dev+test_afere) = defesa de banco; use case `processar_webhook_pagamento` envolve `salvar_pagamento` em savepoint e captura `IntegrityError` → `ja_processado=True` (replay no-op, sem 2º Pagamento/evento). Teste de regressão `test_inv_fin_gw_001_pagamento_gateway_event_unico_resistente_a_corrida` (constraint barra duplicata; parcial não barra manuais). 28 testes verdes (21 regressão-INV + 7 webhook fatia2b). |
| **2ª (escopada R5 — só IDEMPOTÊNCIA, restrita ao conserto)** | **IDEMPOTÊNCIA RESOLVIDO** (adversarial R6) — janela TOCTOU fechada pela constraint parcial + savepoint; sem mascaramento (`except IntegrityError → replay` é semântica de idempotência legítima; teste exerce a barreira real); nenhum NOVO-ACHADO. **Módulo `contas-receber` FECHADO — Wave A.** |

## Débitos rastreados para P9 / Wave B

- Desbloqueio SEM grace (assimetria c/ adapter de bloqueio 3b) — ver `queries_desbloqueio.py`.
- Snapshot do webhook usa `valor_original` (sem juros acumulados).
- Desconto-pontualidade pré-vencimento sem fórmula cravada (AC-CR-004-2).
- Isolamento por-consumer do bus (re-review quando a saga de anonimização sair do stub).
- GATE-CR-REPROVA-PAGA + GATE-CR-OBS-OS-SEM-CERT (ADR-0084 decisão 5 — OS reaberta com pagamento / OS-sem-certificado).
