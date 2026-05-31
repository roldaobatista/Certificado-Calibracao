---
owner: agente-ia
revisado-em: 2026-05-31
proximo-review: 2026-08-31
status: ready-for-implement
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M8-certificados
tipo: tasks-faseamento
relacionados:
  - docs/faseamento/M8-certificados/spec.md
  - docs/faseamento/M8-certificados/plan.md
  - docs/faseamento/M8-certificados/reviews-consolidado.md
  - docs/adr/0077-orcamento-incerteza-por-ponto-calibracao.md
  - docs/adr/0078-certificados-tabela-achatada-logica-aninhada.md
  - docs/adr/0076-fonte-faixa-cobertura-declarada-config-vs-pontos-emissao.md
  - docs/adr/0074-cobertura-rbc-tridimensional-faixa-u-maior-cmc.md
  - docs/adr/0073-validacao-cobertura-metrologica-no-use-case.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
---

# Tasks — M8 `metrologia/certificados` (núcleo metrológico de emissão)

> Deriva do `plan.md` (ready-for-tasks). IDs `T-CER-NNN`. Path **híbrido (ADR-0078,
> decisão tech-lead 2026-05-31):** a **tabela/model `Certificado` permanece em
> `infrastructure/certificados/` (NÃO-aninhado)** porque o trigger cross-app
> `equipamento_imutabilidade_pos_cert_check` (`certificados/migrations/0001`
> linhas 73-78) faz `SELECT ... FROM certificados WHERE status='emitido'` com nome
> de tabela + literal `'emitido'` **hard-coded** — mover `db_table`/app/valor quebra
> INV-025 silenciosamente e desalinha o hook `equipamento-imutabilidade-check.sh`
> (que allowlista o path). Migration **estritamente aditiva** (`ADD COLUMN` +
> `AlterField` que só ESTENDE choices, nunca renomeia/dropa). **Toda a lógica nova**
> (reconciliação, use cases, mappers, entidades) vai em
> `domain/metrologia/certificados/` + `infrastructure/metrologia/certificados/`
> (path aninhado ADR-0072). Portas `cmc_para` e `U(ponto)` = funções de módulo
> injetadas (ADR-0073), fail-closed/fail-safe. `/implement` segue esta ordem, fatia
> por fatia, cada fatia com seu ciclo de auditores (INV-RITUAL-002 + INV-RITUAL-003).
> Verificar (`--no-cov --reuse-db`) antes de afirmar.

> **Item #0 FECHADO (pré-requisito):** ADR-0077 (orçamento de incerteza POR PONTO,
> frente SAN-INCERTEZA-PONTO) já implementada. A reconciliação **lê** o read-model
> `U(ponto)` por `ponto_calibracao` (1:N) — **NÃO deriva U, NÃO usa o agregado
> pior-caso** `OrcamentoIncerteza.U_expandida` (não-normativo, INV-CAL-INC-005).
> **Nomes canônicos do upstream (verificados no código M4 — evita recriar VO):**
> domínio = `OrcamentoPorPontoSnapshot` (`src/domain/metrologia/calibracao/entities.py:237`);
> model de infra = `OrcamentoPorPonto` (`src/infrastructure/calibracao/models.py:1115`,
> `db_table='orcamento_por_ponto'`), **no path ACHATADO `infrastructure/calibracao/`**
> (NÃO `infrastructure/metrologia/calibracao/` — dívida ADR-0072 do M4; a porta de
> leitura aponta pro path achatado legado).

---

## Fatia 0 — Peça compartilhada de reconciliação (puro, reuso M6/M7)

| ID | Tarefa | Saída / teste | Cobre |
|----|--------|---------------|-------|
| T-CER-001 | `domain/metrologia/certificados/reconciliacao.py`: avaliador puro `reconciliar_pontos(...)` que COMPÕE (não reimplementa) as funções REAIS verificadas no código: **`faixa_cobertura.faixa_contida(*, solicitada, escopo)`** (faixa⊆faixa, M7) + **`value_objects.FaixaMedicao.contem(valor)`** (ponto∈faixa — usar ESTE p/ "ponto ∈ faixa_calibrada_declarada"; NÃO existe `contem` em `faixa_cobertura.py`) + `escopos_cmc.cobertura.avaliar_u_cmc` (M6, U≥CMC). Recebe pontos medidos agrupados + `faixa_calibrada_declarada` + `U(ponto)` (porta lookup) + `cmc(ponto)` (porta `cmc_para`) + perfil; classifica cada ponto por **precedência fixa** `FORA_DECLARADA > SEM_CMC > U_MENOR_CMC > RBC_OK` (C-04, replay cl. 7.11). **Seta `u_igual_cmc_suspeita=True` quando `U(ponto)` for EXATAMENTE igual a `CMC(ponto)` (igualdade Decimal — NC-06 anti-cópia de CMC como U; flag, não bloqueia)** | módulo novo, só Decimal, zero import Django; testes puros das 4 classes + precedência + caso `U==CMC` seta flag | INV-CER-RECONCILIA-001/002 + ADR-0073/0074 + NC-06 |
| T-CER-002 | `reconciliar_pontos` retorna VO puro `ReconciliacaoCertificado` (lista `PontoReconciliado` + partição `pontos_rbc`/`pontos_nao_rbc` + `faixa_certificado=[min,max]` dos VÁLIDOS + flag `pode_emitir_rbc`). `U(ponto)` (read-model 1:1 por `ponto_calibracao`) duplicado p/ o mesmo ponto → `ORCAMENTO_PONTO_AMBIGUO` fail-closed (C-01). Ausente → `SEM_ORCAMENTO`. Reusa VO `value_objects.NumeroCertificado` (formato verificado `<SLUG>-<YYYY>-<NNNNNN>`) — NÃO recriar | testes: lookup 1:1 (nunca soma U por repetição), duplicidade fail-closed, ausência | INV-CER-RECONCILIA-005 (lookup único, anti dupla-contagem) |
| T-CER-003 | **Reuso verificado SEM recriar:** `faixa_cobertura.py` (M7 — `faixa_contida`/`avaliar_contencao`), `escopos_cmc/cobertura.py` (M6 `avaliar_u_cmc`/`menor_cmc_por_faixa`), `value_objects.FaixaMedicao.contem`. Reverde M6 (`test_inv_ecmc_*` + `validar_escopos_cmc` 17/17) + M7 (`test_inv_proc_*` + drill) **idênticos** — zero regressão | gate anti-regressão (commit isolado): `pytest tests/test_m6_escopos_cmc_cobertura_p1.py tests/test_m7_faixa_cobertura.py tests/regressao/test_inv_ecmc_classes_nomeadas.py tests/regressao/test_inv_proc_classes_nomeadas.py --no-cov` verde | reuso D-PROC-6 / TL plan §2 |
| T-CER-004 | **Porta `cmc_para` declarada explicitamente (TL plan §1 / ADR-0073/0074 cond. 2 — fecha GATE-ECMC-U-MAIOR-CMC de forma verificável):** `domain/metrologia/certificados/portas.py` declara Protocol/função injetada `CmcParaPort` — `cmc_para(*, tenant_id, grandeza, ponto, data) -> Decimal | None` (2ª porta de EMISSÃO, distinta de `cmc_cobre`/config M6; seam spec §2 `escopos_cmc/query_service.py`). É a porta consumida por `reconciliar_pontos` (T-CER-001) p/ obter `CMC(ponto)`. Fake + teste de CONTRATO: `None` → ponto classificado `SEM_CMC`; valor → avaliação `U(ponto) ≥ CMC` via `avaliar_u_cmc` (U<CMC ⇒ `U_MENOR_CMC`) | Protocol + Fake; teste contrato None/valor; usado em T-CER-001 | INV-CER-RECONCILIA-002 + ADR-0074 cond. 2 / GATE-ECMC-U-MAIOR-CMC |

---

## Fatia 1a — Domínio puro (P1, sem Django — ORDEM tech-lead plan §5)

| ID | Tarefa | Saída / teste | Cobre |
|----|--------|---------------|-------|
| T-CER-010 | `domain/metrologia/certificados/enums.py`: `EstadoCertificado` (`RASCUNHO`/`EMITIDO`/`SUBSTITUIDA`/`REVOGADO` — estende stub, str-enum) com properties `terminal`/`emitido`/`consultavel`; `ClassificacaoPonto` (`RBC_OK`/`FORA_DECLARADA`/`U_MENOR_CMC`/`SEM_CMC`/`EXCLUIDO`); `DecisaoReconciliacaoRT` (`EXCLUIR_PONTO`/`EMITIR_NAO_RBC_NO_PONTO`/`ABORTAR`); `CategoriaMotivoExclusao` (`PADRAO_FORA_VALIDADE`/`FALHA_REPETIBILIDADE`/`U_MAIOR_QUE_CMC_BUG`/`PONTO_FORA_FAIXA_DECLARADA`/`CONDICAO_AMBIENTAL_NC`/`OUTRO`). **Comentário no enum esclarece (BAIXO mapeamento):** `ClassificacaoPonto.U_MENOR_CMC` (incerteza U declarada MENOR que a CMC do escopo) é metrologicamente o caso "CMC declarada otimista demais" e mapeia, na exclusão, para `CategoriaMotivoExclusao.U_MAIOR_QUE_CMC_BUG` — nomes de direção aparente oposta descrevem o MESMO fenômeno | testes enum (properties + serialização JSON nativa) | C-02 / plan §3 |
| T-CER-011 | `domain/metrologia/certificados/reconciliacao_hash.py`: `reconciliacao_hash` PURO — encadeia `PontoReconciliadoSnapshot` ordenados por `ponto_calibracao` ASC (ordenação canônica determinística ANTES do hash E do cálculo de `faixa_certificado` — INV-CER-RECONCILIA-004). Payload congela por ponto `{ponto, valor_reportado, U, k, nivel_confianca, ν_eff, classificacao, incluido_no_certificado, cmc_no_ponto}` + cabeçalho `{versao_reconciliacao, faixa_certificado_min/max, tipo_acreditacao}`. Reusa `canonicalizar_payload_para_hmac` + `formatar_hash_versionado` (Decimal→str/UUID→str antes) | testes: determinismo (mesma entrada → mesmo hash), ordenação, replay; NÃO confundir com `replay_determinismo_hash` (cálculo agregado) nem `cadeia_pontos_hash` (ADR-0077 upstream) | INV-CER-RECONCILIA-004 + INV-DOC-CANON-001 + INV-HMAC-001..005 (C-05) |
| T-CER-012 | `domain/metrologia/certificados/entities.py`: `PontoReconciliadoSnapshot` (frozen) — `ponto_calibracao`, `valor_reportado`, `U_no_ponto`, `k_no_ponto`, `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto` (NC-05), `cmc_no_ponto` (None não-RBC), `classificacao`, `u_igual_cmc_suspeita BOOL` (NC-06 flag, não bloqueia — preenchido em T-CER-001), `incluido_no_certificado BOOL`, `ressalva_nao_rbc` (C-03: texto obrigatório quando `EMITIR_NAO_RBC_NO_PONTO`) | frozen dataclass + testes | NC-05/06 + INV-CER-RESSALVA-001 |
| T-CER-013 | `entities.py`: `CertificadoSnapshot` (frozen, WORM) — id, tenant, `calibracao_id`, `equipamento_id`, `numero_interno` (sequence), `numero_certificado` (VO `NumeroCertificado`), `versao`, `versao_anterior_id` (None p/ v1), `status='emitido'` (contrato trigger ADR-0078), `perfil_emissor_no_momento CHAR(1)`, `faixa_certificado_min/max`, `tipo_acreditacao` (RBC/NAO_RBC), `snapshot_equipamento_json`, **`snapshot_padroes_usados_json` (NC-07 — lista de padrões usados com `padrao_id` + `calibracao_padrao_vigencia_fim` congelada por padrão, p/ confirmar vigência na data de emissão, cl. 6.5)**, cliente ref hash, `regra_decisao_snapshot` (NC-04), `reconciliacao_hash`, `emitido_em`, `correlation_id`. Reusa `EscopoUsado`/`ProcedimentoUsado`/`OrcamentoPorPontoSnapshot` (NÃO recriar — nomes verificados no M4) | frozen dataclass + **teste round-trip serializa→desserializa TODOS os campos** | INV-CER-SNAPSHOT-PERFIL-001 + INV-CER-REGRA-DEC-001 + INV-CER-RECONCILIA-003 + INV-CER-PADRAO-VIG-001 (NC-07) |
| T-CER-014 | `entities.py`: `AnaliseReconciliacaoCertificado` (frozen, WORM, padrão ADR-0070) — decisão RT por ponto problemático: `decisao_rt` + `categoria_motivo` (C-02) + justificativa canonicalizada + hash. **Ligada a `calibracao_id`** (existe ANTES da emissão), não a `certificado_id` | frozen dataclass + testes + **teste binário do mapeamento `classificacao→categoria` (BAIXO):** `classificacao=U_MENOR_CMC` com `decisao_rt=EXCLUIR_PONTO` aceita `categoria_motivo ∈ {U_MAIOR_QUE_CMC_BUG, OUTRO}`; asserção falha se categoria incoerente | NC-03 + C-02 / cl. 7.10.1 |
| T-CER-015 | `domain/metrologia/certificados/transicoes.py`: máquina de estados EXPLÍCITA `_TRANSICOES_VALIDAS` = `{RASCUNHO→{EMITIDO}, EMITIDO→{SUBSTITUIDA, REVOGADO}}`. **`RASCUNHO` declarado (compat stub) mas NÃO materializado** — reconciliação + `AnaliseReconciliacaoCertificado` penduram em `calibracao_id`, SEM linha em `certificados` até `emitir`. `pode_transicionar()` + `validar_motivo_reemissao` (≥50 chars US-CER-004) + `validar_completude_decisoes_rt` (perfil A: ponto não-RBC sem decisão → bloqueia) | testes transição + bloqueios (inclui `emitido→substituida` one-shot válido) | máquina estados plan §3 + INV-CER-WORM-001 |
| T-CER-016 | `domain/metrologia/certificados/repository.py`: `@runtime_checkable` Protocol `CertificadoRepository` — `obter_por_id`, `existe_chave`, `proximo_numero_interno`, `salvar_novo` (snapshot + N `PontoReconciliadoSnapshot` atômico), `atualizar_com_lock` (CAS revision), `marcar_substituida` (one-shot). Protocol separado `AnaliseReconciliacaoRepository` (por `calibracao_id`: `salvar_decisao`, `listar_por_calibracao`, `existe_decisao_para_ponto`). Imports SEMPRE Protocol, nunca Model Django | runtime_checkable + Fakes | ADR-0007 / plan §3 |
| T-CER-017 | Porta de leitura `U(ponto)` declarada como Protocol `LeituraOrcamentoPorPontoPort` injetável (ADR-0073) — resolve `U_expandida_no_ponto`+`k`+`nivel`+`ν_eff` por `ponto_calibracao` via lookup único; fail-closed (ambíguo/ausente → erro tipado). **Nome canônico (BAIXO anti-recriação):** lê o domínio `OrcamentoPorPontoSnapshot`; o adapter de infra (T-CER-027) consulta o model `OrcamentoPorPonto` (`db_table='orcamento_por_ponto'`) no path ACHATADO `infrastructure/calibracao/` (NÃO aninhado) | Protocol + Fake; teste lookup 1:1 | INV-CER-RECONCILIA-005 |
| T-CER-018 | **Testes puros da fatia 1a** consolidados em `tests/test_m8_certificados_dominio_p1.py` (espelha `test_m7_procedimentos_dominio_p1.py`): reconciliação completa (partição rbc/não-rbc + `faixa_certificado` dos válidos + precedência + caso `U==CMC` seta flag NC-06), `reconciliacao_hash` determinístico, máquina de estados, ressalva não-RBC obrigatória, mapeamento classificacao→categoria. Zero PG, zero Django | `pytest tests/test_m8_certificados_dominio_p1.py --no-cov` verde | gate fatia 1a |

---

## Fatia 1b-schema — Schema + persistência (P2, ADR-0078 achatada — TL-02)

| ID | Tarefa | Nota | Cobre |
|----|--------|------|-------|
| T-CER-020 | Migration **aditiva** `infrastructure/certificados/migrations/0002_emissao_metrologica.py`: `AddField` em `certificados` (NÃO renomear/dropar; preservar `db_table='certificados'`, `app_label='certificados'`, manager default `CertificadoVigentesManager`, literal `StatusCertificado.EMITIDO='emitido'` intocado): `calibracao_id` (FK PROTECT), `numero_interno` (BigInt), `numero_certificado` (CharField), `versao` (int default 1), `versao_anterior_id` (UUID null), `perfil_emissor_no_momento` (CHAR(1) NOT NULL), `faixa_certificado_min/max` (Decimal null), `tipo_acreditacao` (choices RBC/NAO_RBC), `snapshot_equipamento_json` (JSONB), `snapshot_padroes_usados_json` (JSONB — NC-07 vigência congelada dos padrões), `regra_decisao_snapshot` (JSONB null), `reconciliacao_hash` (CharField), `correlation_id`, `revision` (int CAS), `emitido_em`. **`migrations.AlterField` na coluna `status` ESTENDENDO os choices (o stub real tem só `rascunho`/`emitido`/`revogado`) com `('substituida','Substituída (reemissão versionada)')`** — aditivo/não-destrutivo: o trigger INV-025 só lê `'emitido'`, então adicionar `'substituida'` não toca o contrato. **PRÉ-REQUISITO DURO da Fatia 2:** sem esta choice, `reemitir_certificado` (T-CER-043, `v(N)→SUBSTITUIDA`) gravaria status inexistente e estouraria tarde. Cabeçalho `# metrologia-classificacao: OQ` + `# replay-fixture: none` + `# replay-fixture-aceite: ADD COLUMN + estender choice status emissão metrológica sem afetar cálculo upstream` (espelha calibracao 0018) | aditiva pura sobre stub; INV-025 intocado; choice `substituida` pronta p/ Fatia 2 | ADR-0078 / TL-01 / INV-CER-SNAPSHOT-PERFIL-001 / INV-CER-PADRAO-VIG-001 |
| T-CER-021 | `infrastructure/certificados/migrations/0003_ponto_e_analise_reconciliacao.py`: 2 tabelas novas — `ponto_reconciliado` (id UUID, tenant FK PROTECT, certificado FK PROTECT, `ponto_calibracao`, `valor_reportado`, `U_no_ponto`, `k_no_ponto`, `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto` sentinela 999999, `cmc_no_ponto` null, `classificacao`, `u_igual_cmc_suspeita`, `incluido_no_certificado`, `ressalva_nao_rbc` TEXT, criado_em/atualizado_em) + `analise_reconciliacao_cert` (id UUID, tenant FK, `calibracao_id` FK, `ponto_calibracao`, `decisao_rt`, `categoria_motivo`, justificativa, hash, criado_em). UNIQUE `(tenant, certificado, ponto_calibracao)` em ponto_reconciliado + `(tenant, calibracao_id, ponto_calibracao)` em analise. `# metrologia-classificacao: IQ` + `# replay-fixture: none` + `# rls-policy: external 0004` | tabelas com tenant_id + índices | INV-CER-RECONCILIA-003/005 + NC-03 |
| T-CER-022 | `infrastructure/certificados/migrations/0004_rls_reconciliacao.py`: RLS v2 (molde M7 `_rls_forward`) nas 2 tabelas novas — ENABLE + FORCE + 4 policies (SELECT/UPDATE/DELETE `app.tenant_ids`; INSERT `app.active_tenant_id`). (A tabela `certificados` já tem RLS no `0001`.) | satisfaz `migration-rls-check.sh` (CREATE POLICY presente) | INV-TENANT-001..004 |
| T-CER-023 | `infrastructure/certificados/migrations/0005_triggers_worm_reconciliacao.py`: WORM Padrão B — `ponto_reconciliado_block_delete` + `ponto_reconciliado_worm_check` (INSERT-only, campos técnicos imutáveis); `analise_reconciliacao_cert_block_delete` + worm one-shot. **NÃO tocar** o trigger `equipamento_imutabilidade_pos_cert_check` do `0001` (lê `'emitido'` literal). Trigger WORM em `certificados`: bloqueia UPDATE de campos técnicos pós `status='emitido'` exceto `revogado_em`/`versao_anterior` one-shot + bump revision; **aceita a transição `emitido→substituida` one-shot (reemissão T-CER-043)** | INSERT-only nas tabelas de reconciliação; transição `emitido→substituida` permitida one-shot | INV-CER-WORM-001 + INV-SOFT-002 |
| T-CER-024 | `infrastructure/certificados/migrations/0006_grants_app_user.py`: GRANT SELECT/INSERT/UPDATE/DELETE em `ponto_reconciliado`, `analise_reconciliacao_cert` TO app_user (certificados já tem grant no stub) | grants OWNER=app_migrator em PROD | infra |
| T-CER-025 | `infrastructure/certificados/migrations/0007_seed_authz_certificados.py`: ações canônicas `certificados.{ver, emitir, reemitir, decidir_ponto, revogar}` × matriz papel (admin_tenant/gerente_operacional/signatario = todas; metrologista_bancada/atendente = só `ver`). Idempotente `ON CONFLICT DO NOTHING`; DISABLE/INSERT/re-CREATE POLICY. `# policy-test-coverage: skip` | bloqueio RBC só-A é RUNTIME via `tenant_perfil_e` (ADR-0067), não policy | INV-CER-PERFIL-001 |
| T-CER-026 | **conftest (instrução corrigida — único passo necessário):** adicionar a tupla `("certificados", "0007_seed_authz_certificados")` em `tests/conftest.py` `_SEED_MIGRATIONS` (lista ~linha 129). **NÃO mexer em `_APP_MODULE_SUBPATH`** — o conftest resolve via `.get(app_label, app_label)` (linha 160), então `certificados` (app NÃO-aninhado, subpath = próprio nome) já resolve por default; só apps aninhados (`padroes`/`escopos_cmc`/`procedimentos_calibracao`) precisam de entrada. A justificativa antiga "importlib falha silencioso" era falsa para app não-aninhado | critério binário: pytest enxerga o seed authz certificados pós-truncate transacional (`TestINV_CER_PERFIL_001` não falha por matriz authz vazia) | pegadinha conftest |
| T-CER-027a | `infrastructure/metrologia/certificados/{__init__.py, apps.py (label='certificados_metrologia' name='src.infrastructure.metrologia.certificados'), models.py (proxies/leitura das tabelas de reconciliação), mappers.py (`model_para_snapshot`/`snapshot_para_campos` p/ Certificado + Ponto + Analise)}` — adapter Model↔Snapshot (ADR-0007); NÃO recriar VO | testes do mapper round-trip Model↔Snapshot | repos plan §3 |
| T-CER-027b | `infrastructure/metrologia/certificados/repositories.py`: `DjangoCertificadoRepository` + `DjangoAnaliseReconciliacaoRepository` implementam os Protocols (T-CER-016); filtro `tenant_id` EXPLÍCITO além do RLS; CAS `atualizar_com_lock`; `salvar_novo` faz `bulk_create` dos N `PontoReconciliadoSnapshot` na mesma `transaction.atomic`. **Adapter da porta `U(ponto)` (T-CER-017) consulta o model `OrcamentoPorPonto` (`db_table='orcamento_por_ponto'`) no path ACHATADO `infrastructure/calibracao/`** | testes: salvar_novo atômico (cert + N pontos), CAS revision, lookup `U(ponto)` 1:1 | repos plan §3 / INV-CER-RECONCILIA-005 |
| T-CER-028 | `infrastructure/certificados/management/commands/validar_certificados.py`: drill ESTRUTURAL (introspecção PG) — tabela `certificados` + colunas aditivas + choice `substituida` presente no constraint, `ponto_reconciliado`, `analise_reconciliacao_cert`, RLS ENABLE+FORCE, triggers WORM, UNIQUEs, índices, **trigger INV-025 INTACTO (confirma `SELECT FROM certificados WHERE status='emitido'` inalterado no `0001`)**. Comportamento testado em `tests/regressao/test_inv_cer_p2_schema_triggers.py` | GATE-CER-DRILL-LOCAL (estrutural agora; PG-real comportamental = Wave A) | INV-CER-WORM-001 + INV-025 preservado |

---

## Fatia 1b-numeração — Numeração inviolável (P2, TL-03 / US-CER-003)

| ID | Tarefa | Nota | Cobre |
|----|--------|------|-------|
| T-CER-030 | Migration `infrastructure/certificados/migrations/0008_numero_seq.py`: sequence PG `certificado_numero_seq` (molde M4 `calibracao_numero_seq_global`) p/ `numero_interno` (buracos aceitos). `# metrologia-classificacao: IQ` + `# replay-fixture: none` | sequence global | INV-CER-NUM-002 |
| T-CER-031 | Tabela `numero_certificado_reservado` (`tenant`, `tipo`, `ano`, `sequencial`, `reservado_em`, `ttl_expira_em`, `confirmado` BOOL, `correlation_id`) — reserva TTL 5min do número VISÍVEL `(tenant,tipo,ano)` sequencial sem buracos; UNIQUE `(tenant, tipo, ano, sequencial)`. Migration aditiva + RLS v2 + grants | reserva atômica TTL | INV-CER-NUM-001 |
| T-CER-032 | Trigger PG virada anual + reuso-de-número: trigger valida sequência consecutiva por `(tenant,tipo,ano)`; reuso de número visível → erro PG; cancelamento de certificado PRESERVA o número (não devolve à sequência) | trigger PG | INV-CER-NUM-001 |
| T-CER-033 | `domain/metrologia/certificados/numeracao.py` + repo: `reservar_numero` (TTL) → `confirmar_numero` (transacional no mesmo `transaction.atomic` da emissão) → `liberar_expirados`. `numero_interno` (sequence, buracos OK) ≠ `numero_certificado` visível (sem buracos). Reusa VO `value_objects.NumeroCertificado` (formato verificado `<SLUG>-<YYYY>-<NNNNNN>`, regex NIT-DICLA-021) — NÃO recriar | testes: reserva→confirma→sem buraco; reserva→abort→reusa reservado | INV-CER-NUM-001/002 |
| T-CER-034 | Threaded gap-detection (job concorrência cronometrada) = **TRACK Wave A** (declarado, não implementado nesta frente) | rastreado GATE-CER-DRILL-LOCAL Wave A | diferido |

---

## Fatia 2a — Pré-condição: decisão RT por ponto (P3 — fatia própria, plan §5/Q3)

> Sub-fatiada da Fatia 2 (achado MÉDIO granularidade): `decidir_ponto_reconciliacao`
> é PRÉ-CONDIÇÃO separada da emissão (roda ANTES, ligada a `calibracao_id`), merece
> ciclo de auditores próprio.

| ID | Tarefa | Cobre |
|----|--------|-------|
| T-CER-040 | `application/metrologia/certificados/decidir_ponto_reconciliacao.py` — roda sobre a reconciliação calculada de uma calibração APROVADA, ligada a `calibracao_id`; `DecidirPontoReconciliacaoInput` (ponto, `decisao_rt`, `categoria_motivo`, justificativa) → crava `AnaliseReconciliacaoCertificado` WORM (padrão ADR-0070); idempotência própria por ponto+correlation; `EMITIR_NAO_RBC_NO_PONTO` exige `ressalva_nao_rbc` | NC-03 + C-02/C-03 + INV-CER-RESSALVA-001 |
| T-CER-040t | Testes Fatia 2a em `tests/test_m8_certificados_use_cases_p2.py`: decisão por ponto cravada WORM, idempotência por ponto, `EMITIR_NAO_RBC_NO_PONTO` sem ressalva → bloqueia, `categoria_motivo` coerente com classificação | `pytest tests/test_m8_certificados_use_cases_p2.py -k decidir_ponto --no-cov --reuse-db` verde | gate fatia 2a |

---

## Fatia 2b — Emissão + reemissão + REST + eventos WORM (P3+P4)

| ID | Tarefa | Cobre |
|----|--------|-------|
| T-CER-041 | `application/metrologia/certificados/emitir_certificado.py` — use case **ATÔMICO fail-closed (US-CER-001), caminho completo:** consome APROVADA (evento `calibracao.aprovada`); **lê da calibração APROVADA real** `grandeza_calibrada` + `faixa_calibrada_declarada` (ADR-0076 — fail-closed se ausente: `FAIXA_DECLARADA_AUSENTE`); reconcilia ponto-a-ponto (`reconciliar_pontos` + porta `U(ponto)` lookup + porta `cmc_para`); valida completude decisões RT; ponto não-RBC sem decisão (perfil A) → **422 `RECONCILIACAO_PENDENTE_DECISAO_RT` SEM persistir nada**. **Duas travas CGCRE distintas, fronteira documentada (resolve achado ALTO NC-09/AC-CER-001-4 SEM contradizer o plan):** (1) **vencimento da acreditação inteira** — perfil A tentando emitir RBC com `acreditacao_vigencia_fim < data_de_emissao` → conforme a regra DECIDIDA no plan §4 (INV-CER-CGCRE-VIG-001, C-06): os pontos são rebaixados a não-RBC exigindo decisão RT (NÃO há 409 hard-block; a divergência com AC-CER-001-4 é reconciliada na emenda PRD T-CER-070, alinhando o AC ao comportamento decidido); (2) **suspensão** (perfil A suspenso) → mesmo rebaixamento. Só classifica `RBC_OK` quando perfil A **ativo E não-suspenso E `acreditacao_vigencia_fim > data_de_emissao`** (data de emissão, não `today`) | INV-CER-EMISSAO-001 + INV-CER-CGCRE-VIG-001 + INV-CER-RECONCILIA-001/002 |
| T-CER-042 | `emitir_certificado` (cont. — persistência atômica): numera (`reservar`→`confirmar`), perfil server-side via `tenant_perfil_e` (NUNCA body — ADR-0067), crava `CertificadoSnapshot` + N `PontoReconciliadoSnapshot` + `reconciliacao_hash` + numeração numa **única `transaction.atomic`** com advisory lock por `(tenant, calibracao_id)`; `status='emitido'` (contrato trigger ADR-0078); congela `regra_decisao_snapshot` (NC-04) + **`snapshot_padroes_usados_json` com a vigência da calibração de cada padrão usado (NC-07); perfil A bloqueia emissão (`PADRAO_CALIBRACAO_VENCIDA`) se algum padrão estava com calibração vencida na `data_de_emissao` (cl. 6.5)** | INV-CER-PERFIL-001 + INV-CER-SNAPSHOT-PERFIL-001 + INV-CER-REGRA-DEC-001 + INV-CER-NUM-001 + INV-CER-PADRAO-VIG-001 |
| T-CER-043 | `application/metrologia/certificados/reemitir_certificado.py` (US-CER-004): nova `v(N+1)` linkada a `v(N)` via `versao_anterior_id`; motivo ≥50 chars; `v(N)` → `SUBSTITUIDA` (one-shot CAS — depende da choice `substituida` cravada em T-CER-020); herda `snapshot_equipamento_json` + `snapshot_padroes_usados_json` (paridade cert com equipamento baixado — US-CER-013); reconcilia de novo se aplicável | INV-CER-WORM-001 + US-CER-004/013 |
| T-CER-044 | `infrastructure/metrologia/certificados/serializers.py`: `EmitirCertificadoSerializer`, `DecidirPontoSerializer` (`categoria_motivo` + justificativa), `ReemitirCertificadoSerializer` (motivo min 50) **+ `CertificadoLeituraSerializer` (retrieve — resolve achado CRÍTICO INV-CER-SNAPSHOT-CMC-001):** serializa `CertificadoSnapshot` + N `PontoReconciliadoSnapshot` (incl. `cmc_no_ponto`, `classificacao`, `ressalva_nao_rbc`, `tipo_acreditacao`, `faixa_certificado_min/max`) lendo APENAS os campos PERSISTIDOS — NUNCA invoca `cmc_para`/`tenant_perfil_e` no read-path. Perfil/tipo_acreditacao NÃO vêm do body (ADR-0067); rótulos PT ("Certificado de calibração", "Número", "Faixa calibrada") | INV-CER-PERFIL-001 + INV-CER-SNAPSHOT-CMC-001 |
| T-CER-045 | `infrastructure/metrologia/certificados/views.py` `CertificadoViewSet`: `ACTION_MAP` (`certificados.{ver/emitir/reemitir/decidir_ponto/revogar}`) + `get_authz_action`/`get_authz_resource`; `@action` emitir/reemitir/decidir_ponto/revogar (POST); **`retrieve`/`listar` (read-path — resolve achado CRÍTICO): devolve o `CertificadoLeituraSerializer` (T-CER-044) lendo SOMENTE do snapshot persistido (`ponto_reconciliado` + colunas de `certificados`), SEM chamar `cmc_para`/`tenant_perfil_e`** (é exatamente o código que o hook T-CER-054 e o teste T-CER-052 protegem). Tenant via `active_tenant_context` (nunca body) | RBC RequireAuthz + INV-CER-SNAPSHOT-CMC-001 |
| T-CER-046 | Views: idempotência IDEMP-001 (header `Idempotency-Key` via `avaliar_chave_idempotencia` → NovoProcessamento/Replay/ErroValidacao); advisory lock superseção (`pg_advisory_xact_lock`); sha256/hashes server-side (não confiar cliente) | IDEMP-001 |
| T-CER-047 | Views `_publicar_evento_cert`: emite **`Certificados.CertificadoReconciliado`** na auditoria central WORM (NÃO `CertificadoEmitido` — normativo cl. 7.8, dispara na assinatura A3 Wave A). Snapshot `perfil_no_evento` (ADR-0067). `status='emitido'` interno = emissão metrológica, não distribuível até A3 | decisão cravada plan §6 / NC-08 |
| T-CER-048 | `infrastructure/metrologia/certificados/urls.py`: `DefaultRouter` registra `CertificadoViewSet` + **plug em `config/urls.py` raiz** (lição T-CAL-124 — não deixar órfã) | infra |
| T-CER-049 | Testes Fatia 2b em `tests/test_m8_certificados_use_cases_p2.py` + `tests/test_m8_certificados_api_p2.py` (`--no-cov --reuse-db`): emissão atômica feliz (perfil A com decisões completas → cert + N pontos + hash), 422 sem decisão RT (perfil A) sem persistir, B/C/D ressalva, reemissão versionada (`v(N)→substituida`), idempotência replay, evento `CertificadoReconciliado` emitido, **read-path retrieve devolve `cmc_no_ponto`/`classificacao`/`ressalva` do snapshot (CRÍTICO)**, **padrão com calibração vencida → perfil A bloqueia `PADRAO_CALIBRACAO_VENCIDA` (NC-07)**, **`U==CMC` seta `u_igual_cmc_suspeita` (NC-06)**, **US-CER-013: emitir cert → marcar equipamento BAIXADO → cert permanece consultável com `snapshot_equipamento_json` intacto e FK PROTECT impedindo perda de referência (cl. 8.4)**, **leitura efetiva de `grandeza_calibrada`+`faixa_calibrada_declarada` a partir da calibração APROVADA real (não só Fake) — fail-closed `FAIXA_DECLARADA_AUSENTE` quando ausente (GATE-CAL-EMISSAO-RECONCILIA-FAIXA fecha com dado de origem real)**. **Reverde suíte M4 chave (629) zero regressão** | gate fatia 2b |

---

## Fatia 3 — Fechamento (INV-CER em REGRAS + testes nomeados + hooks + matriz — P5)

| ID | Tarefa | Cobre |
|----|--------|-------|
| T-CER-050 | Cravar a **família INV-CER (16 invariantes nomeados)** em `REGRAS-INEGOCIAVEIS.md` (nomes idênticos ao plan §4, SEM forma numérica `001..015`): **INV-CER-EMISSAO-001, INV-CER-RECONCILIA-001, INV-CER-RECONCILIA-002, INV-CER-RECONCILIA-003, INV-CER-RECONCILIA-004, INV-CER-RECONCILIA-005, INV-CER-NUM-001, INV-CER-NUM-002, INV-CER-PERFIL-001, INV-CER-SNAPSHOT-PERFIL-001, INV-CER-SNAPSHOT-CMC-001, INV-CER-REGRA-DEC-001, INV-CER-WORM-001, INV-CER-CGCRE-VIG-001, INV-CER-RESSALVA-001, INV-CER-PADRAO-VIG-001** (a 16ª promove NC-07 — vigência da calibração dos padrões usados, cl. 6.5; texto exato no plan §4 + esta task) | toda INV-CER plan §4 + NC-07 promovida |
| T-CER-051 | `tests/regressao/test_inv_cer_classes_nomeadas.py`: 1 classe por INV, citando o ID (TST-004): `TestINV_CER_EMISSAO_001`, `TestINV_CER_RECONCILIA_001..005`, `TestINV_CER_NUM_001/002`, `TestINV_CER_PERFIL_001`, `TestINV_CER_SNAPSHOT_PERFIL_001`, `TestINV_CER_SNAPSHOT_CMC_001`, `TestINV_CER_REGRA_DEC_001`, `TestINV_CER_WORM_001`, `TestINV_CER_CGCRE_VIG_001`, `TestINV_CER_RESSALVA_001`, **`TestINV_CER_PADRAO_VIG_001`** — cada classe exercita a BARREIRA REAL (PG onde trigger/constraint; puro/Fake onde domínio). **`TestINV_CER_WORM_001` inclui caso TL-05:** valida o predicado `tem_emitido` explícito `.filter(status='emitido', revogado_em__isnull=True)` distinguindo cert emitido-vigente de emitido-revogado (não confiar só no manager default que pode mascarar revogados) | TST-004 / sentinela 16:16 |
| T-CER-052 | **Teste anti-reconsulta (TL-04 / INV-CER-SNAPSHOT-CMC-001):** mock que FALHA se o read-path do certificado emitido (retrieve T-CER-045) invocar `cmc_para` ou `tenant_perfil_e`. Drill: emitir → revisar escopo-cmc (muda CMC vigente) → reler cert via retrieve → `cmc_no_ponto` exibido é o do SNAPSHOT, não o novo vigente (WORM furado por LEITURA seria bug) | INV-CER-SNAPSHOT-CMC-001 |
| T-CER-053 | Hook `cert-reconcilia-fail-closed.sh`: bloqueia `reconciliar_pontos`/`emitir_certificado` sem fail-closed em `ORCAMENTO_PONTO_AMBIGUO`/`SEM_ORCAMENTO`/`SEM_CMC`/`FAIXA_DECLARADA_AUSENTE` (override motivo ≥10 chars; filtro paths sensíveis) | INV-CER-RECONCILIA-002/005 |
| T-CER-054 | Hook `cert-snapshot-nao-reconsulta.sh`: bloqueia read-path do cert emitido (serializer/view de retrieve) que importe/chame `cmc_para`/`tenant_perfil_e` (TL-04) | INV-CER-SNAPSHOT-CMC-001 |
| T-CER-055 | Hook `cert-perfil-rbc-so-A.sh`: bloqueia `tipo_acreditacao=RBC` derivado do body/payload (deve vir server-side de `tenant_perfil_e` perfil A; defesa L6 invertido) | INV-CER-PERFIL-001 + INV-CER-RESSALVA-001 / ADR-0075 |
| T-CER-056 | Casos no `_test-runner.sh` (seção M8) p/ os 3 hooks, **contagem cravada (achado BAIXO):** `cert-reconcilia-fail-closed` = 6 casos `CRFC1..6`; `cert-snapshot-nao-reconsulta` = 5 casos `CSNR1..5`; `cert-perfil-rbc-so-A` = 6 casos `CPRA1..6` = **17 casos novos**. Total esperado do `_test-runner` = **491 + 17 = 508** (critério binário). Rodar SEM FILTRO antes de commit. Sentinela CI: 3 hooks ↔ 17 casos ↔ 16 INV-CER ↔ 16 classes Test | sentinela anti-drift |
| T-CER-057 | **Reverde global zero regressão:** M6 (`validar_escopos_cmc` 17/17 + `test_inv_ecmc_*`), M7 (`test_inv_proc_*` + drill), M4 chave (629), SAN-INCERTEZA-PONTO (replay+drill). `makemigrations --check` limpo; `ruff check`+`mypy` dos arquivos tocados; drill `validar_certificados` estrutural | gate fatia 3 |
| T-CER-058 | `docs/faseamento/M8-certificados/matriz-reconciliacao.md` (molde M7, 8 seções): (1) US↔AC↔INV↔ADR↔Hook↔código; (2) **família INV-CER nominal (16 invariantes — EMISSAO-001, RECONCILIA-001..005, NUM-001/002, PERFIL-001, SNAPSHOT-PERFIL-001, SNAPSHOT-CMC-001, REGRA-DEC-001, WORM-001, CGCRE-VIG-001, RESSALVA-001, PADRAO-VIG-001)** ↔ teste nomeado ↔ enforcement; (3) hooks + 17 casos; (4) entregas Fatia 0-P9; (5) GATEs (fechados/diferidos); (6) pendências não-bloqueantes; (7) veredito; (8) P9 ritual | reconciliação |

---

## P8 / P9 — Fechamento de marco (após Fatia 3)

| ID | Tarefa |
|----|--------|
| T-CER-070 | **Emendar PRD/spec `certificados` — itens binários (lista fechada, não "se necessário"):** (a) **corrigir `spec.md` linha 84 (US-CER-001):** trocar evento `Certificados.CertificadoEmitido` → `Certificados.CertificadoReconciliado`, mantendo nota de que `CertificadoEmitido` normativo cl. 7.8 dispara só na A3 Wave A — critério: `grep CertificadoEmitido` em `spec.md`/PRD retorna SÓ ocorrências marcadas como Wave A/normativo (NC-08); (b) **AC-CER-001-1** publica `Certificados.CertificadoReconciliado` na emissão metrológica; (c) **AC-CER-001-4** emendado para refletir o comportamento DECIDIDO no plan §4 (INV-CER-CGCRE-VIG-001/C-06): perfil A com acreditação vencida/suspensa → pontos rebaixados a não-RBC exigindo decisão RT (NÃO 409 hard-block), documentando a fronteira; (d) **AC-CER-001/003/004/013** fiéis ao código (emissão lógica + reconciliação ponto-a-ponto + numeração dual + paridade snapshot pós-baixa US-CER-013); nota terminológica `status='emitido'` interno ≠ entrega normativa cl. 7.8 (A3 Wave A). Verificar matriz-feature-perfil (RBC só perfil A) |
| T-CER-071 | Promover **ADR-0078 a aceito** (migration aditiva concretizou o contrato trigger INV-025) na tabela §11 do AGENTS.md; ADR-0077 já implementada; referenciar 0076/0074/0073/0067 |
| T-CER-080 | Ritual auditores roteados (INV-RITUAL-003): **segurança** (porta fail-closed + RLS + perfil server-side + anti-reconsulta read-path), **llm-correctness** (não aplicável/baixo), **produto** (AC + terminologia RBC/não-RBC + ressalva + evento corrigido na spec), **qualidade** (16 INV testados + reverde), **observabilidade** (evento `CertificadoReconciliado` + WORM), **idempotência** (IDEMP-001 emitir/decidir). MÉDIO+ bloqueia fechamento (`ritual-gate-check.sh`) |

---

## GATEs

**Fechados por esta frente:**
- **GATE-CAL-EMISSAO-RECONCILIA-FAIXA** (T-CER-041/042/049 — reconciliação `pontos ⊆ declarada` + faixa do certificado dos pontos válidos, com leitura efetiva de `faixa_calibrada_declarada` da calibração APROVADA real e fail-closed quando ausente / ADR-0076).
- **GATE-ECMC-U-MAIOR-CMC** (T-CER-004/001/041 — porta `cmc_para` injetada + `U(ponto) ≥ CMC(ponto)` via `avaliar_u_cmc` / ADR-0074 cond. 2 / INV-ECMC-009).

**Rastreados / diferidos Wave A (declarados, NÃO bloqueiam esta frente):**
- GATE-CER-PDF (motor PDF/A-3 ISO 19005-3 + templates Jinja2 — US-CER-010/017).
- GATE-CER-A3 (assinatura Lacuna — US-CER-002 / ADR-0009/0048).
- GATE-CER-OCSP (revogação online — ADR-0046).
- GATE-CER-TSA (carimbo TSA-ITI PAdES-LTV — ADR-0047).
- GATE-CER-PORTAL (portal do cliente — US-CER-006).
- GATE-CER-QR (QR público — US-CER-009).
- GATE-CER-EMAIL (EmailTemplateProvider — ADR-0060 / US-CER-005).
- GATE-CER-EXPORT (export ANVISA/regulatório — US-CER-016/017).
- GATE-CER-POSEMISSAO (recall/suspensão/errata — US-CER-018/019/020).
- **GATE-CER-DRILL-LOCAL** (drills comportamentais PG-real: imutabilidade cruzada equipamento INV-025, numeração sem buraco threaded T-CER-034, anti-reconsulta) — estrutural agora (T-CER-028/052), comportamental PG-real = Wave A.

---

## Verificação por fatia (proporcional — espelha M7; paths reais executáveis)

- **Fatia 0:** `pytest tests/test_m8_certificados_reconciliacao_p0.py --no-cov` + reverde M6+M7 (`pytest tests/test_m6_escopos_cmc_cobertura_p1.py tests/test_m7_faixa_cobertura.py tests/regressao/test_inv_ecmc_classes_nomeadas.py tests/regressao/test_inv_proc_classes_nomeadas.py --no-cov`) idênticos + `validar_escopos_cmc` 17/17. Commit isolado.
- **Fatia 1a:** `pytest tests/test_m8_certificados_dominio_p1.py --no-cov` (puro, sem Docker/PG) + `ruff`/`mypy` dos arquivos novos em `src/domain/metrologia/certificados/`. Zero import Django.
- **Fatia 1b-schema:** `manage.py makemigrations --check` limpo; `migrate --database=migrator`; `_test-runner.sh` (migration-rls-check + migration-metrology-classifier + audit-immutability verdes); drill `validar_certificados` estrutural; `pytest tests/regressao/test_inv_cer_p2_schema_triggers.py --no-cov --reuse-db` (RLS+WORM+INV-025 intacto + choice `substituida` presente).
- **Fatia 1b-numeração:** testes reserva→confirma→sem-buraco + reserva→abort→reusa; `makemigrations --check`.
- **Fatia 2a:** `pytest tests/test_m8_certificados_use_cases_p2.py -k decidir_ponto --no-cov --reuse-db`.
- **Fatia 2b:** `pytest tests/test_m8_certificados_use_cases_p2.py tests/test_m8_certificados_api_p2.py --no-cov --reuse-db`; reverde M4 chave 629; idempotência + evento + read-path retrieve + NC-07 + US-CER-013.
- **Fatia 3:** `_test-runner.sh` SEM FILTRO (508 casos = 491 + 17) verde; `pytest tests/regressao/test_inv_cer_classes_nomeadas.py --no-cov --reuse-db` (16 classes); teste anti-reconsulta; reverde global M4/M6/M7/SAN-INCERTEZA-PONTO; `makemigrations --check`; drill.

---

## Pendências escaladas a humano credenciado (NÃO bloqueiam a frente)

| Pendência | Quando | Quem |
|-----------|--------|------|
| Homologação cl. 7.11 do motor de incerteza por ponto (replay/determinismo do cálculo) | pré-produção | consultor/RT RBC credenciado (`project_sem_contratacoes_externas_ate_producao`) |
| Dossiê RBC da reconciliação (partição rbc/não-rbc + decisões RT) p/ CGCRE | pré-produção / auditoria CGCRE | RT credenciado |
| Validação de método (proc não-normalizado) e parecer de exclusão de ponto por classe específica | pré-produção | RT credenciado |

> Estas pendências são de **revisão/assinatura humana legal** — a frente entrega toda a
> lógica + snapshots probatórios + trilha WORM que as suportam.

---

## Veredito

Tasks **`ready-for-implement`**. 60 tasks `T-CER-001..T-CER-080` em 8 blocos (Fatia 0 →
1a → 1b-schema → 1b-numeração → 2a-decisão-RT → 2b-emissão+REST → 3 → P8/P9),
respeitando a ordem do plan §5 e o path híbrido ADR-0078 (tabela `certificados`
achatada NÃO-aninhada; lógica em `metrologia/certificados/` aninhado). Toda a família
**INV-CER (16 invariantes nominais)** do plan §4 + NC-07 promovida tem (a) task que a
implementa e (b) task na Fatia 3 que a crava em REGRAS + `TestINV_CER` nomeado.
GATE-CAL-EMISSAO-RECONCILIA-FAIXA + GATE-ECMC-U-MAIOR-CMC fecham nesta frente de forma
verificável (porta `cmc_para` injetada + leitura real da faixa declarada);
PDF/A3/OCSP/TSA/portal/QR/email/export/pós-emissão + drill PG-real comportamental ficam
rastreados Wave A. Item #0 (ADR-0077) FECHADO. O read-path de leitura do certificado
emitido (retrieve, T-CER-044/045) lê SÓ do snapshot persistido — protegido por hook
(T-CER-054) E teste anti-reconsulta (T-CER-052). A choice `substituida` é cravada na
migration aditiva da Fatia 1b (T-CER-020) ANTES da Fatia 2 consumi-la (reemissão).

**Próximo passo:** `/implement` começando por **Fatia 0** (reconciliação pura + porta
`cmc_para` + reverde M6/M7) → Fatia 1a (domínio puro, sem Docker/PG). Commits atômicos
por task/grupo.