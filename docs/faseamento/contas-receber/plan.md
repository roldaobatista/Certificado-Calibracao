---
owner: agente-ia
revisado-em: 2026-06-16
proximo-review: 2026-09-15
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: contas-receber
tipo: plan
proximo-passo: P4 — codar Fatia 1a (domínio puro)
relacionados:
  - docs/faseamento/contas-receber/spec.md
  - docs/faseamento/contas-receber/reviews-consolidado.md
  - docs/faseamento/contas-receber/tasks.md
---

# Plan — frente `contas-receber` (P3, derivado da spec v2)

> Regra "não declarar pronto sem rodar" (feedback 2026-05-18): cada fatia tem **Verificação** executada
> em ambiente real antes de seguir. Greenfield de código (T-CR-000 §1). Molde técnico = `fiscal`.

## 0. Princípio de sequenciamento (ordem por dependência + anti-retrabalho)

Dependência interna: **domínio puro → schema PG → use cases/REST (núcleo autossuficiente) → integrações
cross-módulo (tocam OS/clientes, FECHADOS) → fechamento**. Peças compartilhadas feitas 1x; o que depende de
tocar módulo fechado é a ÚLTIMA fatia de código (Fatia 3) — o núcleo (Fatia 2) entrega cobrança MANUAL + mock
gateway + webhook **sem tocar nada fechado**, então é o piso garantido. Conversores/predicates compartilhados
(`Dinheiro`, `grace_period_inadimplencia_por_perfil`, conversor valor string→centavos) entram no domínio (1a)
e são reusados pelas fatias seguintes.

## 1. Riscos e mitigações (cravados antes de codar)

| # | Risco | Sev | Mitigação | Achado |
|---|-------|-----|-----------|--------|
| R1 | Bloqueio duplicado: criar modelo PUSH paralelo ao PULL D+90 já existente em `clientes` | **CRIT** | CR implementa **adapter** do `InadimplenciaSource` existente; grace perfil-aware aplicado no adapter; flag canônica = `bloqueio_automatico_inadimplencia_habilitado` (não criar nova) | TL-CR-01 |
| R2 | `os.faturada`/`os.paga` têm consumer na OS mas ninguém publica (caminho morto) | **CRIT** | CR publica os dois (payload `{os_id}`) ao criar título de OS / dar baixa; registrar em `ACOES_OS` | TL-CR-02 |
| R3 | Injetar `cliente_id`/`valor` no WORM imutável da OS (cadeia 25a) ao enriquecer `os.concluida` | **CRIT** | Enriquecer SÓ o payload do **outbox** (em `repositories.py:660` ao cruzar pro bus); `payload_data` do WORM segue minimalista; cliente como `ReferenciaPIIAnonimizavel` | TL-CR-03 |
| R4 | Consumer relê `obter_perfil_tenant_corrente()` no worker → perfil ATUAL, não do fato gerador (fura CGCRE 8.4) | ALTO | Consumer lê `envelope["perfil_no_evento"]`; trigger fallback só via `COALESCE`, nunca sobrescreve; `None`→fail-closed | TL-CR-07 / RBC-CR-03 |
| R5 | CR tentar desbloquear cliente (não é dono do `ClienteBloqueio`) | ALTO | CR publica `contas_receber.pago` + query `tem_outra_vencida_em_aberto`; **consumer novo em `clientes`** desbloqueia + publica `cliente.desbloqueado` | TL-CR-05 |
| R6 | Título órfão / duplicado em OS reaberta ou replay tardio de `os.concluida` | ALTO | `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado`; consumer idempotente por `os_id`; `os.reaberta` cancela título se sem pagamento parcial | TL-CR-06 |
| R7 | Webhook público vaza existência de `gateway_id` por timing/oráculo | ALTO | tenant via `SECURITY DEFINER`/índice antes de RLS; `gateway_id` inexistente ≡ HMAC inválido = 401; **pentest externo no GATE-CR-ASAAS** | R-CR-NOVO-1 |
| R8 | Tenant perfil A bloqueado SEM notificação prévia (viola CDC) | **CRIT (legal)** | Notificação D+30/D+45 perfil A em Wave A via `send_mail`; payload rico (títulos+data+canal); **GATE-CR-NOTIF-D30-PERFIL-A** bloqueia ativação da flag sem canal | ADV-CR-01 / RBC-CR-01 |
| R9 | Bug de meio-centavo: `valor_total` string decimal × centavos | MÉDIO | CR opera em centavos (`Dinheiro`); conversor único de borda + teste (`"0.10"`,`"100.005"`,zero) | R-CR-NOVO-2 |
| R10 | Dupla baixa no webhook (replay / crash entre baixa e marca) | MÉDIO | idempotência dupla (`gateway_event_id` + estado `pago`); baixa+INSERT `gateway_events`+publish na MESMA `transaction.atomic` | TL-CR-12 |
| R11 | Faturar título de tenant suspenso | MÉDIO | consumer NÃO cria título se tenant suspenso (ADR-0035); dead-letter / reprocessa ao reativar (PRD §10) | R-CR-NOVO-3 |
| R12 | Juros calculados sobre `valor_original` em vez do saldo (parcial+juros) | MÉDIO | `calcular_valor_atualizado(titulo, pagamentos, data, regra)` sobre `valor_original - sum(pagamentos)` | TL-CR-10 |
| R13 | Override grava PII de terceiro em WORM; estouro de 5%/mês não barrado | MÉDIO | `justificativa` filtrada anti-PII (`INV-CAL-TXT-001`); contador 5%/mês no use case → alerta P1 + bloqueia | ADV-CR-04 / R-CR-NOVO-4 |
| R14 | Pré-commit em módulos fechados (OS/clientes) trava por hook de invariante em código legado | MÉDIO | skip oficial + justificativa ≥10 chars no diff (não é mascaramento — feedback_precommit_modulos_fechados); pré-commit ~5min; nunca commits concorrentes | memória projeto |

## 2. Fatia 1a — domínio puro (`src/domain/contas_receber/`)

Criar (molde `src/domain/fiscal/`):
- `enums.py` — `EstadoTitulo`, `MeioCobranca`, `CategoriaReceita`, `OrigemTitulo`, `OrigemPagamento`, `PerfilRegulatorio` (reuso/import). Todos `str, Enum`.
- `entities.py` — `Titulo`, `Parcela`, `Pagamento`, `OverrideBloqueio` (`@dataclass(frozen=True, slots=True)`).
- `transicoes.py` — `_TRANSICOES: Mapping[EstadoTitulo, frozenset[EstadoTitulo]]` + `validar_transicao()` + `pode_cancelar(titulo, pagamentos)`.
- `juros.py` — `calcular_valor_atualizado(titulo, pagamentos, data, regra) -> Dinheiro` (sobre saldo — R12); pura.
- `grace.py` — `grace_period_por_perfil(perfil) -> int` (45/20/30/7) — função pura; o predicate de tenant (`grace_period_inadimplencia_por_perfil`) é o wrapper de infra que lê o perfil.
- `conversao.py` — `valor_decimal_str_para_dinheiro(s) -> Dinheiro` (R9), conversor único de borda.
- `value_objects.py` — `RegraJurosMulta`, `CobrancaCriada`, `CobrancaCancelada`, `RecorrenciaCriada`, `EventoNormalizado`.
- `portas.py` — `PaymentGatewayProvider` (Protocol `@runtime_checkable`) + `TituloRepository` (Protocol).
- `mock_provider.py` — `MockPaymentGatewayProvider` + `ModoMock` (4 modos; `gateway_id` determinístico não-PII).
- `categoria.py` — `categoria_por_perfil_evento(perfil) -> CategoriaReceita` (A→RBC; B/C→NAO_RBC; D→BASICA) + `categoria_permitida(categoria, perfil) -> bool` (RBC só A).
- `erros.py` — hierarquia (spec §4 Erros).

**Verificação 1a:** `pytest tests/test_contas_receber_dominio_fatia1a.py --no-cov` — domínio puro, sem Django/PG.
Cobre: máquina de estados (happy+unhappy parametrize), juros sobre saldo (parcial), grace por perfil, conversão
de valor (bordas), categoria perfil-aware (mismatch), Mock 4 modos, Protocol runtime_checkable.

## 3. Fatia 1b — schema PG (`src/infrastructure/contas_receber/`)

Criar (molde `src/infrastructure/fiscal/`):
- `apps.py` — `ContasReceberConfig` (`label = "contas_receber"`); registra consumers no `ready()` (Fatia 3).
- `models.py` — `Titulo`, `Parcela`, `Pagamento`, `OverrideBloqueio` (tabelas achatadas; choices via `_choices(enum)`; `revision`). Constraint `UNIQUE(tenant_id, os_id_origem) WHERE estado != cancelado` (R6); CHECK `convenio_pix_id NOT NULL` quando `meio=pix_recorrente` (INV-FIN-GW-002).
- `mappers.py` + `repositories.py` (`DjangoTituloRepository` implementa Protocol).
- Migrations (sequência fiscal):
  - `0001_initial.py` — CreateModel + constraints + índices.
  - `0002_rls_policies.py` — ENABLE+FORCE+4 policies (padrão v2).
  - `0003_triggers_worm.py` — block-delete + worm_check (probatórios congelados; `status`/timestamps mutáveis; `data_baixa`/`cancelado_em` one-shot); `Pagamento`/`OverrideBloqueio` INSERT-only; trigger `perfil_no_evento` fallback `COALESCE` (R4).
  - `0004_grants_app_user.py`.
  - `0005_seed_authz.py` — ações `contas_receber.{criar,emitir,baixar,cancelar,override_bloqueio,ver}` × papéis.
- `audit/acoes_canonicas.py` — bloco `ACOES_CONTAS_RECEBER` (8 slugs lowercase) + união `ACOES_CANONICAS`; adicionar `os.faturada`/`os.paga` a `ACOES_OS` (R2/TL-CR-11). **CHECK não precisa migration** (sintático).
- `management/commands/validar_contas_receber.py` — drill estrutural (RLS enabled/force, ≥4 policies, UNIQUE, triggers WORM, grants).

**Verificação 1b:** `pytest tests/test_contas_receber_schema_fatia1b.py --no-cov --reuse-db` (`transaction=True`).
Cobre: RLS ENABLE+FORCE+4 policies, isolamento cross-tenant, block-delete RAISE, campo probatório imutável RAISE,
`Pagamento` INSERT-only, UNIQUE os_id, CHECK convenio_pix. `validar_contas_receber` verde.

## 4. Fatia 2 — use cases + REST (NÚCLEO autossuficiente; não toca módulo fechado)

`src/application/contas_receber/`:
- `criar_titulo_manual.py` — financeiro digita cliente+valor+vencimento+categoria (validada perfil-aware no use case — ADR-0073); perfil síncrono via `obter_perfil_tenant_corrente()`.
- `emitir_boleto.py` / `emitir_pix_recorrente.py` — chama `provider.criar_cobranca`/`criar_recorrencia`; valida `convenio_pix_id` (recorrente); 503 em timeout + publica `gateway_indisponivel`; recorrente emite só 1º título (TL-CR-09).
- `baixar_titulo_manual.py` — grava `Pagamento` + snapshot + transiciona + publica `contas_receber.pago`.
- `processar_webhook_pagamento.py` — valida HMAC + idempotência dupla (R10); baixa ≤60s; tudo na MESMA `transaction.atomic`.
- `cancelar_titulo.py` — 409 se pagamento parcial.
- `override_bloqueio.py` — papel gerente; justificativa≥100 anti-PII (R13); contador 5%/mês; WORM.

`src/infrastructure/contas_receber/`:
- `serializers.py` (sem `perfil`/`categoria` derivada — server-side), `views.py` (`ContasReceberViewSet` + `ContasReceberWebhookView` público — molde D-ORC-19, tenant via SECURITY DEFINER + anti-oráculo R7), `urls.py`.
- Idempotência REST (`_aplicar_idempotencia`), advisory lock, `publicar_evento(outbox=True)` no `atomic`.

**Verificação 2:** `pytest tests/test_contas_receber_api_fatia2.py --no-cov --reuse-db` (`transaction=True,
databases=["default","breaker_writer"]`). Cobre: criar manual perfil A+RBC (201), B+RBC=403, atendente=403, sem
Idempotency-Key=400/428, replay=mesmo titulo_id, emitir boleto mock (201), pix_recorrente sem convenio=422, provider
timeout=503, webhook HMAC válido→baixa+`pago`, HMAC inválido=401+incidente, replay webhook=200 sem 2º Pagamento,
cancelar com parcial=409, override sem papel=403, override justificativa curta=422, cross-tenant retrieve=404.

## 5. Fatia 3 — integrações cross-módulo (toca OS/clientes FECHADOS) + INVs + auto-faturamento

> **R14:** commits desta fatia tocam módulos fechados → pré-commit pode pegar hook de invariante em código
> legado; resolver com skip oficial + justificativa (não mascaramento). Stage seletivo; nunca commits concorrentes.

- **3a — Auto-faturamento de OS (GATE-CR-OS-EVENTO):**
  - Enriquecer o payload do **outbox** de `os.concluida` em `ordens_servico/repositories.py:660` (cliente via
    `ReferenciaPIIAnonimizavel` + `valor_total`); `payload_data` WORM intacto (R3).
  - `criar_titulo_a_partir_de_os.py` (use case) + consumer `@consumer_idempotente` (ADR-0033) — perfil do envelope
    (R4); conversão valor (R9); tenant suspenso não cria (R11); idempotente por `os_id` (R6); publica
    `contas_receber.titulo_emitido` + `os.faturada` (R2).
  - Consumer `os.reaberta` → cancela título sem pagamento.
  - Baixa de título de OS publica `os.paga` (R2).
- **3b — Inadimplência (GATE-CR-INADIMPLENCIA-RECONCILIA):**
  - `infrastructure/contas_receber/inadimplencia_adapter.py` — implementa `InadimplenciaSource` (PULL — R1);
    aplica `grace_period_inadimplencia_por_perfil`; `InadimplenciaItem` ganha `perfil`/`grace_perfil`.
  - **(PLAN-CR-01) Extensão de `InadimplenciaItem` toca módulo fechado `clientes`** (o dataclass vive em
    `domain/comercial/clientes/inadimplencia_source.py`): os campos novos entram como `Optional` com default
    seguro (`perfil=None`/`grace_perfil=None`) E o `SourceListaInterim` é atualizado para entregá-los — senão o
    job quebra (`AttributeError`) num deploy parcial onde o wiring ainda aponta pro source interino. Tratar como
    toque em módulo fechado (skip hook + justificativa, stage seletivo — R14).
  - Substituir o source interino no wiring do `clientes` (`infrastructure/clientes/inadimplencia.py:get_source()`,
    parametrizar via settings é mais limpo que hardcode) — toca clientes (R14); o job é agnóstico à implementação.
  - `notificar_inadimplencia.py` — `send_mail` D+30/D+45 perfil A (R8); payload rico (ADV-CR-01); job/predicate.
  - **GATE-CR-NOTIF-D30-PERFIL-A:** gate de ativação da flag.
- **3c — Desbloqueio (GATE-CLI-6 — toca clientes):**
  - Query `tem_outra_vencida_em_aberto(cliente_id)` exposta por CR.
  - Consumer novo em `clientes` de `contas_receber.pago` → encerra `ClienteBloqueio` + publica `cliente.desbloqueado`
    (R5); idempotente; parcial mantém (AC-CR-006-2).
- **3d — INVs + hooks (família INV-FIN-* volta ao mestre — R14 invariantes-futuras):**
  - Cravar em `REGRAS-INEGOCIAVEIS.md`: INV-FIN-GW-001/002, -PERFIL-001, -GRACE-PERFIL-001, -SNAPSHOT-PERFIL-001,
    -REATIV-001, -INAD-001 + INV-CR-OS-TITULO-UNICO, -PAGAMENTO-WORM, -OVERRIDE-WORM, -OVERRIDE-ANTI-PII,
    -WEBHOOK-PAYLOAD-MINIMO; reconciliar INV-FIS-CR-001 / INV-CAL-FIN-001.
  - Hooks: `policy-tenant-vs-cliente.sh` (INV-FIN-INAD-001), `cr-provider-import-fronteira-check.sh`,
    `cr-perfil-server-side-check.sh` (molde fiscal). Registrar no `pre-commit-manifest.tsv`.

**Verificação 3:** `pytest tests/test_contas_receber_inadimplencia_fatia3.py tests/test_contas_receber_autofatura_fatia3.py
tests/test_contas_receber_api_fatia2.py --no-cov --reuse-db` (+ fatia2 para regressão de R7 — PLAN-CR-03) + `bash
.claude/hooks/_test-runner.sh`. Cobre: auto-fatura de `os.concluida` enriquecida (perfil do envelope; perfil-mudou →
snapshot do evento — R4); replay + os.reaberta (R6); **os.reaberta APÓS pagamento parcial → NÃO cancela** (AC-CR-006-2);
tenant suspenso não cria (R11); **grace na fronteira exata** (D+44 A não entra no bloqueio, D+46 entra); grace por perfil
(D+50 A bloqueia, D+10 A não); notificação D+30/D+45; desbloqueio happy + parcial (R5); adapter interim com
`InadimplenciaItem` estendido (campos Optional não quebram job — PLAN-CR-01); hooks novos verdes.

## 6. P8/P9 — fechamento

- **P8:** ADR de reconciliação (molde ADR-0083) — (a) `Titulo` = "ContasReceber" do PRD / `Fatura` Wave B;
  (b) gatilho = `os.concluida`, NÃO `Certificado.Emitido` (emenda ADR-0043/INV-CAL-FIN-001 — GATE-CR-CERT-RECONCILIA).
  `matriz-reconciliacao.md` (US↔código↔teste; INV↔teste; ata P9). `STATUS-GERADO.md` (`status-projeto.sh --check`).
  Frontmatters → `stable`. Atualizar `plano-dependencia-sistema.md` (nível 5 — CR FECHA receita).
- **P9:** mutirão de auditores roteados (INV-RITUAL-003). Esperados sempre: seguranca, qualidade, llm-correctness,
  performance, observabilidade, idempotencia. Condicionais: supplychain (se tocar pyproject), conformidade-lgpd
  (toca PII — SIM). Produto no merge. MÉDIO+ bloqueia (INV-RITUAL-001); 2ª passada escopada + adversarial (R5/R6).

## 7. Revisão do plan — CONCLUÍDA (2026-06-15)

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES** (PLAN-CR-01..03). Confirmou: sequenciamento
  1a→1b→2→3a→3b→3c→3d correto (3c depende de `contas_receber.pago` da Fatia 2; 3a antes de 3c); `os.faturada`/
  `os.paga` em `ACOES_OS` publicados por CR (verificado `acoes_canonicas.py:191-213` + `assert_acao_canonica`
  na união); flag canônica `bloqueio_automatico_inadimplencia_habilitado` + substituição do source interino
  viável sem reescrever o job. Correções incorporadas: PLAN-CR-01 (extensão `InadimplenciaItem` = toque em módulo
  fechado + defaults Optional → 3b acima); PLAN-CR-02 (apps.py de CR com `# TODO Fatia 3` → nota T-CR-020);
  PLAN-CR-03 (Verificação 3 inclui fatia2 + fronteira de grace + os.reaberta pós-parcial → acima).
- 🔲 `consultor-rbc-iso17025` — já confirmou em RBC-CR-05 (P2) que todo cert vem de OS e cert de padrão interno =
  não-faturável; re-confirmar formalmente no T-CR-060 (P8) antes de fechar a ADR de reconciliação.
- Demais pontos já fechados no P2 (`reviews-consolidado.md`).

**P3 FECHADO. Próximo passo = P4 (codar Fatia 1a — domínio puro, T-CR-010..016; não exige Docker/PG).**

## 8. Non-goals do plan

Não construir: `Fatura` agrupadora, régua rica (Wave B), adapter Asaas real, A3 real, gatilho `Certificado.Emitido`,
faturamento por `AtividadeDaOS`, baixa parcial com sucessor, cartão recorrente PCI, geração de títulos recorrentes
subsequentes, OFX, `em_disputa`, telas/portal. RAT/DPIA/minutas CONGELADOS (GATE-LGPD-RAT-CR).
