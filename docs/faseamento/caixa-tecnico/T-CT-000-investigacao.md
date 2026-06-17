---
owner: agente-ia
revisado-em: 2026-06-17
proximo-review: 2026-09-17
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: caixa-tecnico
tipo: investigacao
relacionados:
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/modelo-de-dominio.md
  - docs/dominios/operacao/modulos/app-tecnico/prd.md
  - docs/faseamento/plano-dependencia-sistema.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# T-CT-000 — Investigação P0 (re-rastreio) — frente `caixa-tecnico`

> REGRA #0: levantar o ESTADO REAL antes da spec. Fonte: varredura do código `src/` +
> docs do módulo + plano de dependências (2026-06-17). Próxima da fila cravada após `agenda`.

## 1. O que é (resumo do PRD — `status: stable`)

Controle financeiro individual do técnico de campo: **adiantamentos** (solicitação→aprovação→entrega),
**despesas** (foto-comprovante OBRIGATÓRIA, offline-first, GPS opcional/LGPD, idempotência IDEMP-001),
**validação** pelo financeiro (swipe valida/rejeita), **despesa validada IMUTÁVEL** (trigger PG
`caixa_tecnico_anti_mutacao`), **prestação de contas** mensal (saldo adiantado×gasto). 7 US (US-CT-001..007).
**Transversal A/B/C/D** (toda empresa com técnico de campo tem caixa) — sem gating regulatório; só a
retenção de PII de GPS varia. **Wave A robusto** (decisão estratégica — técnicos como evangelizadores).

## 2. Estado real do código — GREENFIELD TOTAL

Zero linhas de `caixa_tecnico`/`CaixaTecnico`/`Adiantamento`/`Despesa`/`PrestacaoContas` em `src/`.
Nenhuma migration/model/domínio/view. Único par do **nível 5** ainda ausente (junto de `contas-pagar`,
`chamados`, `base-conhecimento`). `contas-receber` (par N5) já FECHADO.

## 3. Entidades (de `modelo-de-dominio.md`)

| Agregado | Campos-chave | Estados |
|---|---|---|
| `CaixaTecnico` (raiz por técnico) | `tenant_id`, `tecnico_id`, `saldo_atual` (calculado), `politica_id`, `prestacao_em_aberto_id` | — |
| `Adiantamento` | `caixa_id`, `valor` (`Dinheiro`), `meio_entrega` (pix/transferencia/dinheiro), `os_referencia?`, timestamps | `solicitado→aprovado→entregue→cancelado/rejeitado` |
| `Despesa` | `caixa_id`, `tecnico_id`, `valor`, `data`, `categoria` (enum), `os_id?`, `foto_comprovante_url` (obrigatória), `foto_hash` (anti-dup), `gps_lat/lng?`, `km_percorridos?` | `pendente→validada/rejeitada` |
| `PrestacaoContas` | `caixa_id`, `periodo`, `total_adiantado`, `total_despesas_validadas`, `saldo_final`, `direcao` (tecnico-deve/tenant-deve/quitado), `fechada_em/por` | imutável por design |
| `Politica` (por tenant) | `limite_por_categoria`, `alcada_aprovacao`, `tarifa_km`, `exige_gps`, `prazo_prestacao_dias` | — |

**Eventos emitidos:** `adiantamento.solicitado`/`.aprovado`, `despesa.lancada`/`.validada`/`.rejeitada`,
`prestacao.fechada` (slugs lowercase a cravar em `acoes_canonicas.py` — G7). **Consome:** `os.aberta`/
`os.concluida` (disponibiliza OS p/ vínculo).

## 4. Dependências reais (todas upstream CONSTRUÍDAS; downstream/par AUSENTES)

| Dep | Estado | Como usar |
|---|---|---|
| `colaboradores` (papel `tecnico`, `AnexoStoragePort` local) | ✅ | `PapelColaborador.TECNICO`; `AnexoStoragePort` content-addressed SHA-256 (`anexo_storage.py`); B2 diferido (`GATE-COL-ANEXO-B2`) |
| `ordens_servico` (`os_id`, eventos `os.*`) | ✅ | vincular despesa a `os_id`; eventos em `acoes_canonicas.py:194` |
| `Dinheiro`/`ReferenciaPIIAnonimizavel`/`JanelaVigencia` (shared VOs) | ✅ | `src/domain/shared/value_objects.py` |
| `Colaborador.consente_gps_em` (opt-in GPS) | ❌ **não existe** | greenfield — migration nova (G1; tech-lead decide o módulo-dono) |
| `contas-pagar` (reembolso técnico) | ❌ **não construído** (par N5) | reembolso fica fail-open lazy: publica `prestacao.fechada`, GATE consome quando existir (G4) |
| `despesas`/`app-tecnico`/`custeio-real` | ❌ (níveis 6/7) | DESTRAVADOS por esta frente; não são deps |

## 5. Padrões canônicos a reusar (exemplares recentes)

- **Trigger anti-mutação WORM:** `src/infrastructure/orcamentos/migrations/0003_triggers_worm.py` (`{tabela}_anti_mutation_check()` BEFORE UPDATE/DELETE) — molde do `caixa_tecnico_anti_mutacao` (WHEN `OLD.status='validada'`).
- **RLS v2** (ENABLE+FORCE+4 policies): `src/infrastructure/contas_receber/migrations/0002_rls_policies.py`.
- **Idempotência:** consumer `@consumer_idempotente` (`agenda/consumers/os_eventos.py`); REST `_aplicar_idempotencia` + `Idempotency-Key` (`agenda/views.py`) — IDEMP-001 obrigatório (foto offline com `client_offline_id`).
- **Perfil server-side:** `obter_perfil_tenant_corrente` (`authz/perfil_tenant_helper.py`) — nunca do payload.
- **Outbox:** `publicar_evento` (`audit/event_helpers.py`) dentro do `atomic`.
- **Storage de foto:** `AnexoStoragePort` content-addressed (idempotente por hash — cobre replay offline). Foto de recibo é JPG/PNG (≠ PDF do colaboradores) — G2.

## 6. Padrão GPS/offline espelhado de `app-tecnico` (US-APP-003)

- **Fonte única:** `Colaborador.consente_gps_em` no banco — NUNCA do payload. NULL → `403 GPS_CONSENTIMENTO_AUSENTE`.
- **Base legal:** art. 7º V (execução de contrato) + IX (legítimo interesse) LGPD; retenção GPS 5a + crypto-shredding.
- **Revogação** (`consente_gps_em.revogado_em`): para coleta de GPS mas **NÃO bloqueia a despesa** (AC-CT-002-6).
- **Offline-sync:** `POST /v1/sync/despesas-lote` (batch, `foto_base64`); LWW por `client_event_ts`+`device_id`; o app Flutter (cliente offline) é DIFERIDO (ADR-0009) — o backend só provê os endpoints idempotentes.
- **INV compartilhada:** `INV-LGPD-CONSENT-001` governa GPS nos dois módulos.

## 7. GATEs e decisões pendentes (resolver antes/durante P1–P3)

**Decisões de tech-lead (P2 — subagente):**
- **G1/GATE-CT-GPS-MIGRATION:** `Colaborador.consente_gps_em` — migration vai em `colaboradores` (FECHADO) ou no próprio `caixa-tecnico`? (molde da decisão D-AGE-15 da agenda: override morou na própria frente p/ não tocar módulo fechado). Default proposto: entidade/campo de consentimento mora no caixa-tecnico/shared, sem migration em colaboradores.
- **G2/GATE-CT-STORAGE-PORT:** `FotoComprovanteStoragePort` novo vs. generalizar (há 2 ports `AnexoStoragePort` duplicados — colaboradores + metrologia). Risco R1 (drift). Default: port próprio no caixa-tecnico reusando a estratégia content-addressed; consolidação shared = ADR à parte.
- **G6/GATE-CT-PDF:** PDF da prestação — reusar gerador existente (certificados) ou novo. Default: reusar se houver; senão dado estruturado + PDF diferido.

**Decisões de produto (Roldão — batch de planejamento 2026-06-17 — RESOLVIDAS):**
- **G3/GATE-CT-B2:** foto de recibo em B2 pago vs. filesystem local → **LOCAL** (pré-decidido por [[project_sem_contratacoes_externas_ate_producao]]; molde `GATE-COL-ANEXO-B2`). B2 real = GATE pré-produção.
- **G4/GATE-CT-CONTAS-PAGAR (Roldão decidiu):** **prestação FECHA e REGISTRA o saldo** (`direcao=tenant-deve` + `saldo_final`) + publica `prestacao.fechada` (**fail-open lazy** — não trava o fechamento "em 5 min"). A **execução do reembolso** (PIX/transferência) difere até `contas-pagar` existir, que consumirá o evento. **NÃO** bloquear; **NÃO** reembolso manual no caixa-tecnico (evita retrabalho).
- **G5/GATE-CT-DEVOLUCAO (Roldão decidiu):** quando `direcao=tecnico-deve`, o Wave A **só REGISTRA o saldo devedor**; a **execução** da devolução (dinheiro/PIX/desconto-folha) é **Wave B** (coerente com não-objetivo Wave A "adiantamento via folha"). GATE-CT-DEVOLUCAO-EXEC.

**Riscos:** R1 (duplicação de storage port), R2 (migration GPS conflitante com app-tecnico futuro — definir dono agora), R3 (`prestacao.fechada` "ao ar" até contas-pagar), R4 (idempotência de foto offline coberta por content-addressing — documentar na spec).

## 8. Próximo passo

P1 — spec (`spec.md`) incorporando as decisões do batch de produto + decisões cravadas D-CT-N.
Depois P2 (revisão tech-lead + advogado LGPD + — produto via Roldão), P3 (plan/tasks), fatias 1a..3x, P8, P9.
**Ritual obrigatório** (Spec Kit) — ver [[feedback_ritual_orquestrador]].
