---
owner: agente-ia
revisado-em: 2026-05-31
proximo-review: 2026-08-31
status: ready-for-tasks
diataxis: reference
audiencia: [agente, auditor, tech-lead, consultor-rbc]
marco: M8-certificados
tipo: plan-faseamento
relacionados:
  - docs/faseamento/M8-certificados/spec.md
  - docs/faseamento/M8-certificados/reviews-consolidado.md
  - docs/faseamento/M8-certificados/T-CER-000-investigacao.md
  - docs/adr/0077-orcamento-incerteza-por-ponto-calibracao.md
  - docs/adr/0078-certificados-tabela-achatada-logica-aninhada.md
  - docs/adr/0076-fonte-faixa-cobertura-declarada-config-vs-pontos-emissao.md
  - docs/adr/0074-cobertura-rbc-tridimensional-faixa-u-maior-cmc.md
---

# Plan — M8 `metrologia/certificados` (núcleo metrológico de emissão)

> Traduz a `spec.md` (draft) + `reviews-consolidado.md` (ambas APROVA COM CORREÇÕES)
> em fatias executáveis + INV-CER numeradas + sequência de tasks. Ritual: spec →
> revisões → **plan (este)** → revisão `tech-lead`+`consultor-rbc` do plan → tasks →
> implement → P9. Todas as decisões de produto/metrologia já cravadas (não reabrir).

## 0. Item #0 — pré-requisito FECHADO

**ADR-0077 (frente SAN-INCERTEZA-PONTO) IMPLEMENTADA** (2026-05-31). O orçamento de
incerteza agora é **por ponto**: `OrcamentoPorPonto` populado pelo use case
`calcular_orcamento_incerteza` (caminho por-ponto), com `U_expandida_no_ponto`,
`k_no_ponto`, `nivel_confianca_no_ponto`, `grau_liberdade_efetivo_no_ponto`,
`metodo_tipo_a_ponto`, `s_tipo_a_no_ponto` por ponto + `cadeia_pontos_hash`. **Isto
destrava a Fatia 2** (NC-01 CRÍTICO resolvido). A porta de leitura `U(ponto)` que a
reconciliação consome = `OrcamentoPorPonto.U_expandida_no_ponto` (read-model por
`ponto_calibracao`).

> **Consequência para o plano:** a reconciliação ponto-a-ponto NÃO deriva U; lê o
> `OrcamentoPorPonto` já persistido (1:N do `OrcamentoIncerteza` da calibração).
> O agregado `OrcamentoIncerteza.U_expandida` é pior-caso (não-normativo) — NÃO usar
> para conformidade de ponto (INV-CAL-INC-005).

## 1. ADRs desta frente

- **ADR-0077** — ✅ aceito/implementado (item #0).
- **ADR-0078** — certificados: tabela achatada (contrato trigger INV-025 lê
  `status='emitido'` literal) + lógica de reconciliação aninhada. **A promover a
  aceito no fechamento da Fatia 1b** (quando a migration aditiva concretizar o
  contrato). Até lá: proposta, guia o schema.
  - **Path cravado (revisão tech-lead 2026-05-31):** a **tabela/model `Certificado`
    permanece em `infrastructure/certificados/` (NÃO-aninhado)** — o trigger cross-app
    `equipamento_imutabilidade_pos_cert_check` (migration `certificados/0001` linhas
    73-78) faz `SELECT ... FROM certificados WHERE status='emitido'` com nome de tabela
    + literal hard-coded; mover `db_table`/app/valor quebra INV-025 silenciosamente +
    desalinha o hook `equipamento-imutabilidade-check.sh` (allowlista o path). Migration
    **estritamente aditiva** (`ADD COLUMN`), nunca renomear/dropar. **Toda a lógica nova**
    (reconciliação, use cases, mappers) vai em `domain/metrologia/certificados/` +
    `infrastructure/metrologia/certificados/` (ADR-0072). `objects` default já é o
    `CertificadoVigentesManager` filtrado — TL-05 atendido pelo stub.

## 2. Algoritmo de reconciliação (o coração — puro, Fatia 0/1a)

Entrada: calibração `APROVADA` + seus `LeituraSnapshot` (pontos medidos) +
`OrcamentoPorPonto[]` + `grandeza_calibrada`+`faixa_calibrada_declarada` (ADR-0076) +
perfil do tenant + (RBC) porta `cmc_para`.

Para cada **ponto distinto** medido (agrupa `LeituraSnapshot` por `ponto_calibracao`):

1. **Contenção declarada (NC-02 / INV-CER-RECONCILIA-001):**
   `ponto ∈ faixa_calibrada_declarada`? (`FaixaMedicao.contem`). Fora → ponto
   classificado `FORA_DECLARADA` (furo de processo — CGCRE não extrapola).
2. **U do ponto (lookup 1:1, NUNCA agregação — C-01/INV-CER-RECONCILIA-005):** lê
   `OrcamentoPorPonto[ponto].U_expandida_no_ponto` (+k+nível+ν_eff — NC-05) por lookup
   ÚNICO. A U do ponto JÁ agrega as N repetições via Tipo A (`s/√n`) — NÃO somar U por
   repetição (dupla contagem). `OrcamentoPorPonto` duplicado para o mesmo ponto →
   `ORCAMENTO_PONTO_AMBIGUO` fail-closed. Ausente → `SEM_ORCAMENTO` (pré-condição).
3. **(RBC perfil A) U≥CMC (INV-CER-RECONCILIA-002 / ADR-0074 cond.2 / INV-ECMC-009):**
   `cmc = cmc_para(tenant, grandeza, ponto, data_emissao)`. `None` → `SEM_CMC` (fora
   do escopo). `U(ponto) ≥ cmc` → `RBC_OK`; senão `U_MENOR_CMC` (bug de orçamento OU
   exclusão legítima — RT decide, NC-03).
4. **Partição (NC-03):** `pontos_rbc` (RBC_OK) vs `pontos_nao_rbc` (qualquer falha).
   Um ponto problemático **NÃO bloqueia o certificado inteiro**; vira decisão.
5. **Decisão do RT (NC-03, padrão ADR-0070 WORM):** pontos não-RBC exigem
   `AnaliseReconciliacaoCertificado` (registro WORM congelado: ponto, motivo,
   `decisao_rt ∈ {EXCLUIR_PONTO, EMITIR_NAO_RBC_NO_PONTO, ABORTAR}`, justificativa
   hash, A3 diferida Wave A). Perfil A sem decisão para ponto problemático → bloqueia
   (422 `RECONCILIACAO_PENDENTE_DECISAO_RT`). B/C/D → ressalva registrada.
6. **`faixa_certificado` (NC-02 / INV-CER-RECONCILIA-003):** `[min,max]` dos pontos
   **válidos** (não excluídos) — METADADO rotulado "faixa calibrada", NÃO implica
   continuidade. Os pontos discretos válidos são a verdade reportada.

**Classificação determinística por precedência (C-04 / cl. 7.11 replay):** um ponto pode
falhar em >1 critério; a classe é resolvida por precedência fixa
`FORA_DECLARADA > SEM_CMC > U_MENOR_CMC > RBC_OK` — sem isso dois certificados da mesma
calibração classificariam o mesmo ponto diferente (NC de replay).

**`reconciliacao_hash` (fecho WORM — C-05 ordenação + payload ampliado tech-lead):**
encadeia os `PontoReconciliadoSnapshot` ordenados por `ponto_calibracao` ASC (ordenação
canônica determinística antes do hash E do cálculo de `faixa_certificado` —
INV-CER-RECONCILIA-004). O payload congela por ponto `{ponto, valor_reportado, U, k,
nivel_confianca, ν_eff, classificacao, incluido_no_certificado, cmc_no_ponto}` + cabeçalho
`{versao_reconciliacao, faixa_certificado_min/max, tipo_acreditacao}` — certifica a DECISÃO
de reconciliação (partição + exclusões RT), não só os números upstream. Reusa
`canonicalizar_payload_para_hmac` + `formatar_hash_versionado` (Decimal→str/UUID→str antes).

Saída: `ReconciliacaoCertificado` (VO puro) = lista de `PontoReconciliado` +
partição + `faixa_certificado` + flag global `pode_emitir_rbc`.

**Fatia 0** centraliza a geometria `pontos ⊆ declarada` reusando
`domain/metrologia/faixa_cobertura.py` (M7 Fatia 0) + `avaliar_u_cmc` (M6) — sem
reimplementar; só compõe.

## 3. Entidades (Fatia 1a — domínio puro)

- **`CertificadoSnapshot`** (WORM) — id, tenant, calibracao_id, equipamento_id,
  `numero_interno` (sequence), `numero_certificado` (VO visível), `versao` (reemissão),
  `versao_anterior_id` (NULL p/ v1), `status` (`'emitido'` na emissão lógica —
  ADR-0078 contrato trigger), `perfil_emissor_no_momento CHAR(1)` (INV-CER-SNAPSHOT-PERFIL-001),
  `faixa_certificado_min/max`, `tipo_acreditacao` (RBC/NAO_RBC), snapshots congelados
  (`snapshot_equipamento_json`, cliente ref hash, `regra_decisao_snapshot` NC-04),
  `reconciliacao_hash` (fecho WORM da tabela ponto-a-ponto), `emitido_em`, `correlation_id`.
- **`PontoReconciliadoSnapshot`** (1:N, WORM) — certificado_id, `ponto_calibracao`,
  `valor_reportado`, `U_no_ponto`, `k_no_ponto`, `nivel_confianca_no_ponto`,
  `grau_liberdade_efetivo_no_ponto` (NC-05), `cmc_no_ponto` (NULL não-RBC),
  `classificacao` (`RBC_OK`/`FORA_DECLARADA`/`U_MENOR_CMC`/`SEM_CMC`/`EXCLUIDO`),
  `u_igual_cmc_suspeita BOOL` (NC-06 flag P2), `incluido_no_certificado BOOL`,
  **`ressalva_nao_rbc TEXT` (C-03 / cl. 8.1.3 / ADR-0075):** quando
  `EMITIR_NAO_RBC_NO_PONTO`, texto obrigatório "ponto não coberto pela acreditação RBC"
  cravado no snapshot — impede o documento (Wave A) exibir ponto não-RBC como RBC
  (uso indevido de acreditação / L6 invertido).
- **`AnaliseReconciliacaoCertificado`** (WORM, NC-03 / padrão ADR-0070) — decisão RT
  por ponto problemático: `decisao_rt ∈ {EXCLUIR_PONTO, EMITIR_NAO_RBC_NO_PONTO, ABORTAR}`
  + **`categoria_motivo` enum (C-02 / cl. 7.10.1):**
  `{PADRAO_FORA_VALIDADE, FALHA_REPETIBILIDADE, U_MAIOR_QUE_CMC_BUG,
  PONTO_FORA_FAIXA_DECLARADA, CONDICAO_AMBIENTAL_NC, OUTRO}` + justificativa
  canonicalizada + hash (A3 diferida Wave A). Ligada a `calibracao_id` (ver máquina de
  estados abaixo), não a `certificado_id` (existe ANTES da emissão).
- **Reusados sem recriar:** `EscopoUsado`/`ProcedimentoUsado` (já snapshots da
  configuração); `OrcamentoPorPonto` (read-model U por ponto).
- **Enums:** `EstadoCertificado` (`RASCUNHO`/`EMITIDO`/`SUBSTITUIDA`/`REVOGADO` —
  estende stub), `ClassificacaoPonto`, `DecisaoReconciliacaoRT`, `CategoriaMotivoExclusao`.
- **Repository Protocol** + reconciliação pura.

### Máquina de estados + materialização (decisão tech-lead 2026-05-31 — achado ALTO)

`RASCUNHO --emitir_certificado(reconciliação completa)--> EMITIDO --reemitir--> SUBSTITUIDA;
EMITIDO --revogar--> REVOGADO`. **`RASCUNHO` permanece declarado (compat stub) mas NÃO é
materializado em produção nesta frente:** a reconciliação calculada + as
`AnaliseReconciliacaoCertificado` penduram em `calibracao_id` (entidades de reconciliação
independentes), SEM linha em `certificados` até `emitir`. Assim `certificados` contém
APENAS snapshots imutáveis `status='emitido'` (WORM puro, sem rascunho órfão), e o trigger
INV-025 (filtra `status='emitido'` — linha 76) é inócuo para a reconciliação pendente.
**`emitir_certificado` é atômico e fail-closed:** só transiciona `→ emitido` (cravando
`CertificadoSnapshot` + N `PontoReconciliadoSnapshot` + `reconciliacao_hash` + numeração
numa única transação) quando NÃO há ponto não-RBC sem decisão RT (perfil A); senão 422
`RECONCILIACAO_PENDENTE_DECISAO_RT` sem persistir nada.

## 4. INV-CER definitivas (a cravar em REGRAS — Fatia 3)

| ID | Regra | Perfil |
|----|-------|--------|
| INV-CER-EMISSAO-001 | só calibração `APROVADA` (2ª conferência) emite; senão 422 `CALIBRACAO_NAO_APROVADA` | Absoluta A; config B/C/D |
| INV-CER-RECONCILIA-001 | `∀ ponto ∈ leituras incluídas: ponto ∈ faixa_calibrada_declarada` (CGCRE não extrapola) | Absoluta A |
| INV-CER-RECONCILIA-002 | RBC: `U(ponto) ≥ CMC(ponto)` via `cmc_para` (ADR-0074 c.2); `U<CMC` sem decisão RT → bloqueia (fecha GATE-ECMC-U-MAIOR-CMC) | Absoluta A |
| INV-CER-RECONCILIA-003 | `faixa_certificado=[min,max]` dos pontos VÁLIDOS (metadado), pontos discretos = verdade; imutável no snapshot | Absoluta A |
| INV-CER-RECONCILIA-004 | pontos ordenados canonicamente por `ponto_calibracao` ASC antes de `reconciliacao_hash` E `faixa_certificado` (C-05 — replay cl. 7.11 / INV-DOC-CANON-001) | Absoluta |
| INV-CER-RECONCILIA-005 | `OrcamentoPorPonto` é 1:1 com `ponto_calibracao` na calibração; reconciliação resolve `U(ponto)` por lookup único (não agregação); duplicidade → `ORCAMENTO_PONTO_AMBIGUO` fail-closed (C-01) | Absoluta A |
| INV-CER-NUM-001 | numeração `(tenant,tipo,ano)` sequencial, reserva TTL 5min, virada anual; cancelamento preserva número; reuso → erro PG | Absoluta |
| INV-CER-NUM-002 | `numero_interno` (sequence, buracos OK) ≠ `numero_certificado` visível (sem buracos) | Absoluta |
| INV-CER-PERFIL-001 | campos MATCH `Tenant.perfil_regulatorio` vigente; RBC em perfil≠A → 403 (defesa L6) | Absoluta |
| INV-CER-SNAPSHOT-PERFIL-001 | `perfil_emissor_no_momento CHAR(1) NOT NULL` no INSERT, imutável (ADR-0067) | Absoluta |
| INV-CER-SNAPSHOT-CMC-001 | read-path do cert emitido NUNCA reconsulta `cmc_para`/`tenant_perfil_e`; lê snapshots (TL-04 — WORM furado por LEITURA) | Absoluta |
| INV-CER-REGRA-DEC-001 | congela `regra_decisao_snapshot` (cl. 7.8.6/ADR-0024) quando aplicável (NC-04) | Absoluta A |
| INV-CER-WORM-001 | cert emitido imutável; correção só via reemissão versionada (US-CER-004); DELETE bloqueado por trigger | Absoluta |
| INV-CER-CGCRE-VIG-001 | só classifica `RBC_OK` quando perfil A **ativo E não-suspenso** E `acreditacao_vigencia_fim >= data_de_emissao` (C-06 — cobre suspensão ≠ vencimento; vigência **inclusiva do último dia** e suspensão avaliada por janela `[em,ate]` NA data de emissão, não `today` — parecer consultor-rbc 2026-06-01); `acreditacao_vigencia_fim is None` é **fail-open lazy** (GATE-CER-CGCRE-VIG-DATA-POPULAR); senão pontos → não-RBC (decisão RT) | Absoluta A |
| INV-CER-RESSALVA-001 | ponto `EMITIR_NAO_RBC_NO_PONTO` carrega `ressalva_nao_rbc` obrigatória no snapshot (C-03 — anti uso indevido de acreditação cl. 8.1.3 / ADR-0075) | Absoluta A |
| INV-CER-PADRAO-VIG-001 | (NC-07, cl. 6.5) perfil A bloqueia emissão se algum padrão usado tinha a calibração **vencida** na data de emissão (`calibracao_padrao_vigencia_fim < data_de_emissao` → `PADRAO_CALIBRACAO_VENCIDA`); vigência ausente/malformada no snapshot é **fail-open lazy** (GATE-CER-PADRAO-VIG-SNAPSHOT até o wiring com M5 `padroes`) | Absoluta A |

Reusadas: INV-CAL-WORM-001, INV-CAL-INC-005, INV-ECMC-008/009, INV-VIG-*, INV-SOFT-*,
INV-TENANT-*, INV-TENANT-PERFIL-001/003/004, INV-DOC-CANON-001, INV-HMAC-001..005.

## 5. Fatias + tasks (T-CER-NNN — numeração fina no /tasks)

- **Fatia 0 (T-CER-001..00x)** — peça compartilhada reconciliação: compõe
  `faixa_cobertura` + `avaliar_u_cmc` num avaliador `reconciliar_pontos` puro; testes.
- **Fatia 1a (T-CER-01x)** — domínio puro, **nesta ordem (tech-lead)**: VOs/enums →
  `reconciliacao_hash` puro (encadeamento+canonicalização) → `CertificadoSnapshot` +
  `PontoReconciliadoSnapshot` + `AnaliseReconciliacaoCertificado` → **máquina de estados
  explícita** (`RASCUNHO`→`EMITIDO`→`SUBSTITUIDA`/`REVOGADO`; reconciliação ligada a
  `calibracao_id`, sem materializar `RASCUNHO`) → transições → repository Protocol;
  testes puros.
- **Fatia 1b-schema (T-CER-02x, TL-02)** — model `Certificado` estendido (colunas
  tipadas, ADR-0078 achatada) + `ponto_reconciliado` + `analise_reconciliacao_cert` +
  migrations RLS v2/WORM Padrão B/grants/seed + triggers WORM + mappers/repositories +
  drill estrutural. **Não quebrar trigger INV-025 de imutabilidade de equipamento.**
- **Fatia 1b-numeração (T-CER-03x, TL-03)** — sequence PG `certificado_numero_seq` +
  `NumeroReservado` (TTL) + trigger virada anual + `numero_interno` vs visível;
  cancelamento preserva número. (Threaded gap-detection = TRACK Wave A.)
- **Fatia 2 (T-CER-04x)** — use cases. **Ordem (tech-lead Q3): `decidir_ponto_reconciliacao`
  (RT, WORM) é PRÉ-CONDIÇÃO separada** (roda sobre a reconciliação calculada de uma
  calibração APROVADA, ligada a `calibracao_id`, idempotência própria por ponto+correlation)
  → depois `emitir_certificado` ATÔMICO (consome APROVADA via evento `calibracao.aprovada`,
  trava CGCRE NC-09/C-06, reconcilia ponto-a-ponto, valida completude das decisões RT,
  numera, perfil server-side, crava snapshot WORM + `reconciliacao_hash` numa transação,
  emite `Certificados.CertificadoReconciliado`; ponto não-RBC sem decisão → 422
  `RECONCILIACAO_PENDENTE_DECISAO_RT` sem persistir) + `reemitir_certificado` (v(N+1),
  v(N)→SUBSTITUIDA) + CertificadoViewSet REST + idempotência (IDEMP-001) + eventos WORM.
- **Fatia 3 (T-CER-05x)** — fechamento: INV-CER-* em REGRAS + `TestINV_CER_*` nomeadas +
  **teste anti-reconsulta (TL-04): mock que FALHA se read-path do cert emitido invocar
  `cmc_para`/`tenant_perfil_e`** + hooks (candidatos: `cert-reconcilia-fail-closed`,
  `cert-snapshot-nao-reconsulta`, `cert-perfil-rbc-so-A`) + matriz-reconciliacao +
  emenda PRD se necessário + P9 (auditores roteados INV-RITUAL-003).

## 6. Decisões cravadas (não reabrir — fonte: reviews-consolidado + spec §9)

- Evento desta frente = **`Certificados.CertificadoReconciliado`** (NÃO `CertificadoEmitido`
  — normativo cl. 7.8, dispara na assinatura A3 Wave A). `status='emitido'` interno = emissão
  metrológica (números definitivos + snapshot congelado), não distribuível até A3.
- **NÃO inventar estado `EMITIDO_LOGICO`** na entidade metrológica — pendência de documento
  vive no futuro `DocumentoCertificado` (Wave A, fora desta frente).
- **2 entidades (Q6):** `Certificado` (WORM, esta frente) + `DocumentoCertificado` (Wave A).
- Tabela achatada + lógica aninhada (ADR-0078); migration aditiva sobre o stub.
- `tem_emitido` explícito (`.filter(status='emitido', revogado_em__isnull=True)`) — TL-05.
- Vigência dos padrões usados confirmada no snapshot (NC-07, cl. 6.5).

## 7. GATEs fechados / rastreados

- **Fecha:** GATE-CAL-EMISSAO-RECONCILIA-FAIXA, GATE-ECMC-U-MAIOR-CMC.
- **Rastreado Wave A (diferido):** GATE-CER-PDF / -A3 / -OCSP / -TSA / -PORTAL / -QR /
  -EMAIL / -EXPORT / -POSEMISSAO; GATE-CER-DRILL-LOCAL (drills comportamentais PG-real:
  imutabilidade cruzada equipamento, numeração sem buraco threaded, anti-reconsulta).

## 8. Perguntas de revisão do PLAN (rotear)

**Para `consultor-rbc-iso17025`:**
- A reconciliação consumindo `OrcamentoPorPonto.U_expandida_no_ponto` (ADR-0077) por
  `ponto_calibracao` está metrologicamente correta? Há risco quando há MÚLTIPLAS
  repetições no mesmo ponto (a U do ponto já agrega as repetições via Tipo A — confirmar
  que NÃO se soma U por repetição)?
- Partição rbc/não-rbc + decisão RT WORM (NC-03) está suficiente p/ CGCRE, ou falta
  algum registro (ex.: justificativa de exclusão exige classe específica)?
- `faixa_certificado` metadado [min,max] + pontos discretos — algum requisito de
  ordenação/gap mínimo entre pontos que devamos validar?

**Para `tech-lead-saas-regulado`:**
- ADR-0078 tabela achatada: estender o stub `infrastructure/certificados/` (não-aninhado,
  Marco 2) é aceitável OU migrar p/ `infrastructure/metrologia/certificados/` (ADR-0072)?
  O stub tem o trigger INV-025; mover quebraria o contrato cross-app?
- `reconciliacao_hash` (fecho WORM da tabela ponto-a-ponto) — replicar o padrão
  `cadeia_pontos_hash` do ADR-0077 (encadear hashes dos pontos ordenados)?
- A decisão do RT por ponto (`decidir_ponto_reconciliacao`) acontece ANTES de `emitir`
  (pré-condição) ou é um sub-estado da emissão (`RASCUNHO`→decisões→`emitido`)? Impacta
  idempotência + atomicidade.

## 9. Veredito

Plan **`ready-for-tasks`** — revisão `tech-lead` + `consultor-rbc` do plano CONCLUÍDA
(2026-05-31, **ambas APROVA COM CORREÇÕES**, todas incorporadas):
- **consultor-rbc (C-01..C-06):** INV-CER-RECONCILIA-005 (lookup 1:1, anti dupla-contagem),
  `categoria_motivo` enum, ressalva não-RBC no ponto, precedência determinística de
  classificação, INV-CER-RECONCILIA-004 (ordenação canônica), CGCRE-VIG-001 reescrita
  (ativo+não-suspenso+data_emissão). 1 item homologação cl. 7.11 → humano credenciado.
- **tech-lead:** path híbrido ADR-0078 (tabela em `infrastructure/certificados/` achatada
  + lógica aninhada), `reconciliacao_hash` com payload ampliado (congela decisão), decisão
  RT como PRÉ-CONDIÇÃO separada + máquina de estados explícita (RASCUNHO não materializado),
  ordem das tasks Fatia 1a, teste anti-reconsulta.

Item #0 (ADR-0077) FECHADO. Próximo: `/tasks` → implement (Fatia 0 → 1a → 1b-schema →
1b-numeração → 2 → 3) → P9. **Pendente humano credenciado pré-produção (homologação,
não bloqueia frente):** validação cl. 7.11 do motor de incerteza por ponto + dossiê RBC.
