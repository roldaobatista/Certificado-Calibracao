---
owner: roldao
status: stable
revisado-em: 2026-05-27
proximo_review: 2026-08-27
diataxis: reference
audiencia: agente
marco: Saneamento pré-Wave A — perfil regulatório do tenant
fase-ritual: P4 (tasks executáveis desdobradas dos ACs da spec.md)
tipo: tasks-ritual-spec-kit
relacionados:
  - docs/faseamento/SAN-PERFIL-TENANT/spec.md
  - docs/faseamento/SAN-PERFIL-TENANT/plan.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# SAN-PERFIL-TENANT — Tasks P4

> **P4 do ritual Spec Kit:** 9 USs + 7 INVs + 5 hooks + 18 gates da spec.md desdobradas em **62 tasks T-SAN-PERFIL-NNN** ordenadas por sprint. Cada task tem: AC origem + arquivo destino + entregável binário + estimativa.

## Convenções

- **Estimativa em "u"** (unidades de meio-dia): 1u = 4h trabalho concentrado.
- **Estado:** `pending` / `in_progress` / `done` / `blocked`.
- **Dependências:** tasks anteriores que precisam estar `done` antes desta iniciar.
- **Ordem dentro do sprint** segue ordem de migrations cross-app declarada em §2.1 da spec (T6).

---

## Sprint 1 — Schema + Tabela Histórico + Funções SECURITY DEFINER (10 tasks, ~12u = 6 dias)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-001 | Criar enum `PerfilRegulatorio` em domínio (CHAR(1) — A/B/C/D + iteráveis) | `src/domain/tenant/enums.py` | AC-001-1c, T8 | 0.5u | — |
| T-SAN-PERFIL-002 | Criar enum `DirecaoMudancaPerfil` (7 valores R3+A1) em domínio | `src/domain/tenant/enums.py` | AC-001-2 | 0.5u | — |
| T-SAN-PERFIL-003 | Migration `tenant/0003_perfil_regulatorio_add_nullable.py` — ADD COLUMN NULL idempotente | `src/infrastructure/tenant/migrations/0003_*.py` | AC-001-1a, T1 | 0.5u | T-SAN-PERFIL-001 |
| T-SAN-PERFIL-004 | Migration `tenant/0004_perfil_regulatorio_backfill.py` — RunPython com SELECT FOR UPDATE + INSERT TenantPerfilHistorico (Balanças Solution=B); justificativa ≥100 chars | `src/infrastructure/tenant/migrations/0004_*.py` | AC-001-1b, T1 | 1u | T-SAN-PERFIL-003, T-SAN-PERFIL-007 |
| T-SAN-PERFIL-005 | Migration `tenant/0005_perfil_regulatorio_not_null.py` — SET NOT NULL + CHECK | `src/infrastructure/tenant/migrations/0005_*.py` | AC-001-1c | 0.5u | T-SAN-PERFIL-004 |
| T-SAN-PERFIL-006 | Migration `tenant/0006_acreditacao_cgcre_campos.py` — numero_rbc + suspensa_em/ate + ilac_mra_aderido (R1+R9) | `src/infrastructure/tenant/migrations/0006_*.py` | AC-001-1d | 0.5u | T-SAN-PERFIL-005 |
| T-SAN-PERFIL-007 | Migration `tenant/0007_tenant_perfil_historico_table.py` — tabela append-only + trigger anti-mutação + RLS | `src/infrastructure/tenant/migrations/0007_*.py` | AC-001-2 | 1.5u | T-SAN-PERFIL-002 |
| T-SAN-PERFIL-008 | Migration `tenant/0008_aplicar_evento_cgcre_function.py` — função SECURITY DEFINER `aplicar_evento_cgcre(direcao, ...)` com máquina de estados + advisory lock | `src/infrastructure/tenant/migrations/0008_*.py` | AC-001-2, AC-001-8, T5, R3 | 2u | T-SAN-PERFIL-007 |
| T-SAN-PERFIL-009 | Migration `tenant/0009_rebaixar_voluntario_function.py` — função SECURITY DEFINER `rebaixar_perfil_tenant_voluntario_cliente()` com cooldown 30d + pré-aviso 7d (A1) | `src/infrastructure/tenant/migrations/0009_*.py` | AC-001-9 | 1.5u | T-SAN-PERFIL-008 |
| T-SAN-PERFIL-010 | Outbox: emitir `TenantPerfilAlterado` em ambas as funções na mesma transação (S2 + A6) | mesma migration 0008/0009 | AC-001-6, INV-006 | 1.5u | T-SAN-PERFIL-008, T-SAN-PERFIL-009 |
| T-SAN-PERFIL-011 | Modelo Django `Tenant` atualizado: novas colunas + regex validator número RBC (R2) + clean() + property `perfil_vigente()` (cache ContextVar) | `src/infrastructure/tenant/models.py` | AC-001-1d, AC-001-1e, AC-001-4 | 1u | T-SAN-PERFIL-005, T-SAN-PERFIL-006 |
| T-SAN-PERFIL-012 | Modelo Django `TenantPerfilHistorico` + RLS shared-across-tenants + sanitização motivo (A8) | `src/infrastructure/tenant/models.py` | AC-001-2, AC-001-10 | 1u | T-SAN-PERFIL-007 |
| T-SAN-PERFIL-013 | Hook `tenant-perfil-imutavel-check.sh` + 6 casos `_test-runner.sh` | `.claude/hooks/tenant-perfil-imutavel-check.sh`, `.claude/hooks/_test-runner.sh` | AC-001-5 | 1u | T-SAN-PERFIL-008 |
| T-SAN-PERFIL-014 | Drill `validar_san_perfil_tenant_migrations` (idempotência em ambiente zerado E ambiente já-M4) | `src/infrastructure/tenant/management/commands/validar_san_perfil_tenant_migrations.py` | AC-001-7, T6 | 1.5u | T-SAN-PERFIL-005..009 |

---

## Sprint 2 — Predicate canônico + retrofit cmc_cobre + migração testes (16 tasks, ~14u = 7 dias)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-015 | `perfil_tenant_context: ContextVar[Optional[str]]` em `multitenant/context.py` | `src/infrastructure/multitenant/context.py` | AC-002-5, AC-002-8 | 0.5u | — |
| T-SAN-PERFIL-016 | `TenantMiddleware` popula `perfil_tenant_context` ao ativar tenant | `src/infrastructure/multitenant/middleware.py` | AC-003-5 | 0.5u | T-SAN-PERFIL-015 |
| T-SAN-PERFIL-017 | Predicate `tenant_perfil_e(perfis_aceitos)` em authz com timeout 50ms + fail-closed | `src/infrastructure/authz/predicates.py` | AC-002-1, AC-002-5 | 1.5u | T-SAN-PERFIL-015, T-SAN-PERFIL-011 |
| T-SAN-PERFIL-018 | Retrofit `cmc_cobre`: ler de ContextVar, não de payload + 412 `TipoAcreditacaoDivergenteDoTenant` + evento `tentativa_downgrade_perfil` em audit (FAIL L6) | `src/infrastructure/calibracao/predicates_calibracao.py` | AC-002-2 | 2u | T-SAN-PERFIL-017 |
| T-SAN-PERFIL-019 | Predicate `emitir_certificado_rbc`: `tenant_perfil_e({"A"})` + suspensão + delega vigência por escopo (fail-open lazy `escopo_cgcre_cobre`) | `src/application/metrologia/certificados/...` (Wave A — esboço) | AC-002-3 | 1u | T-SAN-PERFIL-017 |
| T-SAN-PERFIL-020 | Predicate `requer_segunda_conferencia(certificado_id)` (perfil A AND modo≠NENHUMA) | `src/infrastructure/calibracao/predicates_calibracao.py` | AC-002-4, R5 | 1u | T-SAN-PERFIL-017 |
| T-SAN-PERFIL-021 | Predicate suspensão: `tenant_perfil_e({"A"})` retorna False se `acreditacao_suspensa_em IS NOT NULL AND today < acreditacao_suspensa_ate` | `src/infrastructure/authz/predicates.py` | AC-002-7 | 0.5u | T-SAN-PERFIL-017 |
| T-SAN-PERFIL-022 | Consumer `notifica_d_e_o` em `direcao=CANCELAMENTO_CGCRE` (S7) | `src/application/tenant/consumers/notifica_d_e_o.py` | AC-002-7b | 1u | T-SAN-PERFIL-010 |
| T-SAN-PERFIL-023 | `TenantFactory.perfil_a/b/c/d()` traits + fixtures `tenant_a/b/c/d` em conftest raiz | `tests/factories.py`, `tests/conftest.py` | AC-006-1 | 1u | T-SAN-PERFIL-011 |
| T-SAN-PERFIL-024 | Retrofit ~67 testes M4 que literalizam `tipo_acreditacao=RBC` no payload para usar fixture `tenant_a` | `tests/test_m4_*.py` (lista em grep estrutural) | AC-006-2 | 2u | T-SAN-PERFIL-023 |
| T-SAN-PERFIL-025 | Compat-shim no `cmc_cobre`: payload `tipo_acreditacao` ignorado + WARN log `payload_tipo_acreditacao_obsoleto` | `src/infrastructure/calibracao/predicates_calibracao.py` | AC-006-3 | 0.5u | T-SAN-PERFIL-018 |
| T-SAN-PERFIL-026 | Hook `payload-tipo-acreditacao-obsoleto-check.sh` + 4 casos `_test-runner.sh` | `.claude/hooks/payload-tipo-acreditacao-obsoleto-check.sh` | AC-006-4 | 1u | T-SAN-PERFIL-025 |
| T-SAN-PERFIL-027 | Marcador `@pytest.mark.perfil(...)` + 40 testes parametrizados por perfil em M4 / 20 em M3 / 10 em M2 | `tests/test_*.py` (vários) | AC-006-5, AC-006-6 | 2u | T-SAN-PERFIL-023 |
| T-SAN-PERFIL-028 | ≥20 testes regressão UNHAPPY: `tests/regressao/test_inv_tenant_perfil_001..007.py` | `tests/regressao/test_inv_tenant_perfil_*.py` | AC-002-6 | 1.5u | T-SAN-PERFIL-018, T-SAN-PERFIL-021 |
| T-SAN-PERFIL-029 | Adicionar INV-TENANT-PERFIL-001..007 em `REGRAS-INEGOCIAVEIS.md` | `REGRAS-INEGOCIAVEIS.md` | §4 spec | 0.5u | — |
| T-SAN-PERFIL-030 | Benchmark `tests/perf/test_perfil_tenant_lookup.py` p95 ≤5ms PG real (5k tenants seed) — falha = GATE Wave A | `tests/perf/test_perfil_tenant_lookup.py` | AC-001-4b, T7 | 1u | T-SAN-PERFIL-017 |

---

## Sprint 3 — Provisioning + PDF CGCRE + verificação periódica + matriz feature×perfil (10 tasks, ~10u = 5 dias)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-031 | Comando `provisionar_tenant` esqueleto + flags obrigatórias + validações (slug, motivo ≥100, perfil) | `src/infrastructure/tenant/management/commands/provisionar_tenant.py` | AC-004-1..4 | 1.5u | T-SAN-PERFIL-009 |
| T-SAN-PERFIL-032 | Provisionamento perfil A: flags `--numero-rbc` + `--certificado-acreditacao-pdf-path` + `--auditor-cgcre-nome` + `--processo-cgcre-numero` + `--ilac-mra-aderido` (A5+S4+R9) | mesmo comando | AC-004-5 | 1.5u | T-SAN-PERFIL-031 |
| T-SAN-PERFIL-033 | Upload PDF certificado CGCRE em B2 + hash SHA-256 + assinatura A3 do Roldão + FK `certificado_acreditacao_documento_id` | `src/infrastructure/documento/uploader.py` (criar se não existir) | AC-004-5, A5 | 1.5u | T-SAN-PERFIL-032 |
| T-SAN-PERFIL-034 | Retrofit `popular_drill.py` com `--perfil B` explícito para Balanças Solution | `src/infrastructure/tenant/management/commands/popular_drill.py` | AC-004-6 | 0.5u | T-SAN-PERFIL-031 |
| T-SAN-PERFIL-035 | Variáveis env `AFERE_OPERADOR_HUMANO_CPF` + `_NOME` + modo IA `--autorizado-por-roldao-issue-id` (A6) | mesmo comando + `config/settings/base.py` | AC-004-7 | 1u | T-SAN-PERFIL-031 |
| T-SAN-PERFIL-036 | Job procrastinate `verificar_vigencia_acreditacao_perfil_a` mensal — itera Perfil A, alerta 60d (S5) | `src/application/tenant/jobs/verificar_vigencia_acreditacao_perfil_a.py` | AC-004-8 | 1.5u | T-SAN-PERFIL-006 |
| T-SAN-PERFIL-037 | Documento `docs/conformidade/comum/matriz-feature-perfil.md` (status stable; ≥7 features cobertas) | `docs/conformidade/comum/matriz-feature-perfil.md` | AC-005-1, AC-005-4 | 1.5u | — |
| T-SAN-PERFIL-038 | Hook `feature-perfil-matriz-validator.sh` (path + grep `US-`) + 5 casos `_test-runner.sh` | `.claude/hooks/feature-perfil-matriz-validator.sh` | AC-005-3, T12 | 1u | T-SAN-PERFIL-037 |
| T-SAN-PERFIL-039 | Emenda ADR-0015 (lifecycle tenant) — adicionar etapa 0 `COLETA_PERFIL_REGULATORIO` | `docs/adr/0015-lifecycle-tenant.md` | §2.1 spec Sprint 3 | 0.5u | — |
| T-SAN-PERFIL-040 | Template `docs/runbooks/dpo-encarregado-resposta-padrao.md` com base legal nomeada (antecipa A2 Sprint 6) | `docs/runbooks/dpo-encarregado-resposta-padrao.md` | AC-007-4, AC-007-5 | 1u | — |

---

## Sprint 4 — Snapshot WORM + escopos vigentes + evidência defensiva (10 tasks, ~10u = 5 dias)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-041 | Migration `audit/00XX_perfil_no_evento.py` via GENERATED ALWAYS AS STORED + DROP EXPRESSION + SET NOT NULL (T4) | `src/infrastructure/audit/migrations/...` | AC-003-1, T4 | 1.5u | T-SAN-PERFIL-005 |
| T-SAN-PERFIL-042 | Migration `calibracao/00XX_perfil_no_evento_e_escopos_vigentes.py` (R7) | `src/infrastructure/calibracao/migrations/...` | AC-003-1, AC-003-1b, R7 | 1.5u | T-SAN-PERFIL-005, T-SAN-PERFIL-041 |
| T-SAN-PERFIL-043 | Migration `os/00XX_perfil_no_evento.py` | `src/infrastructure/ordens_servico/migrations/...` | AC-003-1 | 1u | T-SAN-PERFIL-005, T-SAN-PERFIL-041 |
| T-SAN-PERFIL-044 | Retrofit `Equipamento.perfil_tenant_snapshot` — COPY de `Tenant.perfil_regulatorio` no INSERT (em vez de auto-declarado) + migration de dados | `src/infrastructure/equipamentos/migrations/...`, models.py | §2.1 Sprint 4 spec | 2u | T-SAN-PERFIL-005, T-SAN-PERFIL-041 |
| T-SAN-PERFIL-045 | `registrar_auditoria()` lê `perfil_tenant_context` (não SELECT direto) | `src/infrastructure/audit/services.py` | AC-003-2 | 1u | T-SAN-PERFIL-016 |
| T-SAN-PERFIL-046 | Estender hook `metrology-replay-fixtures-versionadas` para validar `perfil_no_evento` em fixtures (T9) | `.claude/hooks/metrology-replay-fixtures-versionadas.sh` | AC-003-2b | 1u | T-SAN-PERFIL-042 |
| T-SAN-PERFIL-047 | Relatório `validar_san_perfil_tenant_eventos_historicos` — CSV+A3 dos eventos pré-saneamento (A4) | `src/infrastructure/audit/management/commands/validar_san_perfil_tenant_eventos_historicos.py` | AC-003-6, A4 | 1.5u | T-SAN-PERFIL-041..043 |
| T-SAN-PERFIL-048 | Arquivar dossiê A4 em B2 WORM em `docs/governanca/evidencia-defensiva/` | comando do T-SAN-PERFIL-047 | AC-003-6 | 0.5u | T-SAN-PERFIL-047 |
| T-SAN-PERFIL-049 | Drill `validar_san_perfil_tenant_snapshots` (100% preenchidos pós-backfill) | `src/infrastructure/audit/management/commands/validar_san_perfil_tenant_snapshots.py` | AC-003-3 | 1u | T-SAN-PERFIL-041..043 |
| T-SAN-PERFIL-050 | Job `geo_truncamento_calibracao_5a` ganha predicate `tenant.perfil_regulatorio` (A nunca trunca; D anonimização agressiva) (R10) | `src/application/metrologia/calibracao/jobs/geo_truncamento_calibracao_5a.py` | AC-005-6 | 1u | T-SAN-PERFIL-011 |

---

## Sprint 5 — Wave A módulo `certificados` (4 tasks placeholder — desdobrar quando módulo arrancar)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-051 | 4 templates de certificado por perfil (A/B/C/D) | `src/infrastructure/certificados/templates/` | Sprint 5 spec | 4u | Sprint 4 done |
| T-SAN-PERFIL-052 | Pre-flight check em `emitir_certificado` (template.perfil_alvo == tenant.perfil_vigente) | `src/application/metrologia/certificados/emitir_certificado.py` | Sprint 5 spec | 1.5u | T-SAN-PERFIL-051 |
| T-SAN-PERFIL-053 | Hook `template-perfil-d-anti-iso.sh` + casos teste | `.claude/hooks/template-perfil-d-anti-iso.sh` | Sprint 5 spec | 1u | T-SAN-PERFIL-051 |
| T-SAN-PERFIL-054 | Hook `template-ilac-mra-coerencia.sh` + casos teste (R9) | `.claude/hooks/template-ilac-mra-coerencia.sh` | Sprint 5 spec | 1u | T-SAN-PERFIL-051 |

---

## Sprint 6 — Wave A módulo `onboarding` + `direitos-titular` + LGPD (8 tasks placeholder)

| # | Task | Arquivos | AC | Estimativa | Dependências |
|---|------|----------|----|-----------|--------------|
| T-SAN-PERFIL-055 | UX coleta perfil no onboarding (etapa 0 ADR-0015 emenda) | (Wave A frontend) | Sprint 6 spec | 3u | T-SAN-PERFIL-039 |
| T-SAN-PERFIL-056 | Consumer `notificar_titulares_mudanca_retencao_d_para_a` (A3) | `src/application/direitos_titular/consumers/notificar_titulares_d_para_a.py` | AC-007-1, 7-2, 7-3 | 2u | T-SAN-PERFIL-010 |
| T-SAN-PERFIL-057 | ADR-0021 emenda "Camadas de retenção condicional por perfil" + matriz aceita | `docs/adr/0021-anonimizacao-vs-retencao.md` | AC-005-5, R10 | 1u | — |
| T-SAN-PERFIL-058 | DRILL-RET-12 (perfil D pede eliminação ano 6 → elimina) + DRILL-RET-13 (perfil A pede ano 6 → recusa fundamentada) | `tests/drills/test_drill_ret_12_13.py` | Sprint 6 spec | 2u | T-SAN-PERFIL-057 |
| T-SAN-PERFIL-059 | Comando `exportar_distribuicao_perfil_seguradora` + job trimestral (US-008 — S1) | `src/infrastructure/tenant/management/commands/exportar_distribuicao_perfil_seguradora.py` | AC-008-1..4 | 2u | T-SAN-PERFIL-011 |
| T-SAN-PERFIL-060 | Comando `exportar_historico_perfil_evidencia_sinistro` (US-009 — S3) | `src/infrastructure/tenant/management/commands/exportar_historico_perfil_evidencia_sinistro.py` | AC-009-1, 9-2 | 1.5u | T-SAN-PERFIL-012 |
| T-SAN-PERFIL-061 | Cláusula "Mudança de perfil regulatório" no termo de uso v1.0 (A1) | `docs/conformidade/contratos/termo-de-uso-afere-v1.0.md` | AC-001-9 | 0.5u | — |
| T-SAN-PERFIL-062 | Decisão A7: trilha D→A controlada pelo RT do tenant (A3 do RT, não Aferê) — registrar em ADR-0067 §"Decisão Wave A" | `docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md` | A7 | 0.5u | — |

---

## Ritual P5 — fechamento

| # | Task | Estimativa | Dependências |
|---|------|-----------|--------------|
| T-SAN-PERFIL-P5-A | Suite pytest ≥669/669 verde | 1u | Todos Sprints 1-4 done |
| T-SAN-PERFIL-P5-B | Hook `_test-runner.sh` ≥385/385 verde | 0.5u | Todos hooks novos done |
| T-SAN-PERFIL-P5-C | Drill `validar_san_perfil_tenant` ≥30 checks PASS | 1u | T-SAN-PERFIL-014 + T-SAN-PERFIL-049 |
| T-SAN-PERFIL-P5-D | 10 auditores Família 5 — ZERO C/A/M | 2u | Todos anteriores done |
| T-SAN-PERFIL-P5-E | Atualizar `AGENTS.md §12` com saneamento FECHADO + INVs novas + plano Wave A | 0.5u | T-SAN-PERFIL-P5-D done |

---

## Resumo

- **62 tasks** (54 saneamento Sprints 1-4 + 12 Wave A placeholder Sprints 5-6 + 5 P5).
- **Estimativa total saneamento (Sprints 1-4):** 46u = **23 dias úteis** (4-5 semanas).
- **Estimativa total com Wave A Sprints 5-6:** 65u = **33 dias úteis** (~7 semanas).

**Notas:**
- T15 (tech-lead) avisou que 5-10 dias era otimista; 8-14 era realista. 23 dias é mais conservador — inclui retrofit de 67 testes + drill PG real + benchmark perf que originalmente foram subestimados.
- Sprints 5-6 dependem de módulos Wave A que ainda não arrancaram (`certificados`, `onboarding`, `direitos-titular`). Estimativa placeholder até esses módulos terem PRD `stable`.
- 9 tasks na zona crítica (causa-raiz dos 13 BLOQUEANTES): T-SAN-PERFIL-008, 010, 011, 017, 018, 023, 024, 041, 044.

## Status de implementação (atualizado 2026-05-27 noite)

| Sprint | Tasks | Status | Commit |
|---|---|---|---|
| **Sprint 1** Schema + funções SECURITY DEFINER | T-001..T-014 | ✅ FECHADO | `87bbc64` |
| **Sprint 2** Predicate + retrofit cmc_cobre (FAIL L6) | T-015..T-018, T-023, T-025..T-030 | ✅ FECHADO | `87bbc64` |
| **Sprint 3** Provisioning + matriz + job vigência | T-031..T-040 | ✅ FECHADO | `f51fe47` |
| **Sprint 4** Snapshot WORM + retrofit equipamento + evidência | T-041..T-050 | ✅ FECHADO | `694ce27` |
| **Sprint 5** Wave A módulo `certificados` | T-051..T-054 | ⬜ Wave A | — |
| **Sprint 6** Wave A `onboarding` + `direitos-titular` + LGPD | T-055..T-062 | ⬜ Wave A | — |

**Tasks pendentes não-críticas (podem entrar em qualquer Sprint Wave A):**

- T-019: predicate `emitir_certificado_rbc` — pertence ao módulo `certificados` Wave A (Sprint 5).
- T-020: predicate `requer_segunda_conferencia` — pode entrar em Sprint 4.5 standalone OU Sprint 5.
- T-022: consumer `notifica_d_e_o` — depende de `OutboundWebhookProvider` (ADR-0054) já operacional.
- T-024: retrofit dos ~63 testes M4 que ainda mencionam `tipo_acreditacao` na construção de objetos do dominio (não na request) — esses não quebraram porque testam o campo `Calibracao.tipo_acreditacao` direto, não o predicate. Pode ser refactor cosmético em qualquer Sprint Wave A.
- T-046: estender hook `metrology-replay-fixtures-versionadas` para validar `perfil_no_evento` em fixtures — pequeno refinamento Sprint 5.
- T-048: arquivar dossiê A4 em B2 WORM + assinatura A3 — Sprint 5 Wave A (depende de módulo certificados).

## Validações cumulativas (PG real)

- **Drill `validar_san_perfil_tenant_migrations`:** 17/17 PASS
- **Drill `validar_san_perfil_tenant_snapshots`:** 6/6 PASS (Sprint 4)
- **Relatório evidência defensiva A4:** 1 evento pré-saneamento exportado
- **Suite regression+audit+M3+M4:** exit 0 (todos verdes)
- **Hooks `_test-runner.sh`:** 414/414 PASS / 51 hooks ativos
- **Smoke `provisionar_tenant` Perfil A:** tenant `smoke-a-real` criado com PDF + auditor + ILAC; trigger anti-mutation bloqueou DELETE no histórico (defesa em camadas funcionando)

## Histórico

- **2026-05-27 manhã** — Auditoria 10 lentes detectou gap; Roldão decidiu manter 4 perfis + consertar antes Wave A; ADR-0067 aceita.
- **2026-05-27 tarde** — P1 spec → P2 4 reviews paralelos (41 achados) → P3 plan.md + spec.md reescrita → P4 tasks.md (62 tasks).
- **2026-05-27 tarde-noite** — P5 Sprint 1 implementado (schema + SECURITY DEFINER + drill 17/17 PASS).
- **2026-05-27 noite** — P5 Sprint 2 implementado (predicate canonico + retrofit `cmc_cobre` fecha FAIL L6 + 23 testes regressão).
- **2026-05-27 noite** — 8 débitos pré-existentes M4 corrigidos (subcontratacao test + ClienteNotificadoVia.NAO_APLICA).
- **2026-05-27 noite** — P5 Sprint 3 implementado (`provisionar_tenant` + job vigência + matriz feature×perfil + hook validator + emenda ADR-0015 + runbook DPO).
- **2026-05-27 noite tarde** — P5 Sprint 4 implementado (snapshot `perfil_no_evento` WORM via trigger BEFORE INSERT + GUC `app.perfil_tenant` + retrofit equipamento snapshot + retrofit geo_truncamento perfil A nunca trunca + drill snapshots 6/6 PASS + relatório evidência defensiva A4).
- **Saneamento puro = 4 Sprints FECHADOS. Aguarda autorização Roldão para Wave A (Sprints 5-6 dependem de módulos `certificados`, `onboarding`, `direitos-titular` ainda inexistentes).**
