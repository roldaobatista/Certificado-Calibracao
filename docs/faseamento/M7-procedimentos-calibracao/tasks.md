---
owner: roldao
revisado-em: 2026-05-30
status: ready-for-implement
fase: M7-procedimentos-calibracao
dominio: metrologia
modulo: procedimentos-calibracao
ritual: tasks
versao: 1
depende-de:
  - docs/faseamento/M7-procedimentos-calibracao/plan.md (ready-for-tasks)
  - docs/faseamento/M7-procedimentos-calibracao/reviews-consolidado.md
---

# Tasks — M7 `metrologia/procedimentos-calibracao` (3º módulo Wave A)

> Deriva do plan v1. IDs `T-PROC-NNN`. Path aninhado ADR-0072. Reuso explícito
> M6. `/implement` segue esta ordem, fatia por fatia, cada fatia com seu ciclo de
> auditores (INV-RITUAL-002 + INV-RITUAL-003). Porta = funções de módulo em
> `query_service.py` (NÃO singleton — C-3). Verificar (`--no-cov --reuse-db`)
> antes de afirmar.

## Fatia 0 — Peça compartilhada `faixa_cobertura` (D-PROC-6, ALTO)

| ID | Tarefa | Saída |
|----|--------|-------|
| T-PROC-000 | Extrair `faixa_contida` + `avaliar_contencao` de `domain/metrologia/escopos_cmc/cobertura.py:32-54` → novo `domain/metrologia/faixa_cobertura.py` (puro Decimal; reasons `REASON_OK`/`REASON_FORA_DO_ESCOPO`/`REASON_UNIDADE_INCOMPATIVEL` ficam no compartilhado) | módulo novo + testes puros migrados |
| T-PROC-001 | `escopos_cmc/cobertura.py` re-exporta (`from ...faixa_cobertura import ...`) — zero mudança de assinatura; `query_service.py` M6 intocado | re-export |
| T-PROC-002 | **Reverde M6 idêntico:** `validar_escopos_cmc` 17/17 + testes domínio cobertura + `test_inv_ecmc_*` 34/34 sem alteração | gate anti-regressão (commit isolado) |

## Fatia 1a — Domínio puro (P1, sem Django)

| ID | Tarefa | Saída/teste |
|----|--------|-------------|
| T-PROC-010 | `enums.py`: `EstadoProcedimento` (RASCUNHO/PUBLICADO/REVOGADO) + `TipoMetodo` (NORMALIZADO/NAO_NORMALIZADO/MODIFICADO) — propriedades terminal/vigente/publicavel | testes enum |
| T-PROC-011 | `entities.py`: `ProcedimentoSnapshot` (frozen, todos os campos §2 plan) + `ProcedimentoUsado` (VO probatório: codigo+versao+numero_revisao+sha256+tipo_metodo+aprovado_por+vigência) | frozen dataclasses + testes |
| T-PROC-012 | reuso VOs `value_objects.py` (Grandeza/FaixaMedicao) + `faixa_cobertura` (T-PROC-000) — NÃO recriar | teste import |
| T-PROC-013 | `repository.py` Protocols (`ProcedimentoRepository`: vigente_em/obter_por_id/existe_chave/proxima_versao/salvar_novo/publicar/encerrar_vigencia/revogar) | runtime_checkable + Fake |
| T-PROC-014 | `transicoes.py`: máquina de estados + `validar_motivo_revogacao` + invariantes puras INV-PROC-001/006/009/010 (puro) | testes transição+bloqueios |

## Fatia 1b — Schema + persistência (P2, migrations/)

| ID | Tarefa | Nota |
|----|--------|------|
| T-PROC-020 | `models.py` `ProcedimentoCalibracao` colunas TIPADAS (§2 plan) + `apps.py` `label="procedimentos_calibracao"` | |
| T-PROC-021 | `0001_initial`: tabela + UNIQUE `(tenant,codigo,versao)` (INV-PROC-002) + **UNIQUE parcial não-overlap** `(tenant,codigo,grandeza,faixa_min,faixa_max) WHERE PUBLICADO AND vigencia_fim NULL AND revogado_em NULL` (INV-PROC-008) + índice parcial resolução + vigência ADR-0030 + soft-delete B + `# rls-policy: external 0002` + `metrology-affecting:` (toca metodo/faixa) | INV-PROC-002/008 |
| T-PROC-022 | `0002_rls_policies`: RLS v2 (ENABLE+FORCE + 4 policies) | INV-TENANT-001..004 |
| T-PROC-023 | `0003_triggers_worm`: Padrão B — BEFORE DELETE RAISE + BEFORE UPDATE bloqueia campos técnicos (metodo_norma/faixa/anexo_sha256/tipo_metodo) de PUBLICADO exceto one-shot `revogado_em`/`vigencia_fim` + bump CAS | INV-PROC-003/007/SOFT-002 |
| T-PROC-024 | `0004_grants_app_user` | |
| T-PROC-025 | `0005_seed_authz`: ações `procedimentos_calibracao.{cadastrar,publicar,revisar,revogar,ver}` × matriz perfil idempotente (publicar = RT/gestor) | |
| T-PROC-026 | `repositories.py` + `query_service.py` `vigente_em(...)` (função de módulo, fail-CLOSED, tenant_id explícito, PUBLICADO+vigente+contenção via `faixa_cobertura`) + `publicar` com `pg_advisory_xact_lock` + CAS | C-3 / D-PROC-3 |
| T-PROC-027 | drill `validar_procedimentos_calibracao` (estrutural) | GATE-PROC-DRILL-LOCAL |

## Fatia 2 — Use cases + REST + versionamento (P3+P4)

| ID | Tarefa |
|----|--------|
| T-PROC-030 | `cadastrar_procedimento` (RASCUNHO; valida tipo_metodo INV-PROC-010 fail-open lazy) |
| T-PROC-031 | `publicar_procedimento` (RASCUNHO→PUBLICADO; superseção automática D-PROC-3 advisory lock + encerra anterior; exige numero_revisao+aprovado_em+aprovado_por INV-PROC-009) + evento `procedimentos_calibracao.publicado` |
| T-PROC-032 | `revisar_procedimento` = INSERT nova `versao` preservando anterior + evento `revisado` |
| T-PROC-033 | `revogar_procedimento` (one-shot `revogado_em`+motivo ≥10 ADR-0029) + evento `revogado` |
| T-PROC-034 | `AnexoStoragePort` Protocol + adapter (B2/filesystem) + upload sha256 SERVER-SIDE (C-4; ignora hash do cliente) |
| T-PROC-035 | serializers DRF (rótulos "Procedimento técnico"/"Código"/"Norma de referência") |
| T-PROC-036 | `ProcedimentoCalibracaoViewSet` + ACTION_MAP authz + idempotência (IDEMP-001) + tenant de `active_tenant_context` (nunca body) |
| T-PROC-037 | `urls.py` + plug em `config/urls.py` raiz (lição T-CAL-124) |

## Fatia 3 — Wire-in + GATE-CAL-PROC-VIGENTE-PREDICATE (P5)

| ID | Tarefa |
|----|--------|
| T-PROC-040 | 2ª porta `CoberturaProcedimentoPort` injetada em `configurar_calibracao` (3º param, default fail-open lazy); roda DEPOIS do escopo, só RBC, 1ª falha interrompe; None→412 `ProcedimentoVigenteAusente` |
| T-PROC-041 | injeção server-side grandeza+faixa (reusa `grandeza_decl`/`faixa_decl` da peça #1 — SEG-CAL-10); NÃO-RBC = aviso degradante (D-PROC-1) |
| T-PROC-042 | preenche `procedimento_versao_snapshot` real (código+versão+numero_revisao+sha256) — campo JÁ existe M4 (C-1), não cria coluna |
| T-PROC-043 | deprecar predicate STUB `procedimento_vigente_para` (no-op) |
| T-PROC-044 | testes transição fail-open→fail-closed (TST-005): A sem proc→412; A com proc vigente→200; NÃO-RBC nunca 412; ordem escopo→procedimento (escopo falho para antes) — **nunca relaxar assert M4** |
| T-PROC-045 | **suíte M4 chave reverde** (629) |
| T-PROC-046 | INV-PROC-001..010 em REGRAS-INEGOCIAVEIS + classes `TestINV_PROC_001..010` (TST-004) |
| T-PROC-047 | hooks: `proc-vigente-fail-closed-check` (molde escopo-cobre) + `proc-controle-documental-check` (INV-PROC-009) + `proc-metodo-validado-check` (INV-PROC-010 fail-open lazy) + casos `_test-runner` |
| T-PROC-048 | drill PG real GATE-PROC-DRILL-LOCAL (UNIQUE + RLS cross-tenant + WORM + **concorrência superseção cronometrada** + vigente_em bloqueia só RBC) |
| T-PROC-049 | validação cl. 7.11 do gate (ADR-0025; metrology-affecting) + replay fixture |

## P8/P9 (fechamento — após Fatia 3)

| ID | Tarefa |
|----|--------|
| T-PROC-070 | emendar PRD US-CAL-016 (AC-016-1/2 saem do fail-open ADR-0066→real; nota tipo_metodo/cl.7.2.2) + matriz-feature-perfil (procedimento documentado A obrig / B-C-D recomendado) |
| T-PROC-071 | reconciliação `matriz-reconciliacao.md` (US↔AC↔INV↔ADR↔hook↔código + INV↔teste + GATEs + pendências) |
| T-PROC-080 | ritual auditores roteados (INV-RITUAL-003): seguranca (porta fail-closed+RLS+concorrência) · llm-correctness · produto (AC+terminologia) · qualidade (INV testados) · observabilidade (eventos) · idempotência. MÉDIO+ bloqueia. |

## GATEs

GATE-CAL-PROC-VIGENTE-PREDICATE (T-PROC-040/045) · GATE-PROC-DRILL-LOCAL
(T-PROC-048) · GATE-PROC-ANEXO-HASH (T-PROC-034) · GATE-PROC-METODO-VALIDADO
(T-PROC-030 fail-open lazy → licencas-acreditacoes) · GATE-PROC-VALIDACAO-7.11
(T-PROC-049; parecer RBC credenciado pré-produção).

## Pendências externas (diferidas — `project_sem_contratacoes_externas_ate_producao`)

Parecer RBC credenciado da validação de método cl. 7.2.2 + validação cl. 7.11 do
gate de resolução — pré-produção, NÃO agora.

## Próximo passo

`/implement` começando por **Fatia 0** (peça compartilhada `faixa_cobertura` +
reverde M6) → Fatia 1a (domínio puro, sem Docker/PG). Commits atômicos por
task/grupo.
