---
owner: agente-ia
revisado-em: 2026-05-31
proximo-review: 2026-08-31
status: stable
diataxis: reference
audiencia: [agente, auditor]
marco: M7-procedimentos-calibracao
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/M7-procedimentos-calibracao/spec.md
  - docs/faseamento/M7-procedimentos-calibracao/plan.md
  - docs/faseamento/M7-procedimentos-calibracao/tasks.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — M7 `metrologia/procedimentos-calibracao`

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec virou código real
> + teste + hook, e apontar o arquivo. Pré-requisito do ritual P8/P9 (reconciliação
> antes dos auditores roteados — INV-RITUAL-003). Estado: **Fatias 0/1a/1b/2/3 +
> P8 entregues**; PG-real consolidado em `GATE-PROC-DRILL-LOCAL`.
> Path infra aninhado `src/infrastructure/metrologia/procedimentos_calibracao/` (ADR-0072).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-PROC-001 Cadastrar procedimento (RASCUNHO + anexo PDF) | herda US-CAL-016 | INV-PROC-002/006/007/010 | 0030/0031 | **proc-metodo-validado-check** | `application/.../cadastrar_procedimento.py` + `domain/.../entities.py`/`transicoes.py` + migrations 0001 | ✅ |
| US-PROC-002 Publicar (RASCUNHO→PUBLICADO, supersede vigente) | cl. 7.2.1 | **INV-PROC-003/008/009** | 0065/0031 | **proc-controle-documental-check** | `application/.../publicar_procedimento.py` (advisory lock D-PROC-3) + REST `views.py` + migration UNIQUE parcial (0001) + trigger WORM (0003) | ✅ |
| US-PROC-003 Revisar (nova versão, anterior preservada) | AC-CAL-016-3 | INV-PROC-002/003 | 0030/0031 | — (trigger WORM) | `application/.../revisar_procedimento.py` | ✅ |
| US-PROC-004 Revogar (WORM Padrão B) | AC-PROC-004 | INV-PROC-003/006 | 0029/0031 | — (trigger WORM) | `application/.../revogar_procedimento.py` + `domain/.../transicoes.py` (`validar_motivo_revogacao`) + migration 0003 | ✅ |
| US-PROC-005 Resolver procedimento vigente na configuração (`procedimento_vigente_para` real → 412) | AC-CAL-016-1/2 + GATE-CAL-PROC-VIGENTE-PREDICATE | **INV-PROC-001/004** | 0073/0066→0073 | **proc-vigente-fail-closed-check** | `infrastructure/.../query_service.py` (`vigente_em`/`cobre_procedimento`) + `domain/metrologia/faixa_cobertura.py` (`faixa_contida`) + wire-in `application/.../calibracao/configurar_calibracao.py` (`CoberturaProcedimentoPort`) | ✅ (portão config FECHADO) |
| US-PROC-006 Snapshot `procedimento_versao_snapshot` congelado na calibração | AC-CAL-016-3 / INV-CAL-WORM-001 | **INV-PROC-005** | 0029 | — | `domain/.../entities.py` (VO `ProcedimentoUsado.snapshot_minimo` — 4 chaves c/ `numero_revisao`) + wire-in preenche server-side | ✅ |

## 2. INV-PROC-001..010 ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-PROC-001 | porta `vigente_em` só PUBLICADO vigente que contém a faixa (`faixa_contida`) | `TestINV_PROC_001` + `test_inv_proc_p2_schema_triggers` | **proc-vigente-fail-closed-check** |
| INV-PROC-002 | `UNIQUE (tenant, codigo, versao)` migration 0001 + `existe_chave` | `TestINV_PROC_002` + `test_inv_proc_p2_schema_triggers` | migration-metrology-classifier |
| INV-PROC-003 | trigger PG WORM Padrão B `procedimento_calibracao` (UPDATE técnico/DELETE) | `TestINV_PROC_003` + `test_inv_proc_p2_schema_triggers` | soft-delete-padrao-check |
| INV-PROC-004 | porta `cobre_procedimento` fail-CLOSED no use case `configurar_calibracao` (ADR-0073) → 412 | `TestINV_PROC_004` + `test_m7_wire_in_configurar_p3` | **proc-vigente-fail-closed-check** |
| INV-PROC-005 | `ProcedimentoUsado.snapshot_minimo` 4 chaves + wire-in preenche server-side (não payload) | `TestINV_PROC_005` + `test_m7_wire_in_configurar_p3` | — (puro) |
| INV-PROC-006 | `CadastrarProcedimentoInput.__post_init__` (tz-aware) + `vigente_em`/`revogado_em` | `TestINV_PROC_006` | vigencia-canonica-check |
| INV-PROC-007 | `AnexoStoragePort.sha256_server_side` recalcula no cadastrar/revisar (use case + REST) | `TestINV_PROC_007` | — (puro) |
| INV-PROC-008 | UNIQUE parcial (1 PUBLICADO vigente por chave) + `pg_advisory_xact_lock` no publicar | `TestINV_PROC_008` + `test_inv_proc_p2_schema_triggers` | migration-concorrencia-* (molde) |
| INV-PROC-009 | `validar_controle_documental` na transição publicar (numero_revisao+aprovado_*) | `TestINV_PROC_009` + `test_m7_procedimentos_use_cases_p2` | **proc-controle-documental-check** |
| INV-PROC-010 | `metodo_exige_validacao_pendente` fail-open lazy (aviso, não bloqueia) | `TestINV_PROC_010` + `test_m7_procedimentos_dominio_p1` | **proc-metodo-validado-check** |

## 3. Hooks novos M7 Fatia 3 (camada A pré-commit)

| Hook | INV | Criado | Casos `_test-runner` | Status |
|------|-----|--------|----------------------|--------|
| proc-vigente-fail-closed-check.sh | INV-PROC-004 | Fatia 3 | 6 (PVFC1..6) | ✅ |
| proc-controle-documental-check.sh | INV-PROC-009 | Fatia 3 | 5 (PCD1..5) | ✅ |
| proc-metodo-validado-check.sh | INV-PROC-010 | Fatia 3 | 6 (PMV1..6) | ✅ |

Total `_test-runner`: **491/491 verdes / 61 hooks ativos**.

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| 0 | extrair `faixa_contida`+`avaliar_contencao`→`domain/metrologia/faixa_cobertura.py` (compartilhado escopos+procedimentos) + reverde M6 | M6 86 testes + drill IDÊNTICO |
| 1a | domínio puro (enums + entities + transicoes + repository Protocol) | 14 testes puros |
| 1b | schema infra (path aninhado ADR-0072) — models + 5 migrations RLS/WORM/grants/seed + UNIQUE documental + UNIQUE parcial não-overlap + mappers/repositories/query_service + drill | 13 testes PG-real + drill 12/12 |
| 2 | use cases cadastrar/revisar/publicar/revogar + `anexo_storage` (sha256 server-side) + ProcedimentoCalibracaoViewSet REST + idempotência + eventos WORM | 9 use cases + 7 API |
| 3 | wire-in `cobre_procedimento` no `configurar_calibracao` (ADR-0073, ordem escopo→procedimento, só RBC) + snapshot real c/ `numero_revisao` + predicate STUB deprecado | wire-in 5/5 + M4 chave reverde 676/676 PG-real |
| P7 (em Fatia 3) | INV-PROC-001..010 em REGRAS + `TestINV_PROC_001..010` + 3 hooks | 22/22 PG-real/puro + 17 casos hook |
| P8 | emendas PRD (AC-CAL-016-1/2) + matriz-feature-perfil + esta reconciliação | matriz + `--check` anti-drift OK |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-CAL-PROC-VIGENTE-PREDICATE (portão configuração) | ✅ FECHADO | Fatia 3 (`8171671`) — RBC sem procedimento PUBLICADO vigente → 412 `ProcedimentoVigenteAusente` |
| GATE-PROC-ANEXO-HASH | ✅ FECHADO | `sha256_server_side` recalcula o anexo no use case/REST (INV-PROC-007) |
| GATE-PROC-DRILL-LOCAL | 🟡 parcial | drill `validar_procedimentos_calibracao` 12/12 + `test_inv_proc_p2_schema_triggers` (RLS/WORM/UNIQUE/porta) PG-real entregues; **concorrência superseção cronometrada** (2 publicações simultâneas) = TRACK Wave A (padrão M4 ADR-0065 — invariante não-overlap já PROVADO pela UNIQUE parcial `test_inv_proc_008`) |
| GATE-PROC-ANEXO-B2 | 🟡 diferido | adapter `AnexoStorageLocal` entregue; B2 WORM real = Wave A (mesma porta) |
| GATE-PROC-METODO-VALIDADO | 🟡 fail-open lazy | `metodo_exige_validacao_pendente` só AVISA (INV-PROC-010); bloqueio duro entra com `licencas-acreditacoes` (Wave A) |
| GATE-PROC-VALIDACAO-7.11 | 🟡 diferido | parecer RBC credenciado da validação cl. 7.11 do gate de resolução — pré-produção (`project_sem_contratacoes_externas_ate_producao`); metrology-affecting reusa `faixa_cobertura` já cl. 7.11-validado no M6 |

## 6. Pendências (não bloqueiam fechamento do módulo)

- **GATE-PROC-DRILL-LOCAL (concorrência cronometrada)** — teste de 2 publicações
  simultâneas sob advisory lock = TRACK Wave A (PG-real threaded). O invariante de
  não-overlap (no máx 1 PUBLICADO vigente por chave) JÁ está garantido pela UNIQUE
  parcial e testado em `test_inv_proc_008`.
- **GATE-PROC-METODO-VALIDADO** — bloqueio duro de método não-validado (perfil A)
  entra com `licencas-acreditacoes` (Wave A). Hoje fail-open lazy = AVISO.
- **GATE-PROC-ANEXO-B2** — storage B2 WORM real do binário do PDF (Wave A).
- **Pendências externas** (diferidas — `project_sem_contratacoes_externas_ate_producao`):
  parecer RBC credenciado da validação de método cl. 7.2.2 + validação cl. 7.11 do
  gate de resolução — todas pré-produção.

## 7. Veredito de reconciliação

Todas as 10 INV-PROC têm enforcement real + teste nomeado (TST-004) + (onde aplicável)
hook camada A. As 6 US têm código + status. GATE central
(GATE-CAL-PROC-VIGENTE-PREDICATE no portão de configuração) FECHADO; suíte M4 chave
reverde 676/676 (zero regressão). Pronto para **P9 — ritual auditores roteados
(INV-RITUAL-003)**: seguranca (porta fail-closed + RLS + concorrência) ·
llm-correctness (cobertura bate docstring) · produto (AC binários + terminologia) ·
qualidade (INV-PROC testados) · observabilidade (eventos hash-chain) ·
idempotência. INV-RITUAL-001: MÉDIO+ bloqueia.
