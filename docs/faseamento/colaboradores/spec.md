---
owner: agente-ia
revisado-em: 2026-06-13
proximo-review: 2026-09-13
status: stable
diataxis: reference
audiencia: [agente, auditor]
frente: colaboradores
tipo: spec
versao: 2
relacionados:
  - docs/faseamento/colaboradores/T-COL-000-investigacao.md
  - docs/faseamento/colaboradores/reviews-consolidado.md
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md
  - docs/dominios/rh-frota-qualidade/modulos/colaboradores/modelo-de-dominio.md
  - docs/adr/0016-operacao-consistente.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/faseamento/plano-dependencia-sistema.md
---

# Spec v2 — frente `colaboradores` (RH mínimo, base nível 2)

> Recorte sobre o PRD `docs/dominios/rh-frota-qualidade/modulos/colaboradores/prd.md`
> (AC-COL-01..07) + Família 0 completa. Frente #4 da cadeia. Greenfield (T-COL-000 §1).
> **v2 (2026-06-13):** incorpora P2 — tech-lead TL-COL-01..15 + advogado ADV-COL-01..08,
> AMBOS APROVA COM CORREÇÕES (`reviews-consolidado.md`). **Decisões Roldão (batch P2):**
> R-COL-1 MOTORISTA sem CNH = salvar com pendência; R-COL-2 ASO fora do MVP (dono = SST).

## 1. Tese e fronteira

`colaboradores` é o **cadastro-base de quem trabalha pro tenant** — identidade (PII),
papéis de negócio, matriz de habilidades, % de comissão default e documentos. Pré-requisito
DURO de 6 módulos a jusante (agenda, app-tecnico, treinamentos, SST, frota, comissoes) que
o referenciam por **UUID opaco** (`colaborador_id`/`tecnico_id`), não por FK estrutural.
Sobe de Wave B → **Wave A nível 2** (`plano-dependencia-sistema.md` gap #4).

**O que NÃO é (fronteiras):**
- **Não é folha/eSocial/ponto/avaliação/benefícios/férias** (non-goals PRD §5).
- **Não é dono de RBAC** (ADR-0012): papel de **negócio** (TECNICO/SIGNATARIO/…) ≠ perfil
  **authz**; publica `PapelAtribuido/Revogado` → `acesso-seguranca` materializa `UsuarioPerfilTenant`.
- **Não modela treinamento/ASO/jornada UMC** — donos são `treinamentos`/`SST`/`frota`.
  Aqui só vincula papel MOTORISTA_UMC + CNH; jornada Lei 13.103 (INV-020) é de frota/agenda.
  **ASO fora do MVP** (R-COL-2 — dado de saúde art. 11; dono = SST).
- **Não é fonte probatória do signatário** (TL-COL-01): o nome/CPF que vão ao certificado
  são o **snapshot WORM do `ResponsavelTecnicoTenant`** — colaboradores só **referencia** o RT.

## 2. Recorte núcleo vs diferido (por AC do PRD)

| AC | Núcleo Wave A | Diferido (GATE) |
|----|---------------|-----------------|
| AC-COL-01 dedup CPF | `INV-COL-CPF` UNIQUE parcial (tenant, cpf) WHERE não-deletado; VO `CPF`; 409 `DUPLICATE_CPF` | — |
| AC-COL-02 papel→dropdown | sem papel não retorna em `/elegiveis`; papéis filtram listagem | UI dropdown (frente telas) |
| AC-COL-03 signatário escopo | `INV-COL-SIGNATARIO-IDENTIDADE`+`-ESCOPO`: SIGNATARIO exige `usuario_id` casando com `RTCompetencia` vigente; 422 (INV-003; hard perfil A, configurável B/C/D) | — |
| AC-COL-04 comissão | `comissao_default_pct` (Decimal 5,2; CHECK 0..100) + `GET /{id}/comissao-vigente`; alteração grava audit (INV-001) | override por OS mora na OS; cálculo = `comissoes` |
| AC-COL-05 matriz habilidades | `Habilidade` (catálogo seed OU livre, nível); `GET /elegiveis` (DTO mínimo) retorna aptos OU vazio | gestão de validade = `treinamentos` |
| AC-COL-06 desligamento | `INV-COL-DESLIGAMENTO-CASCADE`: data_desligamento → revoga papéis → some de `/elegiveis`; histórico preservado; hard-delete bloqueado (`INV-COL-INATIVO`) | — |
| AC-COL-06-2 evento ≤2s | **publica `Colaborador.Desligado` via outbox** (payload v9) | 6 consumers (módulos futuros); `comissoes_pendentes_count`=0 stub → GATE-COL-COMISSAO-COUNT |
| AC-COL-07 WCAG | erro PT-BR sem jargão + dado servido pronto p/ UI acessível | conformidade WCAG/PDF-UA na UI (frente telas) |

## 3. Decisões cravadas (D-COL-1..14) — v2

- **D-COL-1 — Path ANINHADO por domínio (TL-COL-03):** `src/domain/rh_frota_qualidade/colaboradores/`
  + `src/application/rh_frota_qualidade/colaboradores/` + `src/infrastructure/colaboradores/`
  (infra sempre flat; `app_label = colaboradores`). Critério do codebase: domínio multi-módulo
  aninha (comercial/metrologia/operacao); precificacao/pps são módulos soltos (flat).
- **D-COL-2 — Colaborador↔Usuario(login) por FK opcional:** `usuario_id: UUID | None`. Nem
  todo colaborador tem login (terceirizado/PJ sem acesso). Provisionamento de login é opt-in
  e FORA desta frente (`acesso-seguranca` cria `Usuario`/`UsuarioPerfilTenant` ao consumir
  `PapelAtribuido`). **Exceção dura (TL-COL-01):** SIGNATARIO exige `usuario_id NOT NULL`.
- **D-COL-3 — Desligamento (negócio) ≠ soft-delete (correção) — DOIS mecanismos (TL-COL-04):**
  (a) `data_desligamento`+`motivo_desligamento`+`ativo` derivado → estado de negócio; manager
  `ativos` filtra `data_desligamento IS NULL` (alimenta `/elegiveis`); registro PERMANECE
  (INV-025). (b) `deletado_em`/`deletado_por_usuario_id`/`deletado_motivo` → soft-delete
  Padrão C (corrige cadastro errado; manager default filtra; `all_objects` expõe).
  **Hard-delete físico bloqueado** se houver OS/cert/comissão referenciando (`INV-COL-INATIVO`).
  **Anonimização LGPD (zonas ADR-0021) DIFERIDA** ao GATE-LGPD-RAT-CONSOLIDACAO.
- **D-COL-4 — Papel: entidade filha mutável com revogação auditada (TL-COL-09):**
  `data_inicio`, `data_fim?`, `revogado_em?` (campos do model — NÃO reusar VO `JanelaVigencia`
  em row mutável). Invariantes: (a) SIGNATARIO → identidade+escopo RT (D-COL-11); (b) DONO
  único por tenant (partial unique WHERE `data_fim IS NULL AND revogado_em IS NULL`; troca de
  DONO sob advisory lock por tenant — ADR-0065, TL-COL-11); (c) MOTORISTA_UMC → CNH com
  **pendência** (R-COL-1). Revogação seta `revogado_em`, nunca deleta linha (audit).
  **Verdade probatória do signatário mora no RT (WORM), não no papel.**
- **D-COL-5 — Habilidade + `CatalogoHabilidade` seed global literal (TL-COL-10):** `Habilidade`
  filha (`catalogo_id?` FK XOR `descricao_livre`, `nivel` enum APRENDIZ|CAPACITADO|MESTRE,
  `evidencia_url?`, `data_avaliacao`). `CatalogoHabilidade` é **model próprio em `colaboradores`**,
  global read-only, **seed literal na migration da frente** (molde global authz `0003`, não
  per-tenant). Lista de grandezas é **literal no arquivo** (sem import de `metrologia` — quebra
  a aresta runtime com `calibracao`, objetivo do gap #4). Tenant não edita catálogo; pode
  registrar habilidade livre.
- **D-COL-6 — Documento anexo via `AnexoStoragePort` (local Wave A) — foto inclusa, SEM ASO:**
  `Documento` (tipo CTPS|CNH|CERTIFICADO_CURSO|OUTRO — **ASO removido, R-COL-2**; `storage_key`,
  `sha256` server-side, `data_upload`, `data_validade?` só armazena). Adapter `AnexoStorageLocal`
  content-addressed. **Foto via a mesma porta** (TL-COL-06): EXIF strip + MIME/5MB; **sem blur**
  (foto de colaborador é dado COMUM de identificação, art.7º V — não biométrico; o rosto é a
  finalidade; ADV-COL-02). **B2 WORM real diferido** (GATE-COL-ANEXO-B2). `INV-COL-DOC-VINCULO`
  (alerta): TERCEIRIZADO/PJ não anexam CTPS (minimização art.6º III, ADV-COL-01).
- **D-COL-7 — Mascaramento PII multi-papel, choke-point server-side (TL-COL-05/ADV-COL-04):**
  `filtrar_visao_pii(papeis_solicitante, sujeito, dados)` com `MATRIZ_VISAO_PII[campo][papel]`
  + caso especial `proprio_colaborador` (solicitante == sujeito); aplicado em TODO serializer;
  fail-closed (sem papel → mascarado). Regras (`exports.md`): **CPF só DONO** (demais veem
  `***.***.***-NN` **últimos 2 dígitos** — corrigir exports.md no P8); e-mail/telefone
  Dono/Gerente/próprio; CTPS/CNH só Dono+próprio. Busca `q` por CPF só p/ quem tem `ver_pii`
  (ADV-COL-08, anti-oráculo). **`/elegiveis` tem DTO allowlist próprio** (`INV-COL-ELEGIVEIS-MINIMO`):
  `colaborador_id`, `nome_exibicao`, `papel`, `habilidades`, `ativo` — NUNCA CPF/e-mail/telefone/
  documentos/comissão/foto/vínculo/observação.
- **D-COL-8 — PII pseudonimizada em evento/log (ADV-COL-06):** CPF/nome/documento **hashificados**
  (HMAC-tenant ADR-0029/0064 — **pseudonimização**, não anonimização) em payload de evento,
  log estruturado, corpo 4xx/5xx; só refs/UUID em claro (`INV-COL-PII-LOG`, molde INV-PRC-SEGREDO-LOG).
  Chave HMAC-tenant é PII-crítica. Telemetria usa `colab_id` hash (métricas.md).
- **D-COL-9 — Comissão: só o default mora aqui (TL-COL-14).** `comissao_default_pct` (CHECK
  0..100) + audit (INV-001). Override por OS e cálculo (BIG-09) são do consumidor. `GET
  /{id}/comissao-vigente` → `{pct_default, vigente_desde}`.
- **D-COL-10 — `Colaborador.Desligado` por OUTBOX TRANSACIONAL (TL-COL-02):** publica via
  `outbox=True` (ADR-0033 — INSERT em `bus_outbox` no mesmo `transaction.atomic`), payload v9
  completo + **chave idempotente estável** (`colaborador_id+data_desligamento`, TL-COL-13) para
  os consumers deduplicarem. Os 6 consumers (INV-INT-011) são módulos futuros — plugam handlers
  no outbox sem retrofit do publisher. **NÃO usar "fail-open lazy"** aqui (é para predicate
  síncrono, não publicação). `is_rt_signatario`/`tipos_servico_assinava` derivam do papel
  SIGNATARIO + RT; `comissoes_pendentes_count`=0 stub (GATE-COL-COMISSAO-COUNT).
- **D-COL-11 — SIGNATARIO: identidade + escopo, perfil-aware (TL-COL-01, ADR-0067, REGRAS:33):**
  atribuir SIGNATARIO exige (i) `colaborador.usuario_id IS NOT NULL`; (ii) `RTCompetencia`
  vigente com **o mesmo `usuario_id`** (`INV-COL-SIGNATARIO-IDENTIDADE` — casa pessoa, não só
  "FK RT existe"); (iii) escopo vigente na data (INV-003). **Bloqueio HARD em perfil A**;
  configurável em B/C/D (`tenant_perfil_e`). Em D ("Relatório de Aferição") não produz assinatura
  ISO acreditada. Linha matriz-feature-perfil (A8) no P8.
- **D-COL-12 — REST molde precificacao:** idempotência 2 camadas (Idempotency-Key em escrita),
  `ACTION_MAP` authz `colaboradores.*`, eventos canônicos, perfil/mascaramento server-side.
  `prefetch_related` em list/`/elegiveis` (anti-N+1, TL-COL-12; `assertNumQueries` no P7).
- **D-COL-13 — MOTORISTA_UMC sem CNH = SALVAR COM PENDÊNCIA (R-COL-1):** cadastra com
  `pendencia_cnh=true`; **não** retorna 422 no cadastro. O bloqueio de risco real acontece na
  **alocação** (frota/agenda), fora desta frente. Corrigir api.md/ui.md no P8.
- **D-COL-14 — Audit trail INV-001 via cadeia central (TL-COL-15):** alteração de
  `comissao_default_pct`, atribuição/revogação de papel e desligamento gravam trilha imutável
  via `publicar_evento` (cadeia hash, não tabela ad-hoc). Tabela `*_eventos` nasce com trigger
  anti-mutation (INV-AUDIT-IMMUT-002). `GET /{id}/auditoria` só Dono/Qualidade.

## 4. Modelo (domínio)

**Path:** `src/domain/rh_frota_qualidade/colaboradores/` (D-COL-1).

**Agregado raiz `Colaborador`:** `id`, `tenant_id` (NOT NULL, INV-TENANT-002), `nome`,
`cpf` (VO `CPF`, UNIQUE parcial WHERE não-deletado — INV-COL-CPF), `email`, `telefone`,
`foto_storage_key?`, `usuario_id?` (FK opcional — D-COL-2), `vinculo` (enum
CLT|PJ|ESTAGIARIO|SOCIO|TERCEIRIZADO), `data_admissao`, `data_desligamento?`,
`motivo_desligamento?`, `comissao_default_pct` (Decimal 5,2, CHECK 0..100), `observacao`,
`ativo` (derivado de `data_desligamento`); soft-delete Padrão C (`deletado_em`/
`deletado_por_usuario_id`/`deletado_motivo`). CPF **imutável** pós-criação.

**Entidades filhas:**
- `Papel` (`colaborador_id`, `papel` enum 7, `data_inicio`, `data_fim?`, `revogado_em?`,
  `responsabilidade_tecnica_id?` quando SIGNATARIO, `pendencia_cnh: bool` quando MOTORISTA_UMC).
- `Habilidade` (`colaborador_id`, `catalogo_id?` FK, `descricao_livre?`, `nivel` enum,
  `evidencia_url?`, `data_avaliacao`; CHECK `catalogo_id` XOR `descricao_livre`).
- `Documento` (`colaborador_id`, `tipo` enum {CTPS,CNH,CERTIFICADO_CURSO,OUTRO}, `storage_key`,
  `sha256`, `data_upload`, `data_validade?`).

**Entidade global (model próprio):** `CatalogoHabilidade` (`codigo`, `descricao`, `grandeza?`)
— read-only pro tenant, seed literal global na migration da frente (D-COL-5).

**Domínio puro:** `BASE_LEGAL_POR_VINCULO_E_CATEGORIA` (constante — fonte que o RAT do GATE
fotografa; ADV-COL-01). VO `CPF` reusado. `JanelaVigencia` só no domínio puro, se necessário
(não no model mutável de Papel).

**Erros:** `DUPLICATE_CPF` (409), `SIGNATARIO_SEM_ESCOPO`/`SIGNATARIO_SEM_USUARIO`/
`SIGNATARIO_RT_NAO_CASA` (422), `CPF_INVALIDO` (422), `COLABORADOR_INATIVO` (409),
`DONO_JA_EXISTE` (409), `HARD_DELETE_BLOQUEADO` (409), `COMISSAO_FORA_DA_FAIXA` (422).

## 5. Invariantes candidatas (P7 crava em REGRAS + hook)

| INV candidata | Enforcement |
|---------------|-------------|
| INV-COL-CPF | UNIQUE parcial (tenant_id, cpf) WHERE não-deletado + `clean()` VO + hook migration-linter |
| INV-COL-SIGNATARIO-IDENTIDADE | domínio + use case: SIGNATARIO exige `usuario_id` casando com `RTCompetencia` vigente; 422; teste UNHAPPY (usuario nulo / RT de outra pessoa) |
| INV-COL-SIGNATARIO-ESCOPO | escopo vigente na data (INV-003); hard perfil A, configurável B/C/D |
| INV-COL-DONO-UNICO | partial unique (tenant) WHERE papel=DONO AND data_fim IS NULL AND revogado_em IS NULL; advisory lock na troca |
| INV-COL-INATIVO | **fail-open lazy** (ADR-0066): check use case via porta a jusante (stub bloqueia conservador) + trigger PG defensivo BEFORE DELETE; hook `col-hard-delete-check` |
| INV-COL-DESLIGAMENTO-CASCADE | use case: desligar → revoga papéis (revogado_em) + publica evento (outbox); teste UNHAPPY |
| INV-COL-PII-MASCARA | `filtrar_visao_pii()` multi-papel choke-point em TODOS serializers + teste UNHAPPY por papel + hook `col-pii-mascara-check` |
| INV-COL-ELEGIVEIS-MINIMO | DTO allowlist no `/elegiveis` (sem PII) + teste UNHAPPY "campo fora da allowlist" |
| INV-COL-DOC-VINCULO | alerta: documento incompatível com vínculo (TERCEIRIZADO/PJ × CTPS) — minimização |
| INV-COL-PII-LOG | CPF/nome/documento nunca em claro em evento/log/4xx — só hash/refs + hook `col-evento-pii-hash-check` |
| INV-COL-COMISSAO-AUDIT | alteração `comissao_default_pct` grava audit INV-001 (CHECK 0..100) |
| INV-TENANT-001/002/003 · INV-001 · INV-016 (herdadas) | tenant_id WHERE+NOT NULL+RLS; audit hash-encadeado; dado pronto p/ UI acessível |

## 6. Portas, eventos e seams

- **Consome:** VO `CPF` (shared); `responsavel_tecnico` (FK + predicate competência, por
  `usuario_id`); `AnexoStoragePort` (local); authz + idempotência + eventos canônicos + perfil
  server-side (F-B/F-C); `tenant_perfil_e` (ADR-0067); porta a jusante (fail-open lazy) p/ INV-COL-INATIVO.
- **Expõe:** `GET /elegiveis` (DTO mínimo; agenda/OS) · `GET /{id}/comissao-vigente`
  (comissoes/financeiro) · eventos canônicos · contrato `Colaborador.Anonimizado` (A5,
  publicável agora; materialização no GATE LGPD).
- **Eventos (catálogo v9; via outbox; PII pseudonimizada por evento — D-COL-8):**

| Evento | Hash (HMAC-tenant) | Em claro permitidos | Transporte |
|--------|--------------------|---------------------|------------|
| `Colaborador.Cadastrado` | `cpf_hash`, `nome_hash` | colaborador_id, tenant_id, vinculo | outbox |
| `Colaborador.PapelAtribuido`/`PapelRevogado` | `ator_id_hash` | colaborador_id, papel, vigência, escopo_ref (UUID) | outbox |
| `Colaborador.HabilidadeAtualizada` | — | colaborador_id, catalogo_id/hash-livre, nivel | outbox |
| `Colaborador.Desligado` | `motivo_hash` | colaborador_id, is_rt_signatario, tipos_servico_assinava, comissoes_pendentes_count, chave idempotente | outbox |
| `Colaborador.Anonimizado` (contrato; materialização no GATE) | — | colaborador_id, campos zerados | outbox |

## 7. REST (núcleo)

`ColaboradorViewSet`: list (`papel/vinculo/ativo/habilidade/q`, paginado ≤100, prefetch) ·
create (Dono) · retrieve (agregado mascarado, prefetch) · partial_update (CPF imutável) ·
destroy = **desligamento** (`data_desligamento`+`motivo`, cascade, evento outbox) ·
`papeis` (POST/DELETE) · `habilidades` (POST/DELETE) · `documentos` (POST anexo) ·
`auditoria` (GET, Dono/Qualidade) · `elegiveis` (GET, DTO mínimo) · `comissao-vigente` (GET).
Ações authz `colaboradores.*`: `cadastrar`, `editar`, `desligar`, `ver`, `ver_pii`
(CPF/documentos), `gerir_papel`, `gerir_habilidade`, `ver_comissao`, `ver_auditoria`,
`consultar_elegiveis`. Todo serializer passa por `filtrar_visao_pii`; `/elegiveis` usa DTO allowlist.

## 8. Non-goals (além dos do PRD §5)

Folha/holerite · eSocial/DIRF/RAIS · ponto eletrônico · avaliação de desempenho ·
vagas/recrutamento/onboarding · benefícios · férias/banco de horas · **ASO/gestão de saúde
(módulo SST)** · gestão de validade de treinamento (treinamentos) · jornada UMC (frota/agenda)
· cálculo de comissão (comissoes) · provisionamento de login (acesso-seguranca) · UI/telas ·
geração de exports XLSX/CSV/ZIP/PDF (frente telas — backend serve só o dado mascarado) ·
B2 WORM real de anexos · anonimização LGPD (GATE) · **reconhecimento/matching facial** (vira
art.11 §4 — exige RIPD+ADR; hook `block-biometric-feature`).

## 9. GATEs rastreados

GATE-COL-ANEXO-B2 (B2 WORM real dos documentos+foto) · GATE-COL-COMISSAO-COUNT
(`comissoes_pendentes_count` real) · GATE-COL-CONSUMERS (6 reatores de `Colaborador.Desligado`)
· GATE-COL-PERFIL-MATRIZ (linha matriz-feature-perfil SIGNATARIO por perfil — A8) ·
**GATE-LGPD-RAT-CONSOLIDACAO** (CONGELADO — A3 RAT CTPS/CNH/foto/cert · A4 retenção · A6 zona
ADR-0021 por campo · A7 DPIA cadastro · `[OAB-PRE-PROD]`: texto bloqueio titular, ratificação
matriz de zonas, DPA Aferê↔tenant, designação DPO — bloqueiam go-live com dado real, não dogfooding).

## 10. Log de revisões (P2 — 2026-06-13)

- ✅ `tech-lead-saas-regulado` — **APROVA COM CORREÇÕES**: TL-COL-01..15 incorporados
  (detalhe em `reviews-consolidado.md`). Bloqueantes 01/02/05/06/08 resolvidos.
- ✅ `advogado-saas-regulado` — **APROVA COM CORREÇÕES** (congelamento RAT/DPIA respeitado):
  ADV-COL-01..08 incorporados; 3 MÉDIO absorvidos no código (base legal/vínculo, `/elegiveis`
  mínimo, ASO removido). GATEs congelados rastreados.
- ✅ rodada batch Roldão: R-COL-1 (MOTORISTA pendência) + R-COL-2 (ASO fora do MVP).
- Emendas cross-doc pendentes P8: api.md/ui.md (remover 422 MOTORISTA), exports.md (CPF 2
  dígitos + ASO fora do E-COL-04), faseamento-modulos.md (Wave B→A), matriz-feature-perfil (A8).
