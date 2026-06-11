---
owner: agente-ia
revisado-em: 2026-06-10
proximo-review: 2026-09-10
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: configuracoes-sistema
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/configuracoes-sistema/spec.md
  - docs/faseamento/configuracoes-sistema/plan.md
  - docs/faseamento/configuracoes-sistema/tasks.md
  - docs/adr/0080-numeracao-serie-documento-dois-regimes.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `configuracoes-sistema` (núcleo)

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec virou código real
> + teste + hook, e apontar o arquivo. Pré-requisito do ritual P8/P9 (reconciliação
> antes dos auditores roteados — INV-RITUAL-003). Estado: **Fatias 1a/1b/2 + P7/P8
> entregues**. Path achatado `src/{domain,application,infrastructure}/configuracoes_sistema/`
> (raiz própria — ADR-0072 só normatiza metrologia). Raiz da cadeia de preço
> (`docs/faseamento/plano-dependencia-sistema.md` frente #1).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-CFG-001 dados da empresa e filiais | AC-001-1 (edita + evento `Config.EmpresaAtualizada`), AC-001-2 (filial CNPJ próprio + 1 matriz), AC-001-3 (auditoria antes/depois) | INV-036/037 | 0017 (VO CNPJ), 0029/0064 (evento na cadeia) | — (UNIQUEs + domínio) | `domain/.../entities.py` + `application/.../empresa.py` (`validar_uma_matriz` no conjunto resultante) + `infrastructure/.../views.py` (`EmpresaConfigViewSet`, payload antes/depois no evento) + migration 0001 (`uq_cfg_empresa_cnpj` + `uq_cfg_filial_uma_matriz` parcial) | ✅ |
| US-CFG-003 impostos | AC-003-1 (campos por regime + figuras ADV-02/03), AC-003-2 (alíquota nova só vale p/ futuros — INV-026 via imutabilidade da linha) | **INV-CFG-IMPOSTO-IMUTAVEL** + **INV-CFG-IMPOSTO-SEM-SOBREPOSICAO** | 0030 (JanelaVigencia), 0031 Padrão B | **imposto-imutavel-check** | `domain/.../transicoes.py` (`imposto_vigente_em`/`ha_sobreposicao_vigencia`) + `application/.../imposto.py` + migrations 0003 (triggers worm/block-delete) + 0004 (exclusion `btree_gist`) + `ImpostoViewSet` | ✅ |
| US-CFG-002 numeração e séries | AC-002-1 (config série; regime DERIVADO), AC-002-2 (não diminuir — INV-028), AC-002-3 reescrito (sem duplicata em nenhum tipo; cancelamento não reusa — **INV-CFG-NUM-ATOMICA**, substitui o `INV-006` trocado do PRD TL-01) | INV-028 (reconciliada: sem `nf` ADV-04) + **INV-CFG-NUM-ATOMICA** | **0080** (2 regimes; gap-less reusa motor M8 TL-02), 0056 (estilo UPDATE atômico) | **serie-numeracao-regime-check** | `domain/.../transicoes.py` (`regime_numeracao_do_tipo`/`proximo_formatado`/`validar_proximo_numero_nao_diminui`) + `application/.../serie.py` (derivação; reset TL-07 do `{ano}`) + `infrastructure/.../repositories.py` (`_reservar_gap_less` advisory lock 880_402 + `_alocar_buracos_aceitos` 1 statement) + migrations 0001/0003 + `SerieDocumentoViewSet` | ✅ |
| US-CFG-004/014, US-CFG-005..013 | — | INV-029/030/038/039 | — | — | **Fora do núcleo** (§4 spec): authz/feature_flag JÁ existem; config fina diferida; retenção emendada na matriz | N/A |

## 2. INV ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-CFG-NUM-ATOMICA | advisory lock (tenant,serie,ano) + triggers `numero_doc_reservado_{consecutivo,one_shot,block_delete_confirmado}` + UNIQUE `uq_num_doc_reservado` (gap-less); UPDATE atômico row-lock (buracos) | `TestINV_CFG_NUM_ATOMICA` (4 testes) + `test_configuracoes_schema_fatia1b` (denso/expiração/consecutividade) + E2E reservar | **serie-numeracao-regime-check** |
| INV-CFG-IMPOSTO-IMUTAVEL | triggers `imposto_worm_check` (probatórios + one-shot `vigencia_fim`/`revogado_em`) + `imposto_block_delete` (retenção 5a) | `TestINV_CFG_IMPOSTO_IMUTAVEL` (4 testes) + E2E encerrar one-shot 200→409 | **imposto-imutavel-check** |
| INV-CFG-IMPOSTO-SEM-SOBREPOSICAO | exclusion `excl_imposto_vigencia_sobreposta` (btree_gist, COALESCE filial NULL, WHERE revogado IS NULL) + defesa `ha_sobreposicao_vigencia` no use case | `TestINV_CFG_IMPOSTO_SEM_SOBREPOSICAO` (3 testes: overlap RAISE / encadeado OK / revogada sai) + E2E 422 | — (constraint é a verdade) |
| INV-028 | trigger `serie_documento_inv028_check` (decremento + tipo/prefixo/regime imutáveis; exceção única reset anual TL-07) | `TestINV_028` (3 testes) + `test_configuracoes_schema_fatia1b` | serie-numeracao-regime-check (regime) |
| INV-036 | UNIQUE `uq_cfg_empresa_cnpj` (tenant, cnpj) | `TestINV_036` + E2E cnpj inválido 400 (VO) | — |
| INV-037 | UNIQUE parcial `uq_cfg_filial_uma_matriz` (≤1) + `validar_uma_matriz` no use case (≥1 com filiais) | `TestINV_037` + E2E 2ª matriz 422 | — |
| INV-TENANT-001..003 | RLS pattern v2 nas 5 tabelas (migration 0002) + FORCE | `test_rls_force_e_4_policies_nas_5_tabelas` + cross-tenant (empresa + série 404) | migration-rls-check |
| IDEMP-001 | Idempotency-Key obrigatória nos 6 POST (incl. reservar-numero — retry duplicaria número) | E2E `test_reservar_sem_idempotency_key_falha` + `test_serie_duplicada_409_e_replay_idempotente` | idempotency-key-header-check |

## 3. Hooks novos Fatia 3 (camada A pré-commit)

| Hook | INV | Casos `_test-runner` | Status |
|------|-----|----------------------|--------|
| serie-numeracao-regime-check.sh | INV-CFG-NUM-ATOMICA / ADR-0080 / ADV-04 | 8 (SNR1..8) | ✅ |
| imposto-imutavel-check.sh | INV-CFG-IMPOSTO-IMUTAVEL (TL-04) | 9 (IIM1..9) | ✅ |

Total `_test-runner`: **560/560 verdes / 72 hooks ativos** (gate anti-drift verde).
Ambos testados contra payloads maliciosos (6 BLOCK) e contra os arquivos REAIS da
frente (0 falso-positivo).

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| P0 | `T-CFG-000-investigacao.md` — greenfield + correção regra #0 (dívida de numeração fiscal NÃO existe; frente é #1 pela via tributária) | errata aplicada ao plano-dependencia |
| P1/P2 | spec v2 (3 agregados) + revisões tech-lead TL-01..09 + advogado ADV-01..08 (AMBOS aprova-com-correções) + **ADR-0080** | `reviews` incorporadas na spec §10 |
| P3 | emendas cross-doc (modelo-de-dominio, PRD AC-CFG-002-3, retenção +3 linhas + DRILL-RET-CFG-01, RAT) + plan + tasks | commits `2f015255`/`7d6b480` |
| 1a | domínio puro (enums/VOs/entities/transicoes/erros/repository) | 17 testes puros (`cb...44bcbb2`) |
| 1b | schema PG — 5 tabelas + 6 migrations (UNIQUEs/RLS v2/triggers/exclusion/grants/seed authz) + mappers/repositories (motor gap-less M8 reusado) + drill | drill `validar_configuracoes_sistema` **39/39** + 21 testes PG-real (`ebb297d`) |
| 2 | use cases (empresa/filial/imposto/série/reservar 2 regimes) + 3 ViewSets REST + ACTION_MAP + Idempotency + eventos `Config.*` (ACOES_CONFIG, cadeia hash) | 14 E2E (`6817...`) + django check 0 |
| 3/P7 | INV-CFG-* em REGRAS + INV-028 reconciliada + `TestINV_*` (16) + 2 hooks (17 casos) + contagens 72/560 | `_test-runner` 560/560 |
| P8 | esta reconciliação + ADR-0080 proposta→aceito (§11 AGENTS) + frontmatters draft→stable | `--check` anti-drift OK |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-CFG-NUM-DRILL-LOCAL | 🟡 TRACK Wave A | reserva gap-less sob concorrência CRONOMETRADA (threads PG-real) — espelha GATE-CER-DRILL-LOCAL; invariante de densidade já PROVADO por advisory lock + trigger consecutividade + UNIQUE (`TestINV_CFG_NUM_ATOMICA`) |
| GATE-CFG-TRIBUTARIO-CONTADOR | 🟡 pré-produção | conjunto final de regimes/figuras fiscais (ADV-01/02/08 + uso de `fatura` como duplicata) = validação contador/OAB humana; estrutura entregue (`project_sem_contratacoes_externas_ate_producao`) |
| GATE-CFG-RETROFIT-SERIE | 🟡 Wave B | OS/calibração migram da sequence própria (ADR-0056) para a série central; sem retrofit agora (anti-retrabalho — emissores atuais seguem válidos) |

## 6. Pendências (não bloqueiam fechamento do núcleo)

- **B10 (P9 produto) — interpretação registrada do AC-CFG-002-1:** `proximo_numero`
  inicial é SEMPRE 1 na criação da série (não configurável). Início ≠ 1 só faz
  sentido em regime BURACOS_ACEITOS (migração de numeração legada de OS/orçamento
  vinda de outro sistema) — em GAP_LESS um início > 1 criaria buraco congênito,
  violando INV-CFG-NUM-ATOMICA. Entra junto com **GATE-CFG-RETROFIT-SERIE**
  (Wave B), quando emissores legados migrarem pra série central.
- **GATE-CFG-NUM-DRILL-LOCAL** — concorrência cronometrada PG-real (TRACK Wave A).
- **Consumidores a jusante** (greenfield, seam pronto): `produtos-pecas-servicos` (frente
  #2), `precificacao`, `orcamentos` — consomem `Imposto.vigente_em` e `reservar_numero`.
- **Pendências externas** (pré-produção): GATE-CFG-TRIBUTARIO-CONTADOR (lista de
  regimes/figuras), consolidação RAT (ADV-06).

## 7. Veredito de reconciliação

As 3 INV-CFG novas + INV-028/036/037 reusadas têm enforcement real (trigger/constraint/
use case) + teste nomeado (TST-004) + (onde aplicável) hook camada A. As 3 US do núcleo
têm código + E2E. Numeração nasce CENTRAL com 2 regimes (ADR-0080) sem retrofit
prematuro dos emissores existentes. **Pronto para P9** (auditores roteados INV-RITUAL-003).

## 8. P9 — ritual auditores roteados (INV-RITUAL-003)

**FECHADO 2026-06-11.** 1ª passada (2026-06-10, 8 auditores roteados): 0 CRÍTICO /
0 ALTO / **7 MÉDIO** / ~16 BAIXO. Conserto causa-raiz em 6 commits (`b817e2b`
`4cc64f3` `b54d26d` `62d51ee` `86b87c3` `e1d3dc1`) — destaque: `editar_filial`
completo (M6), menor-livre SQL anti-join (M7), rota de eliminação PII migration
0007 (M5), `confirmar_numero(reserva_id)` molde M8 (M3). 2ª passada (2026-06-11,
7 auditores: 5 com MÉDIO + seguranca/observabilidade por área tocada): **7/7 PASS
ZERO C/A/M** — INV-RITUAL-001 satisfeito. Notas residuais rastreadas (replay=resumo
sem PII; B2 molde seed; GATE-IDEMP-EM-PROCESSO-TTL; CHANGELOG transversal) em
`auditoria-familia5.md` §6. **Frente FECHADA.**
