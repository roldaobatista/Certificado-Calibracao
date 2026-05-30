---
owner: agente-ia
revisado-em: 2026-05-29
proximo-review: pre-fechamento-M5
status: draft
diataxis: reference
audiencia: [agente, auditor]
marco: M5-padroes
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/M5-padroes/spec.md
  - docs/faseamento/M5-padroes/plan.md
  - docs/faseamento/M5-padroes/tasks.md
  - docs/dominios/metrologia/modulos/padroes/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — M5 `metrologia/padroes`

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec virou código real
> + teste + hook, e apontar o arquivo. Pré-requisito do ritual P8/P9 (reconciliação
> antes dos 10 auditores). Estado: **P1-P8 entregues**; PG-real consolidado em
> `GATE-PAD-DRILL-LOCAL`.

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-PAD-001 Cadastrar padrão | 001-1..5 | INV-PAD-001/002/005 | 0040/0067 | migration-rls-check, payload-tipo-acreditacao-obsoleto | `application/.../cadastrar_padrao.py` + `domain/.../entities.py` + migrations 0001/0006 | ✅ |
| US-PAD-002 Recal externo (envio+retorno+aprovação RT) | 002-1..4 | INV-PAD-006 (C-4) | 0040/0064 | **padrao-incertezas-so-via-recal** | `application/.../registrar_recal_envio.py` + `registrar_recal_retorno.py` + `aprovar_recal_rt.py` + migration 0003 (trigger GUC) | ✅ |
| US-PAD-003 Verificação intermediária | 003-x | INV-PAD-003 (VI REPROVADA) | 0040 | — (trigger WORM) | `application/.../registrar_verificacao_intermediaria.py` + migration 0003 | ✅ |
| US-PAD-004 Baixar/sucatar | 004-x | INV-PAD-003 / INV-SOFT-002 | 0031 | soft-delete-padrao-check | `application/.../baixar_padrao.py` + `domain/.../transicoes.py` + migration 0003 (block_delete) | ✅ |
| US-PAD-005 Intercomparação PT (perfil A) | 005-x | INV-023 | 0067 | — (gate perfil A) | `application/.../registrar_intercomparacao.py` | ✅ |
| US-PAD-006 Dossiê CGCRE (JSON, perfil A) | 006-x | supervisão | 0067 | — | `query_service.montar_dossie_cgcre` + `views.py` (GET `dossie-cgcre`, gate perfil A) | ✅ JSON via REST (P10); PDF/A Wave B |
| US-PAD-007 Equipamentos auxiliares cl. 6.4.5 | 007-1..5 | **INV-PAD-007** | 0040/0030 | **padrao-auxiliar-em-controle** | `domain/.../entities.py` (VinculoAuxiliar) + `query_service.py` (`_bloqueado_por_auxiliar`) + `application/.../gerir_vinculo_auxiliar.py` + `views.py` (REST CRUD `vinculos-auxiliares`) | ✅ runtime (P7) + REST CRUD (P10) |
| US-PAD-008 Cartas Shewhart (perfil A) | 008-1/2/2b/3/4 | **INV-PAD-008/010** | 0070/0067 | **shewhart-perfil-A** + **analise-carta-worm** | `domain/.../shewhart.py` + `application/.../registrar_analise_carta_controle.py` + migration 0003 (WORM) + `query_service.carta_controle_readmodel` + `views.py` (GET `carta-controle`, gate perfil A) | ✅ + read-model REST (P10) |
| US-PAD-009 2 implementações mesmo mensurando (cl. 7.11) | 009-1..4 | **INV-PAD-009** | 0071 | incerteza-versao-motor-check (reuso M4) | `domain/.../valor_convencional.py` + `application/.../calcular_valor_convencional.py` | ✅ |

## 2. INV-PAD-001..010 ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-PAD-001 | `UNIQUE (tenant, numero_serie)` migration 0001 | `TestINV_PAD_001` | migration-rls-check |
| INV-PAD-002 | `__post_init__` + CHECK jsonb 0006 | `TestINV_PAD_002` (app + DB) | — |
| INV-PAD-003 | porta `padrao_bloqueado_para_uso` (estado) | `TestINV_PAD_003` | — |
| INV-PAD-004 | porta (proximo_recal/validade < hoje) | `TestINV_PAD_004` | — |
| INV-PAD-005 | use case `cadastrar_padrao` + `tenant_perfil_e(['A'])` | `TestINV_PAD_005` | payload-tipo-acreditacao-obsoleto |
| INV-PAD-006 | trigger PG `padrao_incertezas_so_via_recal_trg` (GUC C-10) | `TestINV_PAD_006` + `test_inv_pad_p2_schema_triggers` | **padrao-incertezas-so-via-recal** |
| INV-PAD-007 | porta `_bloqueado_por_auxiliar` (recursivo fail-CLOSED) | `TestINV_PAD_007` (3 casos PG-real) | **padrao-auxiliar-em-controle** |
| INV-PAD-008 | gate perfil A em 3 pontos | `TestINV_PAD_008` | **shewhart-perfil-A** |
| INV-PAD-009 | `valor_convencional.calcular` + `DivergenciaImplementacoesError` | `TestINV_PAD_009` (convergente+divergente) | incerteza-versao-motor |
| INV-PAD-010 | trigger PG `analise_carta_controle_append_only_trg` | `TestINV_PAD_010` (UPDATE/DELETE) + `test_inv_pad_p2_schema_triggers` | **analise-carta-worm** + audit-immutability |

## 3. Hooks novos M5 P7 (camada A pré-commit)

| Hook | INV | Criado | Casos `_test-runner` | Status |
|------|-----|--------|----------------------|--------|
| padrao-incertezas-so-via-recal.sh | INV-PAD-006 | P7 | 10 (PD6-1..10) | ✅ |
| padrao-auxiliar-em-controle.sh | INV-PAD-007 | P7 | 6 (PA1..6) | ✅ |
| shewhart-perfil-A.sh | INV-PAD-008 | P7 | 8 (SH1..8) | ✅ |
| analise-carta-worm.sh | INV-PAD-010 | P7 | 13 (ACW1..d) | ✅ |

Total `_test-runner`: **450/450 verdes / 55 hooks ativos**.

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| P1 | domínio puro (enums + shewhart + valor_convencional + 7 snapshots + 6 Protocols + transições) | 44 testes puros |
| P2 | schema infra (path aninhado ADR-0072) — 6 models + 4 migrations + triggers WORM | 11 testes PG-real |
| P3 | 10 use cases puros (CAS real) | 28 testes Fake repos |
| P4 | porta fail-CLOSED `padrao_bloqueado_para_uso` + GATE-PAD-PORTA-M4 | 15 PG-real + 5 Fakes |
| P5 | adapters Django + REST (PadraoViewSet) + seed authz (migration 0005) | 6 round-trip + 6 E2E |
| P6 | job `alertar_padroes_pendencias` (4 pendências) | 20 puros + 3 PG-real |
| P7 | INV-PAD-001..010 em REGRAS + 4 hooks + INV-PAD-007 runtime + CHECK 0006 | 19 `TestINV_PAD_*` + 37 casos hook |
| P8 | emenda PRD + matriz retenção + drill `validar_m5_padroes` + esta matriz | drill 43/43 PASS |
| P10 | REST vínculo auxiliar (CRUD) + dossiê CGCRE (uso em calibrações M4 + âncora hash-chain ADR-0064) + carta-controle (gate ≥10 pontos/24m AC-PAD-008-1) + migration 0007 seed authz + PERF-001 baseline | 13 E2E (p10, inclui cross-tenant dossiê/carta) + 22/22 (p5+p10) |

## 5. GATEs do módulo

| GATE | Conteúdo | Status |
|------|----------|--------|
| GATE-PAD-PORTA-M4 | porta consumida pelo M4 antes de gravar `PadraoUsado` | ✅ entregue (P4) |
| GATE-PAD-PERF-DISPONIVEIS | N+1 bounded por `limite=200` em GET `/disponiveis/`; baseline congelado por `assertNumQueries`; otimização batch rastreada | 🟡 baseline (P10) — otimização batch diferida |
| GATE-PAD-DRILL-LOCAL | PG-real: cross-tenant, triggers WORM/incertezas, perfil A bloqueia RBC, INV-PAD-007 auxiliar, concorrência GUC/pool | 🟡 parcial — coberto por `test_inv_pad_p2_schema_triggers` + `test_inv_pad_classes_nomeadas`; teste de concorrência de pool dedicado + revisão pré-1º-tenant pendentes |
| GATE-PAD-SHEWHART-RBC | revisão humana credenciada do motor incerteza+Shewhart | ⛔ diferido pré-tenant-A (memória `project_sem_contratacoes_externas_ate_producao`) |
| GATE-CAL-CMC/PROC-PREDICATE | destravam com módulos `escopos-cmc` + `procedimentos` (próximos) | ⛔ Wave A |

## 6. Pendências para fechar M5

- **P10 1ª leva (2026-05-29):** PROD-PAD-01/02/03 (dossiê+carta+vínculo via REST) + PERF-001 baseline.
- **Re-passada P9 rodada (2026-05-29, INV-RITUAL-003 — 9 auditores):** 7 PASS + 2 CONCERNS; 3 MÉDIO bloqueantes detectados e **resolvidos na causa-raiz na 2ª leva P10**:
  - AC-PAD-006-1 (dossiê): + `uso_em_calibracoes` (M4 PadraoUsado) + `ancora_integridade` (hash-chain WORM ADR-0064). Resolvido em código.
  - AC-PAD-008-1 (carta): gate de ≥10 pontos de VI em 24 meses antes de plotar limites (`amostra_insuficiente`); separado do limiar ≥2 da porta de bloqueio (fail-safe). Resolvido em código.
  - drift D4 (contagem): matriz corrigida para 12 E2E (p10) + 21/21.
- **GATEs BAIXO rastreados (não bloqueiam — INV-RITUAL-001):** GATE-LGPD-PAD-DOSSIE-1 (anti-PII em lab_externo/lab_organizador/protocolo — razão social PJ, Wave A); GATE-OBS-PAD-CORRELACAO-LOG (correlation_id no log dos 2 eventos de vínculo — resolve com middleware correlation Wave A).
- GATE-PAD-DRILL-LOCAL: teste de concorrência GUC/pool dedicado (C-10) — drill PG-real + pentest pré-1º-tenant.

## 7. Próximo passo

Re-passada de confirmação (produto + drift-docs — os 2 que tinham CONCERNS) → se zero MÉDIO+, fechar M5 e promover frontmatter `draft→stable`.
