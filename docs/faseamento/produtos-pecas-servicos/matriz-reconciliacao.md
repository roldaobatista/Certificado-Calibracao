---
owner: agente-ia
revisado-em: 2026-06-11
proximo-review: 2026-09-11
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: produtos-pecas-servicos
tipo: matriz-reconciliacao
relacionados:
  - docs/faseamento/produtos-pecas-servicos/spec.md
  - docs/faseamento/produtos-pecas-servicos/plan.md
  - docs/faseamento/produtos-pecas-servicos/tasks.md
  - docs/adr/0081-duas-fontes-preco-lista-versus-tabela-venda.md
  - REGRAS-INEGOCIAVEIS.md
---

# Matriz de reconciliação spec↔código — frente `produtos-pecas-servicos` + TabelaPreco (núcleo)

> **Pra quê:** provar, item por item, que cada US/AC/INV da spec virou código real
> + teste + hook, e apontar o arquivo. Pré-requisito do ritual P8/P9 (INV-RITUAL-003).
> Estado: **Fatias 1a/1b/2/3 + P7/P8 entregues**. Path achatado
> `src/{domain,application,infrastructure}/produtos_pecas_servicos/` (D-PPS-1).
> Frente #2 da cadeia de preço (`docs/faseamento/plano-dependencia-sistema.md`).

## 1. US ↔ AC ↔ INV ↔ ADR ↔ Hook ↔ código

| US | ACs | INV | ADR | Hook validador | Arquivo de código | Status |
|----|-----|-----|-----|----------------|-------------------|--------|
| US-CAT-001 cadastrar item | AC-001-1 (item + v1 num POST), AC-001-2 (código dup → 409 PT) | **INV-PPS-CODIGO-UNICO** + **INV-PPS-PRECO-POSITIVO** | 0030 (JanelaVigencia), 0031 | — (UNIQUE + VO) | `application/.../item.py` (`cadastrar_item` — controla_estoque derivado TL-PPS-12/14) + `ItemCatalogoViewSet.cadastrar` + migration 0001 (`uq_pps_item_codigo` + CHECKs) | ✅ |
| US-CAT-002 atualizar preço sem afetar histórico | AC-002-1/2 (nova versão; consulta com data_referencia) + **anti-retroativa TL-PPS-08** | **INV-PPS-VERSAO-IMUTAVEL** + **INV-PPS-PRECO-NAO-RETROATIVO** | **0081**, 0031 Padrão B | — (triggers + domínio) | `domain/.../transicoes.py` (`validar_vigencia_nao_retroativa`/`versao_vigente_em`) + `application/.../item.py` (`nova_versao_preco` lock 880_403 + encerra anterior MESMA transação; `corrigir_versao` revoga+recria D-PPS-8) + migrations 0003/0004 | ✅ |
| US-CAT-003 criar kit | AC-003-1 (preço manual OU soma como default sugerido na CRIAÇÃO) | **INV-PPS-KIT-SEM-CICLO** | 0081 (kit = linha própria TL-PPS-09) | — (domínio) | `domain/.../transicoes.py` (`validar_kit_sem_ciclo` — 1 nível, filho ativo, sem repetido) + `application/.../item.py` (`montar_kit`) + `application/.../tabela.py` (`_sugerir_preco` SOMA_PARTES) | ✅ |
| US-CAT-004 importar planilha | AC-004-1 (CSV-only emendado P3) — staging + aceite POR LINHA + extras descartadas | **INV-PPS-IMPORTACAO-STAGING** | 0029 (hash), molde INV-ECMC-007 | **csv-safety-import** (reusado) + **pps-evento-pii-hash-check** | `domain/.../extracao_csv.py` (parser determinístico dialeto BR; "1.234" ambíguo rejeita) + `application/.../importacao.py` (registrar/aceitar [REUSA cadastrar_item]/rejeitar one-shot) + `ImportacaoCatalogoViewSet` + migrations 0007..0009 + command `limpar_importacoes_expiradas` (TTL 90d) | ✅ |
| US-CAT-005 inativar item | AC-005-1 (some de seleção/venda nova; histórico intacto) | (status ADR-0031; bloqueios em nova_versao/criar_linha/montar_kit/porta) | 0031 | — | `application/.../item.py` (`inativar_item`) + `ItemInativoError` 422 nos 4 caminhos | ✅ |
| TabelaPreco (promovida de V2) | porta fail-closed 422 `PrecoTabelaAusente` (US-OS-015) | **INV-PPS-LINHA-IMUTAVEL** + **INV-PPS-LINHA-SEM-SOBREPOSICAO** + **INV-PPS-PRECO-FAIL-CLOSED** | **0081** | **pps-porta-fail-closed-check** | `application/.../tabela.py` (criar_tabela 1 padrão D-PPS-3 / criar_linha default sugerido / corrigir_linha revoga+recria / encerrar_linha one-shot) + `infrastructure/.../query_service.py` (`preco_para_os` — contrato PrecoResolvido COMPLETO, data_referencia=contratação ADV-PPS-05) + `TabelaPrecoViewSet` (+ GET `preco-vigente`) | ✅ |

## 2. INV ↔ teste nomeado (TST-004) ↔ enforcement

| INV | Enforcement real | Teste (cita o ID) | Hook (camada A) |
|-----|------------------|-------------------|-----------------|
| INV-PPS-CODIGO-UNICO | UNIQUE `uq_pps_item_codigo` + consulta prévia no use case | `TestINV_PPS_CODIGO_UNICO` (PG) + E2E 409 | — |
| INV-PPS-VERSAO-IMUTAVEL | triggers `item_catalogo_versao_{worm,block_delete}_trg` + one-shot | `TestINV_PPS_VERSAO_IMUTAVEL` (PG) + `test_pps_schema_fatia1b` | — |
| INV-PPS-PRECO-NAO-RETROATIVO | `validar_vigencia_nao_retroativa` (domínio) + encerrar-anterior na MESMA transação | `TestINV_PPS_PRECO_NAO_RETROATIVO` (puro) + **regressão DURA** `test_regressao_inv026_dura_consulta_historica_nao_muda` (E2E) + E2E 422 | — |
| INV-PPS-LINHA-IMUTAVEL | triggers `linha_tabela_preco_{worm,block_delete}_trg` | `TestINV_PPS_LINHA_IMUTAVEL` (PG) + E2E corrigir-linha (revoga+recria) | — |
| INV-PPS-LINHA-SEM-SOBREPOSICAO | exclusions `excl_pps_{versao,linha}_vigencia` (btree_gist, WHERE revogado IS NULL) + `janelas_sobrepoem` no use case | `TestINV_PPS_LINHA_SEM_SOBREPOSICAO` (PG: overlap RAISE + revogada libera) + E2E 422 | — |
| INV-PPS-PRECO-FAIL-CLOSED | `preco_para_os` levanta `PrecoTabelaAusenteError` (sem fallback); kit exige linha própria | `TestINV_PPS_PRECO_FAIL_CLOSED` (Fakes) + 7 testes de contrato da porta (`test_pps_use_cases`) + E2E 422 `PRECO_TABELA_AUSENTE` | **pps-porta-fail-closed-check** |
| INV-PPS-KIT-SEM-CICLO | `validar_kit_sem_ciclo` (domínio) | `TestINV_PPS_KIT_SEM_CICLO` (puro) + E2E kit-em-kit 422 | — |
| INV-PPS-PRECO-POSITIVO | VO `Preco` (>0, escala 2 HALF_EVEN) + CHECKs no banco | `TestINV_PPS_PRECO_POSITIVO` (puro + PG) + reconciliação centavos TL-PPS-15 | — |
| INV-PPS-IMPORTACAO-STAGING | staging mutável separado; aceite one-shot via UPDATE escopado em `status='validada'`; parser rejeita ambíguo | `TestINV_PPS_IMPORTACAO_STAGING` (puro) + E2E `test_importar_cria_staging_e_nao_auto_persiste_item` + TTL | **pps-evento-pii-hash-check** + csv-safety-import |
| INV-TENANT-001..003 | RLS pattern v2 FORCE nas 7 tabelas (0002 + 0008) | `test_rls_isola_as_5_tabelas` + cross-tenant 404 (itens + importações) | migration-rls-check |
| IDEMP-001 | Idempotency-Key nos 12 POST (fingerprint = payload completo + alvo B6; importar = sha256 do arquivo) | E2E replay resumo B9 + sem-key 400 | idempotency-key-header-check |
| ADV-PPS-01/02 (LGPD eventos) | `criado_por_id_hash` (HMAC-tenant) + `descricao_hash`/`motivo_hash` (ADR-0029) em TODO payload `Catalogo.*` | hooks testados contra o views.py REAL (0 falso-positivo) | **pps-evento-pii-hash-check** |

## 3. Hooks novos P7 (camada A pré-commit)

| Hook | INV | Casos `_test-runner` | Status |
|------|-----|----------------------|--------|
| pps-porta-fail-closed-check.sh | INV-PPS-PRECO-FAIL-CLOSED / ADR-0081 | 6 (PPFC1..6) | ✅ |
| pps-evento-pii-hash-check.sh | ADV-PPS-01/02 / ADR-0029 | 7 (PEPH1..7 — PEPH7 `nome_tabela` adicionado no conserto LGPD-M1) | ✅ |

Total `_test-runner`: **573/573 verdes / 74 hooks ativos** (gate anti-drift verde).
Ambos testados contra payloads maliciosos (5 BLOCK) e contra os arquivos REAIS
da frente (0 falso-positivo; fingerprint de idempotência com `motivo` NÃO dispara).

## 4. Entregas por fase

| Fase | Entrega | Verificação |
|------|---------|-------------|
| P0 | `T-PPS-000-investigacao.md` — greenfield; seams frente #1; TabelaPreco promovida (US-OS-015) | dossiê |
| P1/P2 | spec v2 + revisões tech-lead TL-PPS-01..16 + advogado ADV-PPS-01..09 (AMBOS aprova-com-correções, 0 crítico) + **ADR-0081 proposta** | spec §10 |
| P3 | emendas cross-doc (faseamento Wave B→A; modelo-de-dominio; retenção +2 + DRILL-RET-PPS-01; RAT-PPS-CRIADO-POR; AC-CAT-004-1 CSV-only) + plan + tasks | commit `e570e56` |
| 1a | domínio puro (enums + VO Preco + entidades frozen + transições + erros + Protocols) | 16 testes puros (`0742529`) |
| 1b | schema PG — 5 tabelas + 6 migrations (UNIQUEs/RLS v2/WORM molde Imposto/exclusions/grants/seed `catalogo.*`) + repos (advisory 880_403) + drill | 13 PG-real + drill 29/29 (`8a8b0a2`) |
| 2 | use cases (cadastrar/nova-versão/corrigir ×2/inativar/montar-kit/criar-tabela/criar-linha/encerrar) + porta `preco_para_os` + 2 ViewSets + 8 eventos `Catalogo.*` | 30 puros + 16 E2E incl. **INV-026 dura** + **concorrência 2 criar-versão** (`6d05841`) |
| 3 | importação CSV staging (parser BR + registrar/aceitar/rejeitar + TTL 90d + SHA-256 no evento) + drill 36/36 | 11 testes (6 parser + 5 E2E) (`5f6c845`) |
| P7 | INV-PPS-* (9) em REGRAS + `TestINV_PPS_*` (12) + 2 hooks (12 casos) + contagens 74/572 | `_test-runner` 572/572 |
| P8 | esta reconciliação + **ADR-0081 proposta→aceito** (§11 AGENTS + arquivo) + frontmatters stable | `--check` anti-drift OK |

## 5. GATEs do módulo

| GATE | Estado | Evidência / pendência |
|------|--------|------------------------|
| GATE-PPS-WIREIN-OS | 🔴 **bloqueante pré-1º tenant externo** | preço da OS avulsa hoje é client-supplied (`ordens_servico/views.py:507`); a FONTE (porta `preco_para_os`) está pronta e testada — o wire-in é da frente OS (não desta) |
| GATE-PPS-XLSX | 🟡 V2 | dep `openpyxl` (DEP-001); "salvar como CSV" resolve onboarding |
| GATE-PPS-OUTBOX-ESTOQUE | 🟡 Wave A/B | eventos `Catalogo.*` promovem a outbox `_schema_version: v1` quando estoque/orçamentos chegarem (TL-PPS-05) |
| `[OAB-PRE-PROD]` ToS importação | 🟡 pré-produção | cláusula titularidade/indenidade dados importados (ADV-PPS-07 — lote único ToS/DPA) |
| GATE-PPS-KIT-BATCH (P9 PERF-B2) | 🟡 condição do WIREIN-OS | decomposição de kit resolve versões POR filho (K+1 queries); aceitável kit<10 partes — método em lote (`item_id IN (...)`) obrigatório ANTES do wire-in na OS (M×(K+1) no caminho quente) |
| GATE-PPS-RETRIEVE-PAGINACAO (P9 PERF-B3) | 🟡 UI Wave A | `tabelas/{id}/` serializa TODAS as linhas (vigentes+encerradas+revogadas) — paginação/filtro `?vigentes_em=` quando a UI consumir |
| GATE-IDEMP-EM-PROCESSO (P9 IDEMP-B1) | 🟡 transversal F-C | chave presa `em_processo` após crash sem `falhar_chave` devolve 425 além do TTL (`_avaliar_existente` checa EM_PROCESSO antes de `expira_em`) — carryover do serviço compartilhado (M2/M4/CFG idem); conserto transversal, não desta frente |
| GATE-OBS-METRIC-PPS (OBS-003) | 🟡 carryover M5..M9 | métrica de endpoint fecha quando Prometheus fizer scrape (GATE-OBS-METRIC-SCRAPE-1) |

## 6. Pendências (não bloqueiam fechamento do núcleo)

- **Multi-tabela por cliente/segmento** — frente `precificacao` (#3)/V2; schema já N-tabelas (D-PPS-3).
- **Recálculo de orçamentos abertos** ao alterar preço — consumidor futuro de `Catalogo.PrecoAlterado` (frente #5).
- **mypy serializers** — `Missing type parameters for generic type "Serializer"` (molde tolerado M6/M8/M9/CFG; só `serializers.py`).
- **Consumidores a jusante** (seam pronto): `precificacao` (#3), `orcamentos` (#5), `estoque` (`controla_estoque` no item).

## 7. Veredito de reconciliação

As 9 INV-PPS têm enforcement real (trigger/constraint/domínio/use case) + teste
nomeado (TST-004) + (onde aplicável) hook camada A. As 5 US do núcleo + TabelaPreco
têm código + E2E PG-real (incl. regressão INV-026 DURA e concorrência sob advisory
lock). A porta `preco_para_os` nasce fail-closed com contrato probatório completo
(ADR-0081 aceita). Importação é staging-only com TTL e prova permanente por SHA-256.
**Pronto para P9** (auditores roteados INV-RITUAL-003).

## 8. P9 — ritual auditores roteados (INV-RITUAL-003)

**1ª passada (2026-06-11, 8 auditores roteados):** seguranca · qualidade ·
llm-correctness · produto · idempotencia · conformidade-lgpd · performance ·
observabilidade = **8× CONCERNS — 0 CRÍTICO / 0 ALTO / 9 MÉDIO / ~20 BAIXO**.
Supplychain N/A (CSV-only mantido — zero dep nova).

**Conserto causa-raiz (mesmo dia — regra resolver-TUDO):** 9/9 MÉDIOS + 14 BAIXOs
de código + 6 emendas de doc. Destaques: migration **0010** (colunas motivo
200→600 — DataError 500 eliminado) + **0011** (trigger `item_catalogo_imutavel_trg`
QUAL-M1; CHECK `fim>=inicio` ×2; patch WORM motivo pré-revogação); parser valida
agrupamento de milhar (QUAL-M2) + comprimento por campo (SEG-M1b); `montar_kit`
com advisory lock + IntegrityError→409 (IDEMP-M1); `nome_tabela_hash` em WORM +
hook estendido PEPH7 (LGPD-M1); `obter_linha` pontual (PERF-M1);
`Catalogo.LinhaImportacaoRejeitada` (OBS-M1); glossário do módulo emendado
(PROD-M1); `ImportacaoAusenteError`/`agora_utc`/`listar` órfãos removidos
(LLM-M1/B2/B4); `_falha` sem detail PG cru + `codigo` estável; logs OBS-B1..B4;
RLS estrutural 7/7 + UNHAPPY staging em pytest. BAIXOs não-acionáveis viraram
GATE rastreado (§5). Verificado PG real: suíte PPS **105/105** (contagem por
`--collect-only`: 16 domínio + 31 use cases + 17 E2E + 14 importação + 14 schema
+ 13 INV nomeadas; o "106" anotado no commit do conserto era soma manual com
off-by-one) + hooks 573/573 + anti-drift (74/573/82/148) + makemigrations limpo.

**2ª passada (2026-06-11, mesmos 8 auditores roteados):** **8/8 PASS — ZERO
CRÍTICO / ZERO ALTO / ZERO MÉDIO.** Cada auditor confirmou seu(s) MÉDIO(s) da
1ª passada resolvido(s) na CAUSA-RAIZ + varreu o diff do conserto sem regressão
nova: seguranca (SEG-M1 em 4 camadas: coluna 600 + LIMITES_CAMPO + DataError→400
com falhar_chave + teste) · qualidade (trigger `item_catalogo_imutavel_trg` real
no banco + patch WORM estritamente aditivo, listas de campos idênticas à 0003) ·
llm-correctness (órfãos zero referências; docstrings verazes) · produto (glossário
stable coerente ADR-0081; ACs reconferidos; zero scope creep) · idempotencia
(lock 880_403 no `montar_kit` + IntegrityError→409 + chave nunca presa; GATE
carryover legítimo) · conformidade-lgpd (PEPH7 executado com evidência BLOCK/PASS;
8 eventos `Catalogo.*` 100% hashificados) · performance (obter_linha nas 4 camadas;
GATEs KIT-BATCH/PAGINACAO com condição objetiva) · observabilidade
(`LinhaImportacaoRejeitada` atômica na mesma transação; processor F-C2 confirmado
no código). Único resíduo da 2ª passada (BAIXO drift interno — contador PEPH §3)
corrigido neste mesmo fechamento. **Verificação dinâmica do fechamento (PG real,
2026-06-11):** suíte PPS 105/105 + drill `validar_produtos_pecas_servicos` 36/36
+ hooks `_test-runner` 573/573 + gate anti-drift OK (74/573/82/148) +
makemigrations --check limpo. **INV-RITUAL-001 SATISFEITO — frente FECHADA.**
