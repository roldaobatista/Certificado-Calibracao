---
owner: roldao
revisado-em: 2026-05-31
status: stable
fase: M7-procedimentos-calibracao
dominio: metrologia
modulo: procedimentos-calibracao
ritual: specify
versao: 1
fontes:
  - docs/dominios/metrologia/modulos/calibracao/prd.md (US-CAL-016 — AC-CAL-016-1/2/3)
  - src/infrastructure/calibracao/predicates_calibracao.py (procedimento_vigente_para — STUB ADR-0066)
  - src/application/metrologia/calibracao/configurar_calibracao.py (seam ADR-0073 + faixa_calibrada_declarada)
  - docs/faseamento/M6-escopos-cmc/spec.md (módulo-espelho — mesmo molde)
  - docs/faseamento/ordem-dependencia-bloco-metrologia.md (#3 — consome peça #1)
adrs:
  - 0002 (RLS) / 0007 (codegen) / 0025 v2 (validação software) / 0029 (canonicalização)
  - 0030 (vigência) / 0031 (soft-delete B) / 0064 (HMAC 25a) / 0067 (perfil)
  - 0066 (predicates fail-open lazy — este módulo o substitui por real) / 0072 (path aninhado)
  - 0073 (validação no use case, não permission layer) / 0076 (faixa declarada = portão config)
  - 0064 (HMAC — só eventos hash-chain, NÃO o anexo PDF) / 0065 (advisory lock superseção)
---

# Spec de faseamento — M7 `metrologia/procedimentos-calibracao` (3º módulo Wave A)

> **v2 (2026-05-30):** atualizada pós-revisões `consultor-rbc-iso17025` +
> `tech-lead-saas-regulado` (APROVA COM CORREÇÕES — ver `reviews-consolidado.md`).
> +INV-PROC-008/009/010; anexo = `sha256` server-side (NÃO HashVersionado);
> `procedimento_versao_snapshot` JÁ EXISTE (M4 P4) — M7 só preenche; B/C/D aviso
> degradante; +GATE-PROC-METODO-VALIDADO. Nenhuma ADR nova.

> **Ritual (memória `feedback_ritual_orquestrador`):** este é o passo `/specify`.
> Próximos passos OBRIGATÓRIOS antes de qualquer código: `plan` revisado pelos
> subagentes (`tech-lead-saas-regulado`, `consultor-rbc-iso17025`) → `tasks` →
> `implement` → auditores Família 5 roteados por risco (INV-RITUAL-003). **Nada
> de código antes do plan revisado.**
>
> **Por que este módulo importa:** destrava `GATE-CAL-PROC-VIGENTE-PREDICATE`
> (origem PROD-CAL-02 / ADR-0066). Hoje o predicate `procedimento_vigente_para`
> é STUB fail-open (`predicates_calibracao.py:199-227` retorna sempre `True`),
> deixando passar emissão RBC **sem procedimento técnico documentado controlado
> vigente** — violação direta de ISO 17025 cl. 7.2.1. É o **módulo-irmão** de
> `escopos-cmc` (M6): a ADR-0066 deixou os DOIS predicates em fail-open lazy;
> M6 fechou `cmc_cobre`, M7 fecha `procedimento_vigente_para`.

## 1. Objetivo

Construir o cadastro, versionamento e validação do **Procedimento de Calibração**
(o "como medir" — método/norma técnica documentada e controlada por par
grandeza/faixa) de um tenant: o catálogo de **procedimentos vigentes** que torna
o predicate `procedimento_vigente_para` real e o bloqueio efetivo (412
`ProcedimentoVigenteAusente`). **Espelha `escopos-cmc` (M6)** no molde estrutural
(entidade Django persistida, WORM Padrão B, vigência canônica, path aninhado,
porta consumida pelo predicate) — diferindo na semântica: aqui a validação é
**existência de procedimento vigente que cobre a faixa**, NÃO cobertura
tridimensional de CMC (não há U≥CMC; é o "como", não o "quanto"). Documento
técnico controlado cl. 7.2.1 com **anexo PDF versionado + hash** (integridade do
documento controlado). Perfil-aware (ADR-0067), vigência canônica (ADR-0030),
WORM Padrão B (ADR-0031), path aninhado (ADR-0072).

## 2. Escopo (deriva de US-CAL-016 — não duplicar AC aqui)

- CRUD de `ProcedimentoCalibracao` (colunas tipadas — não JSONField — p/ índice
  grandeza+range): `codigo` (ex. "PC-MASSA-001"), `titulo`, `grandeza`,
  `faixa_min/max`, `unidade`, `metodo_norma` (NIT-DICLA / norma técnica de
  referência), `anexo_pdf_storage_key` + `anexo_pdf_hash` (HashVersionado),
  `versao` + `vigente_a_partir`, vigência canônica ADR-0030.
- Versionamento: revisão = INSERT de nova `versao` preservando a anterior
  (AC-CAL-016-3 — superseção; auditoria retroativa).
- Revogação/desativação WORM Padrão B (`revogado_em` + `motivo_revogacao`;
  DELETE bloqueado por trigger).
- `procedimento_vigente_para` real fail-CLOSED: RBC (perfil A) configurando
  grandeza+faixa SEM procedimento CONFIRMADO vigente → 412
  `ProcedimentoVigenteAusente` na **configuração**.
- Resolução + snapshot na configuração: vincula `Calibracao.procedimento_id` +
  `Calibracao.procedimento_versao_snapshot` (código + versão + hash do anexo) —
  imutável (AC-CAL-016-3 / INV-CAL-WORM-001 estendido).
- Porta `procedimento_repo.vigente_em(tenant_id, grandeza, faixa, data)`
  consumida pelo predicate `procedimento_vigente_para`.
- Consome a **peça compartilhada** `Calibracao.faixa_calibrada_declarada`
  (ADR-0076 — já entregue na frente SAN-FAIXA-CALIBRADA): a faixa solicitada
  server-side vem desse campo de 1ª classe, NÃO do payload.
- Rótulo que o cliente lê: **"Procedimento técnico"** + **"Código do
  procedimento"** + **"Norma de referência"**.

## 3. Non-goals (explícito)

NÃO: a CMC/escopo de acreditação (é `escopos-cmc` — M6, já entregue); o padrão
físico usado (é `metrologia/padroes` — M5); a emissão de certificado (é
`certificados`); a gestão da acreditação CGCRE (é `licencas-acreditacoes`); o
fluxo de aprovação documental SGQ completo (versão controlada com workflow de
revisão/aprovação multi-papel é simplificada aqui — só o ciclo
RASCUNHO→PUBLICADO→REVOGADO + RT publica); geração/edição do PDF do procedimento
(o anexo é upload de documento pronto — storage + hash, não editor); extração de
PDF (procedimento é autorado internamente, NÃO extraído de fonte externa como o
escopo CGCRE — **sem fatia de extração**). PDF/A de relatório.

## 4. Entidade + agregado

**Agregado raiz `ProcedimentoCalibracao`** (model Django, colunas tipadas,
path aninhado `src/infrastructure/metrologia/procedimentos_calibracao/`,
`label="procedimentos_calibracao"` — ADR-0072). Campos canônicos: `codigo`
(identidade do documento controlado cl. 8.3), `titulo`, `grandeza` (UMA por
código — D-PROC-2), `faixa_min/max`, `unidade`, `metodo_norma`, `tipo_metodo`
(NORMALIZADO / NAO_NORMALIZADO / MODIFICADO — cl. 7.2.2 / D-PROC-5),
`registro_validacao_id` (FK opcional — evidência de validação de método não-
normalizado), `numero_revisao` (ex. "Rev. 03" — distinto de `versao`, cl.
8.3.2c), `aprovado_em` (data do ato de aprovação ≠ vigência — cl. 8.3.1),
`aprovado_por_id` (+ snapshot do nome — quem aprovou), `anexo_pdf_storage_key`,
`anexo_pdf_sha256` (sha256 puro do binário, recalculado SERVER-SIDE — NÃO
HashVersionado/HMAC; molde OS `termo_pdf_sha256`), `versao` + `vigente_a_partir`
(AC-CAL-016-3). Vigência
canônica ADR-0030 (`vigencia_inicio` NOT NULL / `vigencia_fim` NULL=aberta /
`revogado_em` / `motivo_revogacao` ≥10 chars). Soft-delete Padrão B WORM
(ADR-0031 / INV-SOFT-002 / trigger PG). `revision` (CAS) + `correlation_id`
(molde M5/M6).

**Estado de ciclo de vida:** `RASCUNHO` (editável, em elaboração) → `PUBLICADO`
(vigente, controlado, imutável WORM Padrão B) → `REVOGADO` (terminal). Só
`PUBLICADO` + vigente entra na consulta `vigente_em()`. Revisão de procedimento
publicado = INSERT de nova `versao` (a anterior é encerrada por `vigencia_fim`,
preservada para auditoria retroativa — AC-CAL-016-3).

VOs reusados de `src/domain/metrologia/value_objects.py` (`Grandeza`,
`FaixaMedicao`). **Não recriar** (T-PROC-003). Domínio puro sem Django (ADR-0007).
**Reuso da geometria de faixa:** a contenção `faixa ⊆ faixa_procedimento` é a
mesma de `escopos_cmc.cobertura.faixa_contida` — decisão tech-lead no /plan:
extrair helper compartilhado em `domain/metrologia/` vs replicar a verificação
trivial (§9 A).

## 5. User Stories → mapa de implementação (AC detalhado em US-CAL-016 + /plan)

| US | Tema | Bloqueia / herda | Perfil |
|----|------|------------------|--------|
| US-PROC-001 | Cadastrar procedimento (RASCUNHO, editável) + anexo PDF | herda US-CAL-016 | todos (A obrigatório) |
| US-PROC-002 | Publicar procedimento (RASCUNHO→PUBLICADO, vigente) | cl. 7.2.1 | A=RT publica |
| US-PROC-003 | Revisar procedimento (nova versão, anterior preservada) | AC-CAL-016-3 | todos |
| US-PROC-004 | Revogar procedimento (WORM Padrão B) | ADR-0031 | todos |
| US-PROC-005 | Resolver procedimento vigente na configuração (`procedimento_vigente_para` real → 412) | AC-CAL-016-1/2 + GATE-CAL-PROC-VIGENTE-PREDICATE | **A (RBC)** |
| US-PROC-006 | Snapshot `procedimento_versao_snapshot` congelado na calibração | AC-CAL-016-3 / INV-CAL-WORM-001 | **A** |

## 6. Invariantes (a cravar em REGRAS-INEGOCIÁVEIS no `implement`)

- **INV-PROC-001** — procedimento técnico documentado vigente na data: resolução
  via `vigente_em(tenant_id, grandeza, faixa, data)` só considera `PUBLICADO` +
  vigente em `data` (ADR-0030) que CONTÉM a faixa solicitada (contenção total).
  Fonte de US-CAL-016 / cl. 7.2.1.
- **INV-PROC-002** — UNIQUE tenant-scoped da chave natural do procedimento
  (provisório `(tenant_id, codigo, versao)` — `codigo` é a identidade controlada;
  granularidade grandeza×faixa por código a confirmar com RBC, §9 B).
- **INV-PROC-003** — procedimento PUBLICADO é WORM Padrão B: muta só via
  revogação (`revogado_em`+`motivo_revogacao`); DELETE bloqueado por trigger;
  revisão cria nova `versao` preservando a anterior (AC-CAL-016-3). Campos
  técnicos (`metodo_norma`/`faixa_*`/`anexo_pdf_hash`) congelados pós-publicação.
- **INV-PROC-004** — `procedimento_vigente_para` fail-CLOSED real: calibração RBC
  (perfil A) com grandeza+faixa SEM procedimento PUBLICADO vigente → DENY
  `procedimento_inexistente`/`procedimento_vencido` → view 412
  `ProcedimentoVigenteAusente`. Substitui o fail-open ADR-0066. (NÃO replicar
  fail-open.)
- **INV-PROC-005** — snapshot `procedimento_versao_snapshot` (campo que **JÁ
  EXISTE** em `ConfigurarCalibracaoInput` desde M4 P4 — M7 só PREENCHE, não cria
  coluna) congelado na configuração (código + versão + `numero_revisao` +
  `anexo_pdf_sha256` da época — canonicalização ADR-0029) imutável; superseção
  (RT publica N+1) NÃO altera calibração já configurada (AC-CAL-016-3 /
  INV-CAL-WORM-001 estendido).
- **INV-PROC-006** — vigência canônica ADR-0030 (tz-aware, CHECK INV-VIG-001..004).
- **INV-PROC-007** — integridade do documento controlado: `anexo_pdf_sha256` é o
  sha256 do conteúdo do PDF, **recalculado server-side** (não confiar no
  cliente); alteração do anexo de procedimento PUBLICADO bloqueada (WORM —
  INV-PROC-003); o snapshot na calibração guarda o sha256 da época
  (rastreabilidade cl. 7.2.1). (HMAC ADR-0064 é dos EVENTOS hash-chain, não do
  anexo.)
- **INV-PROC-008** — não-overlap de vigência: no máximo UMA versão PUBLICADA
  vigente por `(tenant, codigo, grandeza, faixa_min, faixa_max)` numa data.
  Publicação de N+1 encerra `vigencia_fim` da anterior na MESMA transação, sob
  `pg_advisory_xact_lock(hash(tenant, codigo, grandeza, faixa))` (molde ADR-0065)
  + UNIQUE parcial `WHERE estado='PUBLICADO' AND vigencia_fim IS NULL AND
  revogado_em IS NULL`. (Race de 2 publicações simultâneas = 2 vigentes =
  ambiguidade regulatória.)
- **INV-PROC-009** — controle documental cl. 8.3.1: procedimento PUBLICADO tem
  `numero_revisao` + `aprovado_em` + `aprovado_por_id` preenchidos; os 3 entram
  no snapshot da calibração (reconstituível sem cruzar audit log).
- **INV-PROC-010** — qualificação de método cl. 7.2.2: `tipo_metodo` obrigatório;
  perfil A + `NAO_NORMALIZADO`/`MODIFICADO` exige `registro_validacao_id` antes
  de publicar — **fail-open lazy** (paralelo ADR-0066) até `licencas-acreditacoes`
  existir (GATE-PROC-METODO-VALIDADO).
- **Reusadas:** INV-CAL-WORM-001 (snapshot calibração imutável), INV-CAL-VERSAO-001,
  INV-VIG-001..004, INV-SOFT-001/002, INV-TENANT-001..004,
  INV-TENANT-PERFIL-001/003/004, INV-DOC-CANON-001, INV-HMAC-001..005 (eventos
  hash-chain — §9 E).

## 7. Integração com `procedimento_vigente_para` (porta consumida pelo predicate)

Stub a substituir (`predicates_calibracao.py:199-227`). **Contrato a honrar
(espelha o wire-in M6 ADR-0073):**
- A validação real vai para DENTRO do use case `configurar_calibracao` (ADR-0073
  — não no permission layer DRF), via injeção de porta
  `procedimentos_calibracao.query_service.vigente_em(tenant_id, grandeza, faixa,
  data) -> ProcedimentoSnapshot | None` (funções de módulo, NÃO singleton —
  molde M6/TL-C-04).
- Fonte de grandeza+faixa+data **server-side**: `Calibracao.grandeza_calibrada`
  + `Calibracao.faixa_calibrada_declarada` (peça #1 SAN-FAIXA-CALIBRADA — já
  entregue), NÃO o payload (SEG-CAL-10).
- `vigente_em()` filtra `tenant_id` EXPLÍCITO além da RLS (defesa em
  profundidade); só PUBLICADO + vigente em `data` + contenção total da faixa;
  preserva o **short-circuit perfil A** (não-A não é bloqueado — §9 C).
- Predicate STUB `procedimento_vigente_para` DEPRECADO (no-op) após wire-in.
- **GATE-CAL-PROC-VIGENTE-PREDICATE:** wire-in real + testes do caminho
  bloqueado + teste de transição fail-open→fail-closed (TST-005) sem quebrar
  legado + suíte M4 chave reverde.
- **Ordem composta escopo→procedimento (M6 §9 I):** em `configurar_calibracao`,
  a validação de cobertura de escopo (M6) roda ANTES; 1ª falha interrompe. Este
  módulo adiciona o 2º portão (procedimento) na mesma transição.

## 8. Decisões de produto (rótulos — análogo M6 decisões Roldão)

- Rótulo cliente: **"Procedimento técnico"** / **"Código do procedimento"** /
  **"Norma de referência"** (NIT-DICLA / ABNT / OIML).
- Aplicabilidade por perfil (**confirmado RBC — D-PROC-1**): bloqueio 412 **só
  perfil A** (RBC); **C ("em preparação") NÃO entra no bloqueio duro**; B/C/D
  recebem **aviso degradante recomendado** ("procedimento técnico documentado é
  recomendado — cl. 7.2.1", educa a trilha D→A; não bloqueia). US-PROC-005 ganha
  ramo NÃO-RBC = aviso (não no-op).

## 9. Questões abertas → roteamento /plan

| Q | Tema | Decisor | Recomendação inicial |
|---|------|---------|----------------------|
| A | geometria de faixa: helper compartilhado vs replicar `faixa_contida` | tech-lead | extrair `domain/metrologia/faixa_cobertura.py` compartilhado (escopos+procedimentos) — evita drift "kg vs kilograma" |
| B | granularidade chave: `(codigo, versao)` vs `(codigo, grandeza, faixa, versao)` | RBC + tech-lead | `codigo` é a identidade controlada; 1 procedimento cobre 1 grandeza+faixa (ou N?) — RBC decide se um código pode ter múltiplas faixas |
| C | short-circuit perfil: bloqueio só A vs A+C (em preparação) | RBC | só A bloqueia (molde M6 cobre); C/D aviso |
| D | cl. 7.2.1 aplica a B/C/D? | RBC | procedimento documentado recomendado p/ B/C; bloqueio duro só A |
| E | eventos hash-chain dedicados vs só audit trail | tech-lead | molde M6 (eventos WORM `procedimentos_calibracao.publicado/revisado/revogado` em ACOES_CANONICAS) |
| F | anexo PDF: hash do binário em upload — porta storage vs hash recebido | tech-lead | hash calculado server-side do binário (não confiar no cliente); storage key opaca |
| G | superseção: encerrar `vigencia_fim` da versão antiga ao publicar N+1 — automático vs manual | tech-lead + RBC | automático na publicação (uma vigente por código+faixa); calibração em curso preserva snapshot |
| H | WORM Padrão B vs C | tech-lead | Padrão B (molde M6) |

## 10. Faseamento proposto — 4 fatias (INV-RITUAL-002; detalhar no `tasks`)

- **Fatia 1a — Domínio puro:** entities/enums (`EstadoProcedimento`
  RASCUNHO/PUBLICADO/REVOGADO) + repository Protocols + cobertura de faixa
  (reuso/extração — §9 A) + invariantes puras + máquina de estados. Testes puros.
- **Fatia 1b — Schema + persistência:** model colunas tipadas + UNIQUE
  tenant-scoped + migrations irmãs (initial → RLS v2 → triggers WORM Padrão B →
  grants → seed authz `procedimentos_calibracao.{cadastrar,publicar,revisar,
  revogar,ver}`) + repositório/query_service `vigente_em()` (funções de módulo) +
  CAS + drill estrutural `validar_procedimentos_calibracao`.
- **Fatia 2 — Use cases + API + versionamento:** `cadastrar_procedimento`
  (RASCUNHO) / `publicar_procedimento` (RASCUNHO→PUBLICADO + encerra vigência da
  anterior) / `revisar_procedimento` (nova versão) / `revogar_procedimento`;
  ViewSet REST + serializers + idempotência (IDEMP-001) + urls na **raiz** +
  upload de anexo PDF (hash server-side — §9 F).
- **Fatia 3 — Wire-in do predicate + GATE-CAL-PROC-VIGENTE-PREDICATE:**
  `procedimento_vigente_para` real (drop-in ADR-0073), injeção server-side da
  faixa declarada (peça #1), teste transição fail-open→fail-closed (TST-005),
  snapshot `procedimento_versao_snapshot`, suíte M4 reverde, INV-PROC-* em REGRAS
  + `TestINV_PROC_NNN`, validação software cl. 7.11 perfil-aware.

Ordem entrega valor regulatório (Fatia 3 fecha o gate). Cada fatia passa pelo
ritual completo (auditores essenciais + roteados, MÉDIO+ bloqueia — INV-RITUAL-001).

## 11. Gates

- **GATE-CAL-PROC-VIGENTE-PREDICATE** — `procedimento_vigente_para` real plugado
  em `configurar_calibracao` + suíte M4 reverde + teste do caminho bloqueado
  (ADR-0066). **Gate central deste módulo.**
- **GATE-PROC-DRILL-LOCAL** — drill PG real (RLS isolamento cross-tenant +
  triggers WORM + UNIQUE + `vigente_em` bloqueia faixa sem procedimento só RBC).
- **GATE-PROC-ANEXO-HASH** — integridade do anexo PDF (hash server-side
  versionado; alteração de anexo PUBLICADO bloqueada).
- **GATE-PROC-VALIDACAO-7.11** — validação software cl. 7.11 do gate de
  resolução (ADR-0025; dado que toca método/faixa é metrology-affecting) —
  parecer RBC credenciado é pré-produção.
- **GATE-PROC-METODO-VALIDADO** — qualificação de método não-normalizado cl.
  7.2.2 (INV-PROC-010): bloqueio duro "perfil A + método NÃO-NORMALIZADO sem
  `registro_validacao_id` → não publica" entra em vigor quando
  `licencas-acreditacoes` existir; **fail-open lazy** no MVP (campo + aviso,
  paralelo ADR-0066). Emenda US-CAL-016.

## 12. Critérios de validação (drill `validar_procedimentos_calibracao`)

Estrutural (sem PG): entidades + invariantes puras + máquina de estados
(RASCUNHO/PUBLICADO/REVOGADO) + porta `vigente_em()` declarada. PG real
(GATE-PROC-DRILL-LOCAL): UNIQUE tenant-scoped + RLS isolamento cross-tenant +
trigger WORM (DELETE bloqueado, UPDATE de campo imutável bloqueado) +
`procedimento_vigente_para` bloqueia grandeza/faixa sem procedimento só em RBC +
snapshot imutável na superseção.

## 13. Dependências e ordem na Wave A

`procedimentos-calibracao` depende de:
- `metrologia/escopos-cmc` (M6 fechado) — módulo-espelho (mesmo molde); a ordem
  composta escopo→procedimento roda na mesma transição de configuração.
- Calibracao (M4) — campo de 1ª classe `faixa_calibrada_declarada` (peça #1
  SAN-FAIXA-CALIBRADA, já entregue) + `procedimento_versao_snapshot`
  (CalibracaoSnapshot — já existe desde M4 P4).
- `responsavel_tecnico` — RT publica procedimento (perfil A); retrofit ADR-0022
  v2 é Wave A.

Habilita / fecha: **GATE-CAL-PROC-VIGENTE-PREDICATE** (irmão do
GATE-CAL-CMC-PREDICATE fechado pelo M6).

## 14. Próximo passo do ritual

`plan` (M7-procedimentos-calibracao/plan.md) com revisão dos subagentes — em
especial `consultor-rbc-iso17025` (aplicabilidade cl. 7.2.1 por perfil B/C/D,
granularidade código×grandeza×faixa, superseção) e `tech-lead-saas-regulado`
(geometria de faixa compartilhada A, hash de anexo server-side F, eventos E,
superseção automática G, molde-espelho M6). **Sem código antes do plan aprovado.**
