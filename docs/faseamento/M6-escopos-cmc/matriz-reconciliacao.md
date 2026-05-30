---
owner: agente-ia
revisado-em: 2026-05-30
proximo-review: 2026-08-30
status: stable
diataxis: reference
audiencia: [agente, auditor]
marco: M6-escopos-cmc
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/M6-escopos-cmc/spec.md
  - docs/faseamento/M6-escopos-cmc/plan.md
  - docs/faseamento/M6-escopos-cmc/tasks.md
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — M6 `metrologia/escopos-cmc`

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec virou código real
> + teste + hook, e apontar o arquivo. Pré-requisito do ritual P8/P9 (reconciliação
> antes dos auditores roteados — INV-RITUAL-003). Estado: **Fatias 1a/1b/2/3/4 +
> P7 + P8 entregues**; PG-real consolidado em `GATE-ECMC-DRILL-LOCAL`.
> Path infra aninhado `src/infrastructure/metrologia/escopos_cmc/` (ADR-0072).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-ECMC-001 Cadastrar escopo/capacidade | herda AC-CAL-015-1 | INV-ECMC-001/002/006 | 0067/0074/0075 | **escopo-rbc-perfil-a-check** | `application/.../cadastrar_escopo.py` + `domain/.../entities.py`/`transicoes.py` + migrations 0001/0005 | ✅ |
| US-ECMC-002 Revisar escopo (versão preservada) | AC-CAL-015-2 | INV-ECMC-003 | 0030/0031 | — (trigger WORM) | `application/.../revisar_escopo.py` + migration 0003 | ✅ |
| US-ECMC-003 Revogar escopo (WORM Padrão B) | — | INV-ECMC-003/006 | 0029/0031 | — (trigger WORM) | `application/.../revogar_escopo.py` + `domain/.../transicoes.py` (`validar_motivo_revogacao`) | ✅ |
| US-ECMC-004 Validar cobertura na configuração (`cobre()` real → 412) | AC-CAL-002-2/015-1 + GATE-CAL-CMC-PREDICATE | **INV-ECMC-004/005** | 0073/0074/0066→0073 | **escopo-cobre-fail-closed-check** | `infrastructure/.../query_service.py` (`cobre`) + `domain/.../cobertura.py` + wire-in `application/.../calibracao/configurar_calibracao.py` (`CoberturaEscopoPort`) | ✅ (portão config FECHADO) |
| US-ECMC-005 Aviso degradante na recepção | AC-CAL-001-2 | INV-ECMC-004 | 0073 | — | `application/.../calibracao` recepção (aviso NÃO-RBC) | ✅ |
| US-ECMC-006 Importar escopo do PDF CGCRE + conferência | decisão N | **INV-ECMC-007** | 0025/0059(não ativada) | **escopo-extracao-nao-auto-persiste-check** | `domain/.../extracao.py` + `application/.../importar_escopo_pdf.py` + `confirmar_escopo_extraido.py` + `views.py` (`importar-extracao`/`confirmar-extraido`) | ✅ (linhas já extraídas; PDFlib diferido) |
| US-ECMC-007 Declarar capacidade interna (B/C/D `rbc=false` forçado) | decisão O | **INV-ECMC-002** | 0075/0067 | **escopo-rbc-perfil-a-check** | `application/.../cadastrar_escopo.py` (perfil B/C/D → `rbc_efetivo` força false) | ✅ |
| US-ECMC-008 Snapshot `EscopoUsado` + U≥CMC na emissão | ADR-0014 | **INV-ECMC-008/009** | 0014/0029/0074 | — | `domain/.../entities.py` (VO `EscopoUsado`) + `infrastructure/.../query_service.py` (`cmc_para`) | ✅ porta entregue; consumo emissão = GATE-ECMC-U-MAIOR-CMC Wave A |

## 2. INV-ECMC-001..009 ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-ECMC-001 | `UNIQUE (tenant, grandeza, faixa_min, faixa_max, procedimento_id, versao)` migration 0001 + `existe_chave_confirmada` | `TestINV_ECMC_001` + `test_inv_ecmc_p2_schema_triggers` | migration-metrology-classifier |
| INV-ECMC-002 | gate domínio `rbc_efetivo` (força false não-A) | `TestINV_ECMC_002` | **escopo-rbc-perfil-a-check** |
| INV-ECMC-003 | trigger PG WORM Padrão B `escopo_cmc` (UPDATE metrológico/DELETE) | `TestINV_ECMC_003` + `test_inv_ecmc_p2_schema_triggers` | — (trigger) |
| INV-ECMC-004 | porta `query_service.cobre()` fail-CLOSED | `TestINV_ECMC_004` | **escopo-cobre-fail-closed-check** |
| INV-ECMC-005 | `cobertura.faixa_contida`/`avaliar_contencao` (contenção total) | `TestINV_ECMC_005` | — (puro) |
| INV-ECMC-006 | `CadastrarEscopoInput.__post_init__` (tz-aware) + `vigente_em` | `TestINV_ECMC_006` | — |
| INV-ECMC-007 | `importar_escopo_pdf` só staging + `confirmar_escopo_extraido` único promotor (one-shot) | `TestINV_ECMC_007` | **escopo-extracao-nao-auto-persiste-check** |
| INV-ECMC-008 | VO frozen `EscopoUsado` (conteúdo probatório RBC-NC-06) | `TestINV_ECMC_008` | — |
| INV-ECMC-009 | `cobertura.avaliar_u_cmc`/`menor_cmc_por_faixa` + porta `cmc_para()` | `TestINV_ECMC_009` | — |

## 3. Hooks novos M6 P7 (camada A pré-commit)

| Hook | INV | Criado | Casos `_test-runner` | Status |
|------|-----|--------|----------------------|--------|
| escopo-rbc-perfil-a-check.sh | INV-ECMC-002 | P7 | 11 (ERBC1..b) | ✅ |
| escopo-cobre-fail-closed-check.sh | INV-ECMC-004 | P7 | 6 (ECFC1..6) | ✅ |
| escopo-extracao-nao-auto-persiste-check.sh | INV-ECMC-007 | P7 | 7 (EEXT1..7) | ✅ |

Total `_test-runner`: **474/474 verdes / 58 hooks ativos**.

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| 1a | domínio puro (enums + entities + cobertura + transicoes + repository Protocols) | 52 testes puros |
| 1b | schema infra (path aninhado ADR-0072) — models + 5 migrations RLS/WORM/grants/seed + mappers/repositories/query_service + drill | 11 testes PG-real + drill 17/17 |
| 2 | use cases cadastrar/revisar/revogar + EscopoCMCViewSet REST + idempotência + eventos WORM | 12 use cases + 7 API |
| 3 | wire-in `cobre()` no `configurar_calibracao` (ADR-0073) + SAN-FAIXA-CALIBRADA (`Calibracao.faixa_calibrada_declarada`, migration 0017) | configurar 24/24 PG-real |
| 4 | extração PDF determinística + staging + confirmação humana + REST | 15 parser + 8 use cases + 5 API |
| P7 | INV-ECMC-001..009 em REGRAS + `TestINV_ECMC_001..009` + 3 hooks | 33/33 PG-real + 24 casos hook |
| P8 | emendas PRD (AC-CAL-001-2/002-2/015-1/2) + matriz-feature-perfil + drill PG real + esta reconciliação | drill 17/17 + 33/33 regressão |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-CAL-CMC-PREDICATE (portão configuração) | ✅ FECHADO | SAN-FAIXA-CALIBRADA (commit `2af1d6d`) + Fatia 3 (`b246bc9`) — `cobre(declarada) ⊆ escopo` → 412 |
| GATE-ECMC-DRILL-LOCAL | ✅ FECHADO | drill `validar_escopos_cmc` 17/17 + `test_inv_ecmc_*` 33/33 PG-real |
| GATE-ECMC-EXTRACT-ENGINE | ✅ FECHADO | parser determinístico (NÃO IA) + replay fixture cl. 7.11 |
| GATE-ECMC-U-MAIOR-CMC | 🟡 Wave A | porta `cmc_para()` entregue; consumo na emissão = módulo `certificados` |
| GATE-ECMC-RT-VINCULO | 🟡 Wave A | vínculo RT↔escopo fail-open lazy documentado (paralelo ADR-0063); bloqueio real pré-1º tenant RBC externo |
| GATE-ECMC-COBERTURA-RBC | 🟡 diferido | revisão RBC credenciada da semântica U≥CMC — pré-tenant A (`project_sem_contratacoes_externas_ate_producao`) |
| GATE-ECMC-EXTRACT-PDFLIB | 🟡 diferido | porta binário-PDF→linhas (dep pdfplumber); REST recebe linhas já extraídas |

## 6. Pendências (não bloqueiam fechamento do módulo)

- **GATE-ECMC-U-MAIOR-CMC / GATE-ECMC-RT-VINCULO** — consumo na emissão e bloqueio
  RT efetivo entram com o módulo `certificados` (Wave A). Portas entregues no M6.
- **GATE-CAL-FAIXA-M2-SANIDADE** — sanidade da `Equipamento.faixa` texto livre do M2
  (origem alternativa da faixa) — frente própria.
- **Terminologia B/C/D** — rótulo "Capacidade interna declarada (sem acreditação
  RBC)" (refinamento RBC cl. 8.1.3) — decisão de produto aberta ao Roldão (veto).
- **Pendências externas** (diferidas — `project_sem_contratacoes_externas_ate_producao`):
  parecer RBC credenciado da cobertura U≥CMC + validação cl. 7.11 do parser + dossiê
  CGCRE assinado — todas pré-produção.

## 7. Veredito de reconciliação

Todas as 9 INV-ECMC têm enforcement real + teste nomeado (TST-004) + (onde aplicável)
hook camada A. As 8 US têm código + status. GATE central (GATE-CAL-CMC-PREDICATE no
portão de configuração) FECHADO. Pronto para **P9 — ritual auditores roteados
(INV-RITUAL-003)**: seguranca (porta fail-closed + RLS + anti-fraude rbc) ·
llm-correctness (cobertura bate docstring) · produto (AC binários + terminologia
ADR-0075) · qualidade (INV-ECMC testados) · observabilidade (eventos hash-chain) ·
idempotência. INV-RITUAL-001: MÉDIO+ bloqueia.
