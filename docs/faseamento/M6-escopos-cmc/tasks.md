---
owner: roldao
revisado-em: 2026-05-29
status: draft
fase: M6-escopos-cmc
dominio: metrologia
modulo: escopos-cmc
ritual: tasks
versao: 1
depende-de:
  - docs/faseamento/M6-escopos-cmc/plan.md (v2 ready-for-tasks)
  - docs/faseamento/M6-escopos-cmc/reviews-consolidado.md
  - docs/adr/0073-validacao-cobertura-metrologica-no-use-case.md
  - docs/adr/0074-cobertura-rbc-tridimensional-faixa-u-maior-cmc.md
  - docs/adr/0075-capacidade-interna-nao-acreditada-distinta-cmc.md
  - docs/adr/0066-predicates-cmc-procedimento-fail-open-lazy-wave-a.md (emenda 2026-05-29)
---

# Tasks — M6 `metrologia/escopos-cmc` (2º módulo Wave A)

> Deriva do plan v2 (§15 deltas). IDs `T-ECMC-NNN`. Path
> `src/infrastructure/metrologia/escopos_cmc/` (ADR-0072, `label="escopos_cmc"`).
> Reuso explícito M4/M5 (plan §6). **`/implement` segue esta ordem, fatia por fatia,
> cada fatia com seu ciclo de auditores (INV-RITUAL-002 + INV-RITUAL-003).**
> Porta = funções de módulo em `query_service.py` (NÃO singleton — TL-C-04).

## ⚠️ Pré-condição da Fatia 3 (investigação regra #0 — TL-C-03)

| ID | Tarefa | Saída |
|----|--------|-------|
| T-ECMC-000 | ANTES do wire-in: investigar estado real da suíte M4 sob perfil A no `configurar` — a view passa grandeza/faixa no resource hoje? Algum teste M4 de `configurar` perfil A passa, e por quê? Rodar `pytest` M4 chave (`--no-cov --reuse-db`) + ler `calibracao/views.py` `configurar`. | Relatório curto do tamanho real do wire-in; decide 2 etapas da Fatia 3. **Exige Docker/PG real.** |

---

## Fatia 1a — Domínio puro (P1, sem Django)

| ID | Tarefa | Saída/teste |
|----|--------|-------------|
| T-ECMC-001 | `enums.py`: `EstadoEscopo` (RASCUNHO_EXTRAIDO/CONFIRMADO/REVOGADO), `OrigemEscopo` (MANUAL/EXTRACAO_PDF), `FormaCMC` (ABSOLUTA / `a+b·X` relativa) | testes enum + propriedades terminal/vigente |
| T-ECMC-002 | `entities.py`: migrar `EscopoCMCSnapshot` (de calibracao/queries/escopo.py) + `EscopoUsado` (VO WORM probatório — versao/CMC-época/forma/U×CMC/RT-época/perfil — RBC-NC-06) + `EscopoExtraido` (staging) | frozen dataclasses + testes |
| T-ECMC-003 | reuso VOs `src/domain/metrologia/value_objects.py` (Grandeza/FaixaMedicao/IncertezaExpandida) — NÃO recriar | teste import |
| T-ECMC-004 | `cobertura.py` puro Decimal: `faixa_contida` (contenção total — TL-C-08, NÃO interseção) + `u_atende_cmc` (U≥CMC normalizando unidade/forma abs vs `a+b·X` — ADR-0074/INV-ECMC-009) + `menor_cmc_por_faixa` (RBC-NC-03) | testes: contenção (dentro/borda/fora), U<CMC bloqueia, U=CMC cego rejeita (RBC-NC-07), menor CMC entre métodos |
| T-ECMC-005 | `repository.py` Protocols (`EscopoRepository`: cobre/cmc_para/listar/por_versao) | runtime_checkable + Fake no teste |
| T-ECMC-006 | máquina de estados (RASCUNHO_EXTRAIDO→CONFIRMADO→REVOGADO; revisão=nova versão) + invariantes puras INV-ECMC-001..009 | testes de transição + bloqueios |

## Fatia 1b — Schema + persistência (P2, `migrations/`)

| ID | Tarefa | Nota |
|----|--------|------|
| T-ECMC-010 | `models.py` `EscopoCMC` colunas TIPADAS (TL-C-02: não JSONField) + `apps.py` `label="escopos_cmc"` (TL-C-10) | D-ECMC-2 |
| T-ECMC-011 | `0001_initial`: `escopo_cmc` + UNIQUE `(tenant_id, grandeza, faixa_min, faixa_max, procedimento_id, versao)` + índice parcial `WHERE estado='CONFIRMADO' AND revogado_em IS NULL` (TL-C-11) + `revision` + vigência ADR-0030 + soft-delete B + `rbc_acreditado` + `numero_escopo_cgcre` + `documento_regulatorio_id` (FK NULLABLE→Licenças) + `escopo_extraido` (staging) | INV-ECMC-001/006; `# rls-policy: external 0002` |
| T-ECMC-012 | `0002_rls_policies`: RLS pattern v2 (ENABLE+FORCE + 4 policies) nas 2 tabelas | INV-TENANT-001..004 |
| T-ECMC-013 | `0003_triggers_worm`: Padrão B — BEFORE DELETE RAISE + BEFORE UPDATE bloqueia campos metrológicos de CONFIRMADO exceto one-shot `revogado_em` (TL-C-07, molde `recal_externo_padrao_worm_check`); `escopo_extraido` mutável (sem WORM) | INV-ECMC-003/SOFT-002 |
| T-ECMC-014 | `0004_grants_app_user` + `metrology-affecting:` nas migrations que tocam cmc_valor/faixa (INV-CAL-VAL-002 / hook migration-metrology-classifier) | |
| T-ECMC-015 | `0005_seed_authz`: ações `escopos_cmc.{cadastrar,revisar,revogar,declarar_capacidade,confirmar_extraido,ver}` × matriz perfil (A=RBC; B/C/D=capacidade interna) idempotente | ADR-0075 |
| T-ECMC-016 | `repositories.py` + `query_service.py` funções de módulo `cobre(...)`/`cmc_para(...)` (fail-CLOSED, filtro tenant_id explícito, só CONFIRMADO vigente em `data`, contenção total, menor CMC) + CAS `atualizar_com_lock` | TL-C-04; reuso M4 |
| T-ECMC-017 | drill `validar_escopos_cmc` (estrutural) | GATE-ECMC-DRILL-LOCAL |

## Fatia 2 — Use cases + REST + versionamento (P3+P4)

| ID | Tarefa |
|----|--------|
| T-ECMC-020 | `cadastrar_escopo` (perfil A: rbc_acreditado=true via `tenant_perfil_e(['A'])`; INV-ECMC-002) |
| T-ECMC-021 | `declarar_capacidade_interna` (B/C/D: rbc_acreditado **forçado false** — anti-fraude INV-ECMC-002/INV-015; ADR-0075) |
| T-ECMC-022 | `revisar_escopo` = INSERT nova `versao` preservando anterior (AC-CAL-015-2; TL-C-07) + evento `escopos_cmc.revisado` na cadeia hash (TL-C-06) |
| T-ECMC-023 | `revogar_escopo` (one-shot `revogado_em`+motivo canon ADR-0029; redução prospectiva RBC-NC-05) + evento `escopos_cmc.revogado` |
| T-ECMC-030 | serializers DRF (validação payload; rótulo perfil-aware ADR-0075) |
| T-ECMC-031 | `EscopoCMCViewSet` + ACTION_MAP authz + idempotência (IDEMP-001) + paginação F-C3 herdada + tenant de `active_tenant_context` (nunca body) |
| T-ECMC-032 | `urls.py` + plug em `config/urls.py` raiz (evitar órfã — lição T-CAL-124) |
| T-ECMC-033 | vínculo `documento_regulatorio_id` (Licenças NULLABLE até módulo existir — não bloqueia) |

## Fatia 3 — Wire-in cobertura + GATE-CAL-CMC-PREDICATE (P5 — após T-ECMC-000)

| ID | Tarefa |
|----|--------|
| T-ECMC-040 | **ADR-0073:** mover validação para DENTRO do use case `configurar_calibracao` (M4) — chamada `escopos_cmc.query_service.cobre(...)` → 412 `EscopoNaoCobreFaixa`; recepção = aviso degradante NÃO-RBC (AC-CAL-001-2); deprecar predicate STUB `cmc_cobre` (no-op) |
| T-ECMC-041 | injeção server-side de grandeza+faixa+data (não payload — SEG-CAL-10); investigar fonte (campo 1ª classe na Calibracao vs snapshot recepção — definido por T-ECMC-000) |
| T-ECMC-042 | **2ª porta `cmc_para()` (ADR-0074/INV-ECMC-009):** consumo no ponto de emissão onde U é final (M4 `aprovar_2a_conferencia` OU diferir a `certificados` Wave A com **GATE-ECMC-U-MAIOR-CMC**) → 412 `IncertezaAbaixoDoCMC` |
| T-ECMC-043 | snapshot `EscopoUsado` congelado na configuração (VO WORM canon ADR-0029) alimenta `escopos_acreditados_vigentes_no_momento` JSONB (ADR-0014; INV-ECMC-008) |
| T-ECMC-044 | vínculo RT↔escopo **fail-open lazy** documentado (paralelo ADR-0063) + **GATE-ECMC-RT-VINCULO** + teste nomeado do fail-open (TL-C-05/RBC-NC-04) |
| T-ECMC-045 | testes transição fail-open→fail-closed (TST-005): A sem escopo→412; A com escopo→200; B/C/D nunca 412 por CMC; anti-fraude rbc forçado false (TestINV_ECMC_002) — **nunca relaxar assert M4** |
| T-ECMC-046 | **suíte M4 chave reverde** (transição 2 etapas T-ECMC-000: canal de dados com STUB True → troca real) |

## Fatia 4 — Extração PDF + conferência humana (P6)

| ID | Tarefa |
|----|--------|
| T-ECMC-050 | `extracao/parse_pdf_cgcre.py` motor DETERMINÍSTICO (leitor de tabela; porta isolada/trocável) — GATE-ECMC-EXTRACT-ENGINE; NÃO IA (não ativa ADR-0059) |
| T-ECMC-051 | use case `importar_escopo_pdf` → cria `EscopoExtraido` (RASCUNHO_EXTRAIDO, editável) — nunca persiste vigente (INV-ECMC-007) |
| T-ECMC-052 | use case `confirmar_escopo_extraido` (ação `escopos_cmc.confirmar_extraido`) → cria linha CONFIRMADA em `escopo_cmc` (WORM) + audit (quem/quando) |
| T-ECMC-053 | REST upload + tela de conferência (serializers + view); replay fixture versionado do parser (cl. 7.11 — molde metrology-replay-fixtures-versionadas) |
| T-ECMC-054 | validação cl. 7.11 do motor (ADR-0025; dado extraído que toca cmc_valor/faixa é metrology-affecting) |

## P7 — INVs em REGRAS + hooks

| ID | Tarefa |
|----|--------|
| T-ECMC-060 | cravar INV-ECMC-001..009 em REGRAS-INEGOCIAVEIS.md + classes `TestINV_ECMC_001..009` (TST-004) em `tests/regressao/` |
| T-ECMC-061 | hooks novos: vínculo escopo↔RBC (rbc só perfil A) + transição fail-open→fail-closed + terminologia A vs B/C/D (ADR-0075) — avaliar reuso `cmc-binding-check.sh` existente; casos no `_test-runner` |
| T-ECMC-062 | hook/validação: extração nunca auto-persiste (INV-ECMC-007) |

## P8 — Emendas docs + reconciliação + drill PG real

| ID | Tarefa |
|----|--------|
| T-ECMC-070 | emendar PRD calibração: AC-CAL-001-2/002-2/015-1/2 (sair do fail-open ADR-0066→0073/0074) + nota terminologia ADR-0075 |
| T-ECMC-071 | matriz `matriz-feature-perfil.md`: escopo RBC (A) vs capacidade interna (B/C/D) + matriz retenção (escopo sustenta cert 25a) |
| T-ECMC-072 | drill `validar_escopos_cmc` PG real (GATE-ECMC-DRILL-LOCAL): UNIQUE + RLS cross-tenant + triggers WORM + perfil A declara RBC / B-C-D forçado false + cobre() bloqueia fora-de-escopo só RBC + extração não persiste sem confirmação |
| T-ECMC-073 | reconciliação spec↔código `matriz-reconciliacao.md` (US↔AC↔INV↔ADR↔hook↔código + INV↔teste + GATEs + pendências) |

## P9 — Ritual auditores (roteados — INV-RITUAL-003)

| ID | Tarefa |
|----|--------|
| T-ECMC-080 | auditores essenciais (6) + roteados por área: seguranca (porta fail-closed + RLS + anti-fraude rbc) · llm-correctness (cobertura bate docstring) · produto (AC binários + terminologia ADR-0075) · qualidade (INV-ECMC testados) · observabilidade (eventos hash-chain) · idempotência. INV-RITUAL-001: MÉDIO+ bloqueia. |

## GATEs do módulo

GATE-CAL-CMC-PREDICATE (T-ECMC-040/046) · GATE-ECMC-U-MAIOR-CMC (T-ECMC-042 — pode
diferir a `certificados`) · GATE-ECMC-RT-VINCULO (T-ECMC-044 — pré-1º tenant externo) ·
GATE-ECMC-DRILL-LOCAL (T-ECMC-072) · GATE-ECMC-EXTRACT-ENGINE (T-ECMC-050) ·
GATE-ECMC-COBERTURA-RBC (revisão humana credenciada pré-tenant-A — diferido).

## Pendências externas (diferidas — `project_sem_contratacoes_externas_ate_producao`)

Parecer RBC credenciado da cobertura U≥CMC + validação cl. 7.11 do parser (RBC-NC-08
verificar nº NIT) · dossiê CGCRE assinado · todas pré-produção, NÃO agora.

## Próximo passo

`/implement` começando por **Fatia 1a (domínio puro)** — não depende de Docker/PG nem
do M4. **Fatia 3 exige T-ECMC-000 (investigação) com ambiente real ANTES.** Commits
atômicos por task/grupo. Verificar (`--no-cov --reuse-db`) antes de afirmar
(memória `feedback_test_db_nao_dropar_create_db`).
