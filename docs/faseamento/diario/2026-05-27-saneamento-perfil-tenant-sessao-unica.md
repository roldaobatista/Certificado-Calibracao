---
owner: roldao
status: stable
revisado-em: 2026-05-27
diataxis: explanation
audiencia: agente
tipo: diario-sessao
relacionados:
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/faseamento/SAN-PERFIL-TENANT/spec.md
  - docs/faseamento/SAN-PERFIL-TENANT/plan.md
  - docs/faseamento/SAN-PERFIL-TENANT/tasks.md
---

# Diário 2026-05-27 — Saneamento SAN-PERFIL-TENANT em sessão única

## Gatilho

Roldão pediu: "faca uma auditoria com 10 agentes diferentes; veja se o sistema grava o tipo de empresa, se vai agir conforme, se tem os templates de certificado para cada tipo de empresa, se o sistema inteiro vai se adaptar a cada tipo".

A pergunta era simples; a resposta provou ser estrutural.

## Auditoria 10 lentes — 10/10 FAIL

10 agentes paralelos (tech-lead, advogado, corretora, RBC, drift-docs, segurança, performance, observabilidade, idempotência, conformidade-LGPD) auditaram a mesma pergunta sob perspectivas diferentes. Resultado:

| Lente | Veredito | Achado-chave |
|---|---|---|
| L1 Modelo de dados | FAIL ALTO | Campo `Tenant.perfil_regulatorio` não existe. ADR-0006:39 e ADR-0009:27 já citavam `tenant.perfil` como se existisse — referência fantasma. |
| L2 M4 calibração | CONCERN ALTO | M4 colapsou 4 perfis em binário RBC/NAO_RBC NO NÍVEL DA CALIBRAÇÃO. |
| L3 Templates certificado | CONCERN ALTO | Sem campo + sem template diferenciado = Perfil B/C/D podia emitir certificado com selo RBC. |
| L4 Drift PRD vs código | FAIL ALTO | 8 drifts. Trilha D→A (BIG-03 do discovery) atravessou 7 Marcos sem 1 linha de código. |
| L5 Onboarding/migração | FAIL **CRÍTICO** | Sem comando `provisionar_tenant`. Snapshot existia no nível ERRADO (equipamento, não tenant). |
| **L6 Autorização/fraude** | **FAIL ALTO** | Predicate `cmc_cobre` recebia `tipo_acreditacao` do **payload JSON da request**. Self-attestation = fraude documental viável. |
| L7 Billing/contrato | FAIL ALTO | DAP varia 10x mas sistema cobrava igual. Contrato único viola CDC art. 39 V. |
| L8 LGPD retenção | FAIL ALTO | Retém 25a para todos — over-retention LGPD art. 6º III em perfil D. |
| L9 Testes | FAIL ALTO | Cobertura: D 100% / C <1% / B 0% / A 5%. |
| L10 Observabilidade | CONCERN MÉDIO | 5 KPIs estratégicos inviáveis (trilha D→A, ARPU por perfil, etc). |

## Decisão estratégica — manter 4 perfis + consertar agora

Via AskUserQuestion, Roldão decidiu:
1. **Manter os 4 perfis A/B/C/D** (confirma PRD; trilha D→A vira feature codificada — diferencial competitivo principal).
2. **Consertar agora, antes de Wave A** (não diferir).

ADR-0067 redigida e aceita 2026-05-27.

## Ritual Spec Kit completo

- **P1** spec.md inicial (5 USs).
- **P2** 4 reviews paralelos (tech-lead-saas-regulado / advogado-saas-regulado / corretora-seguros-saas / consultor-rbc-iso17025) — **41 achados** (13 BLOQ + 17 MÉDIO + 10 ALTO + 1 ACEITE).
- **P3** plan.md absorvendo achados + spec.md reescrita por causa-raiz (9 USs, 7 INVs, 5 hooks, 18 gates).
- **P4** tasks.md (62 tasks T-SAN-PERFIL-001..062 ordenadas por sprint).
- **P5** implementação — Sprints 1-4 entregues em sessão única.

## Sprints 1-4 — entregues

### Sprint 1 (commit `87bbc64` — junto com Sprint 2)

Schema multi-step (T1 plan.md) + funções SECURITY DEFINER + tabela append-only:
- 7 migrations (`tenant/0003..0009`) + 1 cosmética Django auto-gerada (`0010`).
- `Tenant.perfil_regulatorio CHAR(1) NOT NULL CHECK A/B/C/D`.
- Colunas auxiliares: `acreditacao_cgcre_numero` (regex `CRL NNNN`), `acreditacao_suspensa_em/ate`, `ilac_mra_aderido`.
- Tabela `tenant_perfil_historico` (append-only via 2 triggers PL/pgSQL).
- 2 funções SECURITY DEFINER: `aplicar_evento_cgcre()` (8 validações de transição + advisory lock + outbox) e `rebaixar_perfil_tenant_voluntario_cliente()` (cooldown 30d + pré-aviso 7d).
- Hook `tenant-perfil-imutavel-check.sh` (13 casos test runner).
- Drill `validar_san_perfil_tenant_migrations`: **17/17 PASS** no PG real.

### Sprint 2 (commit `87bbc64`)

Predicate canônico + retrofit `cmc_cobre` fechando FAIL L6:
- `perfil_tenant_context: ContextVar[str]` em `multitenant/context.py`.
- `TenantMiddleware` popula contexto + método `_resolver_perfil_active_tenant` (cache 1 SELECT/request, elimina N+1).
- `src/infrastructure/authz/perfil_tenant_helper.py` — `obter_perfil_tenant_corrente()` (ContextVar primário + fallback DB timeout 50ms + fail-closed) + `tenant_perfil_e(perfis_aceitos)`.
- **Retrofit `cmc_cobre`**: deixa de ler `tipo_acreditacao` do payload, passa a consultar tenant. Compat-shim com WARN log para payload legado. Operador em B/C/D enviando `RBC` no JSON recebe `tipo_acreditacao_divergente_do_tenant`.
- Hook `payload-tipo-acreditacao-obsoleto-check.sh` (11 casos test runner).
- `TenantFactory` traits `.perfil_a/b/c/d` + fixtures `tenant_a/b/c/d` em conftest.
- INV-TENANT-PERFIL-001..007 em `REGRAS-INEGOCIAVEIS.md`.
- 23 testes regressão em `tests/regressao/test_inv_tenant_perfil_001_007.py`.

### Sprint 3 (commit `f51fe47`)

Provisioning + matriz + job vigência:
- Comando `provisionar_tenant` com flags obrigatórias `--perfil` + `--motivo` ≥100 chars; Perfil A exige adicionalmente `--numero-rbc` (regex `CRL NNNN`) + `--certificado-acreditacao-pdf-path` + `--auditor-cgcre-nome` + `--processo-cgcre-numero` + `--ilac-mra-aderido`. Env `AFERE_OPERADOR_HUMANO_CPF/NOME` OU flag `--autorizado-por-roldao-issue-id` (ADR-0019).
- Job procrastinate `verificar_vigencia_acreditacao_perfil_a` — função pura, 3 severidades (AVISO/CRITICO/INCONSISTENCIA).
- Matriz canônica `docs/conformidade/comum/matriz-feature-perfil.md` (14 features + 4 camadas retenção + 6 direções mudança perfil + resolve conflito ADR-0064 HMAC 25a × PII por perfil).
- Hook `feature-perfil-matriz-validator.sh` (9 casos test runner).
- Emenda ADR-0015 — etapa 0 `COLETA_PERFIL_REGULATORIO` (7→8 etapas).
- Runbook `docs/runbooks/dpo-encarregado-resposta-padrao.md` (4 cenários LGPD com base legal nomeada).
- Retrofit `popular_drill` — tenants drill recebem perfil B explícito.

### Fix M4 pré-existentes (commit `de5877f` — entre Sprint 2 e 3)

Não relacionado ao saneamento mas detectado na validação:
- 7 testes `test_m4_uc_subcontratacao.py` — `RegistrarRecebimentoSubcontratadoInput.actor_user_id` faltando (M4 P5 batch S4+S5 introduziu campo, testes não atualizados).
- 1 enum `ClienteNotificadoVia.NAO_APLICA` faltando.

### Sprint 4 (commit `694ce27`)

Snapshot WORM + retrofit equipamento + evidência defensiva:
- **Decisão de design revisada (T4 plan.md):** PostgreSQL não suporta subquery em `GENERATED ALWAYS AS STORED`. Substituído por trigger BEFORE INSERT lendo `current_setting('app.perfil_tenant')` + aplicação populando via ContextVar (defesa em camadas).
- GUC PG novo `app.perfil_tenant` em `setar_contexto_pg_na_conexao` + middleware passa perfil.
- 3 migrations adicionando `perfil_no_evento CHAR(1) NULL` em audit/evento_de_calibracao/evento_de_os + 3 triggers BEFORE INSERT.
- Coluna `escopos_acreditados_vigentes_no_momento JSONB` em evento_de_calibracao (R7 plan.md — NIT-DICLA-030 item 8.2.6 — auditor CGCRE pode reconstruir escopo vigente em data passada).
- Retrofit `registrar_auditoria()` lê perfil via ContextVar.
- Retrofit `criar_equipamento` deriva perfil do Tenant pra snapshot (fecha FAIL L5).
- Retrofit `geo_truncamento_calibracao_5a` — Perfil A nunca trunca (R10/AC-005-6).
- Drill `validar_san_perfil_tenant_snapshots`: **6/6 PASS** no PG real.
- Comando `validar_san_perfil_tenant_eventos_historicos` (relatório CSV+A3 evidência defensiva A4) — exportou 1 evento pré-saneamento.

## Validações cumulativas (PG real)

- Drill migrations 17/17 PASS.
- Drill snapshots 6/6 PASS (Sprint 4).
- Suite ampla regression+audit+M3+M4 = exit 0.
- Hooks `_test-runner.sh` = 414/414 PASS / 51 hooks ativos (+3 ADR-0067).
- Smoke real `provisionar_tenant` Perfil A criou tenant; trigger anti-mutation bloqueou DELETE no histórico (defesa em camadas funcionando).

## O que ficou para Wave A

Sprints 5-6 (módulos novos `certificados`, `onboarding`, `direitos-titular`) + 12 ADRs em proposta para aceite + autorização Roldão.

## Lições

- **Auditoria multi-lente antes de codar pega lacuna estrutural que ritual normal não pega.** Os 10 reviews paralelos do P2 produziram 41 achados de várias perspectivas — densidade maior que ritual normal de Marco (M4 fechou com 45 achados em 4 reviews).
- **Defesa em camadas no banco vale o overhead.** Trigger PL/pgSQL anti-mutation bloqueou DELETE direto no smoke test — sinal de que a invariante está enforced de verdade, não só "esperada".
- **Causa-raiz, nunca sintoma.** FAIL L6 (fraude documental) podia ter sido mascarado com validação adicional no payload; foi consertado removendo o payload da fonte da verdade (predicate consulta tenant agora).
- **Geografia também era drift.** No início da sessão, Roldão corrigiu "Mato Grosso, não Sudeste" — drift documental herdado de halo founder errado. Mesma sessão, fix incluso no commit `de229b8`.

## Próximo passo

Wave A propriamente — aguarda autorização Roldão.
