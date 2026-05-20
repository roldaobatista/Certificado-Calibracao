---
owner: roldao
revisado_em: 2026-05-20
proximo_review: 2026-08-19
status: stable
diataxis: reference
audiencia: agente
marco: Wave A Marco 1 — clientes
tipo: matriz-reconciliacao-spec-codigo
relacionados:
  - docs/faseamento/M1-clientes/spec.md
  - docs/faseamento/M1-clientes/plan.md
---

# Marco 1 (clientes) — Reconciliação spec ↔ código (P3)

> **Pra quê:** mede cada AC binário da `spec.md` (versão STABLE pós-P2)
> contra o código real do módulo. Coluna **Estado**: `OK` (código
> satisfaz — base de evidência citada), `GAP` (diverge → vira
> `T-CLI-NNN`, conserto causa-raiz em P4), `TRACK` (gate Wave A
> rastreado, NÃO bloqueia fechar Marco 1).
>
> **Base de evidência do `OK`** (Constituição "verificar antes de
> afirmar"): leituras diretas de `src/infrastructure/clientes/` +
> migrations 0001..0016 + auditorias 10 lentes (CONSOLIDADO.md de
> 2026-05-18) cruzadas com saneamento já feito (SANEA-01/02/03/06/10
> fechados em commits anteriores; SANEA-04 fechado via F-A FA-C1).
>
> **Severidade pra fechamento (INV-RITUAL-001):** MÉDIO bloqueia
> igual a CRÍTICO/ALTO; só BAIXO é rastreável.

---

## Matriz

### US-CLI-001 — Cadastro PF/PJ

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-CLI-001-1 | OK | `models.py:49-71` Cliente + VOs `CPF`/`CNPJ` (ADR-0017); `views.py:138-149` POST cria com `tenant_id` do middleware. |
| AC-CLI-001-2 | OK | `serializers.py:80-110` valida via VO; 400 em documento inválido. |
| AC-CLI-001-3 | OK | índice `unique_doc_ativo` (migration 0006); `views.py:138-149` retorna 409. |
| **AC-CLI-001-4** | **GAP** | **T-CLI-101**: enum atual (`lgpd.py:65-68`) tem só 2 valores (`art_7_v`, `art_7_i`); spec exige 5 (`CONSENTIMENTO`, `EXECUCAO_CONTRATO`, `OBRIG_LEGAL`, `LEGITIMO_INTERESSE` com `lia_id`, `PROTECAO_CREDITO`). Nomenclatura também diverge — spec usa nomes simbólicos, código usa `art_*`. Migration de enum + `lia_id` FK + alinhamento de `aceite_lgpd_origem` (atual `balcao/portal/importacao/api_terceiro` ≠ spec `CADASTRO_DIRETO/IMPORTACAO_LEGADA/MIGRACAO_SISTEMA_ANTERIOR`). |
| AC-CLI-001-5 | OK | evento `Cliente.Criado` publicado (`views.py:170`); helper único ainda a confirmar (cruz-ref T-CLI-105). |
| AC-CLI-001-6 | OK | `views.py:244-262` `registrar_auditoria` com payload sanitizado; cadeia tenant F-A; `SEC-SANITIZE-001` aplicado em escrita. |
| **AC-CLI-001-7** | **GAP** | **T-CLI-102**: `ClienteIdentidadeHistorico` não existe. Criar modelo + migration + trigger PG anti-mutation; PATCH em `nome`/`razao_social` grava histórico imutável (ISO/IEC 17025 §7.8.2.1 (b) + §8.4). |

### US-CLI-002 — Visão 360°

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-CLI-002-1 | TRACK | `EventoTimeline` materialização via consumer multi-módulos — **GATE-CLI-2** Wave A; hoje `visao_360` filtra `Auditoria` direto (`views.py:578-584`). |
| AC-CLI-002-2 | TRACK | LIMIT 200 hardcoded (`views.py:584`); cursor de paginação ausente — **GATE-CLI-3** valida p95<1.5s em produção com índice composto + cursor. |
| AC-CLI-002-3 | OK | `views.py:568-575` `registrar_acesso_dados_cliente` chamado ANTES de retornar timeline; fail-loud em falha de gravação (LGPD art. 37). |
| AC-CLI-002-4 | OK | enum `finalidade` validado (`views.py:540-548`); cada acesso com finalidade nova grava linha separada. |
| **AC-CLI-002-5** | **GAP** | **T-CLI-103**: `cliente_canonico_id` coluna inexistente; `resolver_cliente_canonico` ausente; materialização preguiçosa não implementada. Criar coluna NOT NULL DEFAULT id + função recursiva cap=10 + UPDATE em leitura quando hops>1. |
| **AC-CLI-002-6** | **GAP** | **T-CLI-104**: circuit breaker observado ausente — sem métrica `acessos_dados_cliente.gravacao_falhada_total{tenant_id}` nem alerta P1 em janela 5min ≥0.1%. |
| **AC-CLI-002-7** | **GAP** | **T-CLI-105**: `INV-013-A` (contagem diária imutável) ausente — sem job daily; criar management command + métrica em sink imutável (cadeia sistema até GATE-1; depois B2 WORM). |

### US-CLI-003 — Importação CSV/XLSX

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-CLI-003-1 | OK | `views.py:621` `importar_preview` retorna 10 linhas + mapeamento + warnings. |
| AC-CLI-003-2 | OK | `views.py:715` `importar_executar` com `Idempotency-Key` obrigatório; job Celery; status via GET `importacoes/{import_id}`. |
| AC-CLI-003-3 | OK | `repositories.py:210-220` `pg_advisory_xact_lock(hashtext(tenant_id))` dentro de `transaction.atomic()` (SANEA-01 fechado em `ef7d3c1`). |
| AC-CLI-003-4 | OK | dedup lote `(tenant_id, tipo_pessoa, documento)` (INV-024); idempotência por `Idempotency-Key`. |
| AC-CLI-003-5 | OK | `csv_safety.py:21` `sanitizar_celula_csv` chamada em export (`repositories.py:308-311`); SANEA-03 fechado em `e123c4a`. |
| AC-CLI-003-6 | OK | `PII_HASH_KEY` server-side (F-A); SANEA-02 fechado em `a98b3d5`. |
| **AC-CLI-003-7** | **GAP** | **T-CLI-106**: origens atuais (`lgpd.py:42-47`) não batem com spec (`CADASTRO_DIRETO`/`IMPORTACAO_LEGADA`/`MIGRACAO_SISTEMA_ANTERIOR`); flag `pii_regularizacao_em` ausente; estado restrito não modelado. Migration alinhando enum + flag + dashboard regularização (este último = GATE-CLI-4). |

### US-CLI-004 — Bloqueio comercial

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| AC-CLI-004-1 | OK | `views.py:291-334` `bloquear()` exige papel financeiro/dono via `AuthorizationProvider.can` (F-B) + justificativa ≥30 chars; cria `ClienteBloqueio` motivo `MANUAL`. |
| AC-CLI-004-2 | OK | `predicates_authz.py` declara predicate `cliente.bloqueado` (F-B); `models.py:208-212` property `bloqueado`. |
| AC-CLI-004-3 | OK | `management/commands/job_inadimplencia_alertas.py` Celery daily; cria `ClienteBloqueio` motivo `AUTOMATICO_INADIMPLENCIA_90D`; publica evento. |
| AC-CLI-004-4 | TRACK | régua D+30/60/89 depende de `comunicacao-omnichannel` (Wave A) — **GATE-CLI-5**. |
| AC-CLI-004-5 | TRACK | reativação depende de `financeiro/contas-receber` (módulo futuro) emitir `ContasReceber.Pago` — **GATE-CLI-6**. |
| AC-CLI-004-6 | OK | cada transição grava `authz_decisions` (F-B integration); `causation_id` rastreado. |
| AC-CLI-004-7 | ✅ FECHADO | **T-CLI-107** (2026-05-20): migration `audit/0011_bus_outbox.py` cria tabela com UNIQUE `(causation_id, acao)` + CHECK anti-PII em `acao` + CHECK envelope ≤64KiB + RLS FORCE com divergência justificada (modo_sistema cross-tenant pra worker). `event_helpers.publicar_evento(outbox=True)` faz INSERT idempotente no `transaction.atomic` do caller. |
| AC-CLI-004-8 | OK | spec cravada (não há código pra escrever — é regra de NÃO derivar do estado bloqueado). |
| **AC-CLI-004-9** | **GAP / módulo futuro** | **T-CLI-108**: consumer `operacao/agenda` ainda não existe — registrar como gate de habilitação Wave A; aqui só garantir que `Cliente.Bloqueado` carrega payload suficiente. |
| **AC-CLI-004-10** | **GAP / módulo futuro** | **T-CLI-109**: predicate `cliente.bloqueado_para_entrega` ausente; criar predicate isolado pra ser consumido pelo `operacao/certificados` (Marco futuro). |
| AC-CLI-004-11 | ✅ FECHADO | **T-CLI-110** (2026-05-20): `outbox_worker.processar_outbox_em_contexto_tenant` em 3 transações (Tx-1 tentativas + Tx-2 dispatch+processado_em + Tx-3 ultimo_erro sanitizado inline), garante `INV-TENANT-001..004` via `run_as_system`/`run_in_tenant_context`. Drill 3 tenants intercalados verde. |

### US-CLI-005 — Dedup manual

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| **AC-CLI-005-1** | **GAP** | **T-CLI-111**: GET `/clientes/{vencedor_id}/dedup/{perdedor_id}/` (comparação lado a lado + contagens) ausente. |
| AC-CLI-005-2 | OK | `views.py:194-285` `mesclar()` exige papel `atendente_senior`/`dono`; transação atômica + advisory lock por tenant. |
| **AC-CLI-005-3** | **GAP** | **T-CLI-103 (compartilhado)**: depende de `cliente_canonico_id` (mesmo conserto da AC-CLI-002-5); snapshot de certificado emitido é do módulo `operacao/certificados` (Marco futuro — interface acordada). |
| **AC-CLI-005-3b** | **GAP** | **T-CLI-112**: campos `tipo_mesclagem` + `evidencia_documental_id` ausentes; migration + validação no use case (M&A obriga anexo). |
| AC-CLI-005-4 | OK | evento `Cliente.Dedup.Mesclado` publicado em `mesclagem.py`; payload sanitizado (T-CLI-105 valida no helper). |
| AC-CLI-005-5 | OK | `mesclagem.py` verifica `soft_deleted_at IS NOT NULL` pra rejeitar re-dedup do perdedor. |
| AC-CLI-005-6 | TRACK | retenção 25a / WORM B2 — **GATE-CLI-1**: `retencao-matriz.md` promovida a stable + B2 ativo. |
| **AC-CLI-005-7** | **GAP** | **T-CLI-113**: trigger PG `cliente_canonico_imutavel` BEFORE UPDATE ausente; criar trigger validando transição self→vencedor_id_vivo + hook `cliente-canonico-imutavel.sh`. |

### US-CLI-006 — Direitos do titular (LGPD)

| AC | Estado | Evidência / ação |
|----|--------|------------------|
| **AC-CLI-006-1** | **GAP** | **T-CLI-114**: endpoints `POST /clientes/{id}/direitos-titular/{tipo}/` (8 tipos) ausentes; criar use cases + SLA 15 dias úteis (Res. CD/ANPD 2/2022). |
| **AC-CLI-006-2** | **GAP** | **T-CLI-115**: campo `consentimento_revogado_em` + endpoint `revogacao_consentimento` com efeito ≤1min ausentes. |
| **AC-CLI-006-3** | **GAP** | **T-CLI-116**: matriz eliminação vs anonimização ausente; use case `EliminarDadosDoTitular` aplica decisão por categoria (cadastro/NF/cert/audit). |
| **AC-CLI-006-4** | **GAP** | **T-CLI-117**: validador anti-PII sensível em `observacao` ausente; regex (saúde/biometria/genética/política/religião) fail-loud no serializer (LGPD art. 11). |
| **AC-CLI-006-5** | **GAP** | **T-CLI-118**: validador `data_nascimento < 18 anos` ausente; rejeitar no serializer (LGPD art. 14 + NG-CLI-12). |
| **AC-CLI-006-6** | **GAP** | **T-CLI-119**: evento `Cliente.PII.IncidenteDetectado` ausente no bus; criar + interface pra módulo de governança. |
| **AC-CLI-006-7** | **GAP** | **T-CLI-120**: modelo `OperacaoTratamentoCliente` ausente; criar + registrar em CADASTRO/EDICAO/EXPORT/COMPARTILHAMENTO_INTERMODULAR (LGPD art. 37). |

---

## Resumo P3 (atualizado 2026-05-20)

- **OK:** 24 (cadastro core, audit access, importação core, bloqueio core, dedup atomic).
- **GAP / FECHADO em P4:** 7 ✅ → T-CLI-101 + T-CLI-102 + T-CLI-103 + T-CLI-105 + T-CLI-107 + T-CLI-110 + T-CLI-113.
- **GAP / pendente:** 13 (T-CLI-104 + T-CLI-106 + T-CLI-108 + T-CLI-109 + T-CLI-111 + T-CLI-112 + T-CLI-114..120).
- **TRACK:** 6 (GATE-CLI-1..6 — Wave A; não bloqueia fechamento).

---

## Tarefas P4 (causa-raiz, sem mascaramento)

> Convenção: `T-CLI-1NN` (não conflita com `T-CLI-001..010` propostos no
> Explore — esses não foram cravados; usamos numeração nova). Cada
> tarefa **resolve a raiz**, nunca mascara (anti-padrão Constituição).

| T-CLI | AC | Conserto (raiz) | Bloqueia fechar Marco 1? |
|-------|----|-----------------|--------------------------|
| T-CLI-101 | AC-CLI-001-4 | migration alinhando enum (5 bases + 3 origens spec) + FK `lia_id` + helper de migração para Cliente legado (mapear `art_7_v→EXECUCAO_CONTRATO`, `art_7_i→CONSENTIMENTO`). | Sim — base legal incorreta = LGPD art. 8 §6. |
| T-CLI-102 | AC-CLI-001-7 | modelo `ClienteIdentidadeHistorico` + trigger PG anti-mutation + hook integração com PATCH (`nome`/`razao_social`). | Sim — ISO/IEC 17025 §7.8.2.1. |
| T-CLI-103 | AC-CLI-002-5 + AC-CLI-005-3 | `cliente_canonico_id` (migration nova) + função recursiva `resolver_cliente_canonico` (cap=10, fail-loud ciclo) + materialização preguiçosa via UPDATE em leitura + integração na visão 360. | Sim — INV-CLI-001 + SANEA-05. |
| T-CLI-104 | AC-CLI-002-6 | métrica `acessos_dados_cliente.gravacao_falhada_total` + alerta P1 (≥0.1%/5min) + drill que injeta falha de gravação verificando alerta dispara. | Sim — corretora §A. |
| T-CLI-105 | AC-CLI-002-7 + AC-CLI-001-5 (helper) | management command `job_contagem_diaria_acesso_pii` + `src/infrastructure/audit/event_helpers.py` (helper único, garantias 1-4 do plan §"Decisão arquitetural") + hook `event-helper-unico.sh`. | Sim — INV-013-A + SANEA-08. |
| T-CLI-106 | AC-CLI-003-7 | migration alinhando `aceite_lgpd_origem` enum + flag `pii_regularizacao_em` + use case de importação aceita base legal vinda da chamada. | Sim — advogado §D. |
| T-CLI-107 | AC-CLI-004-7 | tabela `bus_outbox` (migration nova) + worker dedicado + adoção pelo use case `bloquear()`. | Sim — INV-INT-010. |
| T-CLI-108 | AC-CLI-004-9 | payload `Cliente.Bloqueado` carrega `agendamentos_futuros: List[UUID]` (resolvido por query no momento da emissão; consumer `operacao/agenda` futuro). | Não (módulo futuro) — vira **GATE-CLI-7** rastreado. |
| T-CLI-109 | AC-CLI-004-10 | predicate `cliente.bloqueado_para_entrega` em `predicates_authz.py`; consumível pelo módulo futuro `operacao/certificados`. | Não — gate **GATE-CLI-8** rastreado. |
| T-CLI-110 | AC-CLI-004-11 | helper `processar_outbox_em_contexto_tenant` em `src/infrastructure/audit/outbox_worker.py` + teste multi-tenant (3 tenants intercalados, ZERO vazamento). | Sim. |
| T-CLI-111 | AC-CLI-005-1 | GET endpoint comparação lado a lado + use case + serializer. | Sim. |
| T-CLI-112 | AC-CLI-005-3b | migration `tipo_mesclagem` + `evidencia_documental_id` + validação no use case (M&A obrigatório anexo). | Sim — consultor-rbc §C. |
| T-CLI-113 | AC-CLI-005-7 | trigger PG `cliente_canonico_imutavel` BEFORE UPDATE + hook `cliente-canonico-imutavel.sh`. | Sim — defesa em profundidade. |
| T-CLI-114 | AC-CLI-006-1 | endpoints `direitos-titular/{tipo}/` (8 tipos) + use cases + SLA 15 dias. | Sim — LGPD art. 18 (pré-condição dogfooding PII real). |
| T-CLI-115 | AC-CLI-006-2 | campo `consentimento_revogado_em` + endpoint imediato; bases CONSENTIMENTO viram inaplicáveis. | Sim — LGPD art. 8 §5º. |
| T-CLI-116 | AC-CLI-006-3 | use case `EliminarDadosDoTitular` aplica matriz; helper `anonimizar_em_lugar` + helper `eliminar_efetivamente` (DELETE cascade respeitando audit). | Sim — LGPD art. 18 VI + 16 I/II/III. |
| T-CLI-117 | AC-CLI-006-4 | validador anti-PII sensível em `observacao` (regex + lista de termos curados); fail-loud 400. | Sim — LGPD art. 11 + NG-CLI-11. |
| T-CLI-118 | AC-CLI-006-5 | validador `data_nascimento < 18` (timezone tenant) no serializer. | Sim — LGPD art. 14 + NG-CLI-12. |
| T-CLI-119 | AC-CLI-006-6 | evento `Cliente.PII.IncidenteDetectado` no bus + helper de emissão a partir de hook de erro. | Sim — Res. ANPD 15/2024. |
| T-CLI-120 | AC-CLI-006-7 | modelo `OperacaoTratamentoCliente` + middleware/interceptor que grava CADASTRO/EDICAO/EXPORT/COMPARTILHAMENTO. | Sim — LGPD art. 37. |

**20 T-CLI no total — todas causa-raiz, nenhuma "aceitável".**

---

## Gates Wave A rastreados (TRACK — não bloqueiam Marco 1)

| Gate | Item | Onde rastrear |
|------|------|---------------|
| GATE-CLI-1 | `retencao-matriz.md` promovida a stable + B2 WORM ativo | `docs/conformidade/comum/retencao-matriz.md` + foundation-waves |
| GATE-CLI-2 | `EventoTimeline` materializada por consumers de outros módulos | Wave A (depende de OS/Cert/Fatura) |
| GATE-CLI-3 | SLA p95<1.5s visão-360 com cursor de paginação medido em produção | observabilidade Wave A |
| GATE-CLI-4 | Dashboard regularização (`aceite_lgpd_origem=IMPORTACAO_LEGADA`) | Wave A admin |
| GATE-CLI-5 | régua D+30/60/89 (consumer `comunicacao-omnichannel`) | Wave A módulo futuro |
| GATE-CLI-6 | reativação automática via `ContasReceber.Pago` | Wave A `financeiro/contas-receber` |
| GATE-CLI-7 | consumer `operacao/agenda` cancela futuro em Cliente.Bloqueado | Wave A módulo futuro |
| GATE-CLI-8 | consumer `operacao/certificados` consulta `cliente.bloqueado_para_entrega` | Wave A módulo futuro |

---

## Próximo passo

P4 executa T-CLI-101..120 (causa-raiz), commits atômicos por tarefa,
suíte verde + hooks + `validar_f_a` + `validar_m1_clientes` (novo) +
`makemigrations --check` limpo + drill multi-tenant. Então P5 (10
auditores Família 5, loop até zero CRÍTICO/ALTO/MÉDIO).

P4 é trabalho extenso (20 T-CLI tocando migrations, modelos, use cases,
endpoints novos, triggers PG, hooks). Estimativa honesta: várias sessões
de implementação. Cada T-CLI ganha commit próprio.
