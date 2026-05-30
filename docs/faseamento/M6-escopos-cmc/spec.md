---
owner: roldao
revisado-em: 2026-05-29
status: draft
fase: M6-escopos-cmc
dominio: metrologia
modulo: escopos-cmc
ritual: specify
versao: 2
fontes:
  - docs/faseamento/M6-escopos-cmc/dossie-requisitos.md (workflow entender-escopos-cmc, 80 achados)
  - docs/faseamento/M6-escopos-cmc/reviews-consolidado.md (tech-lead + RBC, 2026-05-29)
  - docs/dominios/metrologia/modulos/calibracao/prd.md (stable — US-CAL-015, AC-CAL-001-2/002-2/015-1/2)
  - src/application/metrologia/calibracao/queries/escopo.py (EscopoCMCSnapshot — contrato cravado)
  - src/infrastructure/calibracao/predicates_calibracao.py (cmc_cobre — DEPRECADO por ADR-0073)
adrs:
  - 0002 (RLS) / 0007 (codegen) / 0022 v2 (RT competência) / 0025 v2 (validação software)
  - 0029 (canonicalização) / 0030 (vigência) / 0031 (soft-delete B) / 0040 (entidade separada)
  - 0064 (HMAC 25a) / 0066 (fail-open lazy + emenda 2026-05-29) / 0067 (perfil) / 0072 (path aninhado)
  - 0014 (snapshot acreditação) / 0059 (LLMProvider — pode ser ativada por extração PDF)
  - 0073 (validação no use case, não permission layer) / 0074 (cobertura RBC tridimensional)
  - 0075 (capacidade interna não-acreditada ≠ CMC)
---

> **v2 (2026-05-29):** spec atualizada pós-revisões tech-lead + RBC. Mudanças
> principais: **INV-ECMC-009** (`U ≥ CMC` ILAC-P14 §5.5 — §6), validação no use case
> (ADR-0073), cobertura tridimensional + 2ª porta `cmc_para()` (ADR-0074), separação
> terminológica A vs B/C/D (ADR-0075 — §5), fatiamento em **5 fatias** (§10), 2 gates
> novos (§11). Deltas completos em `reviews-consolidado.md` + `plan.md` §15.

# Spec de faseamento — M6 `metrologia/escopos-cmc` (2º módulo Wave A)

> **Ritual (memória `feedback_ritual_orquestrador`):** este é o passo `/specify`.
> Próximos passos OBRIGATÓRIOS antes de qualquer código: `plan` revisado pelos
> subagentes (`tech-lead-saas-regulado`, `consultor-rbc-iso17025`; `advogado` +
> `corretora` se a extração PDF/IA acender risco) → `tasks` → `implement` →
> auditores Família 5 roteados por risco (INV-RITUAL-003). **Nada de código antes
> do plan revisado.**
>
> **Por que este módulo importa:** destrava `GATE-CAL-CMC-PREDICATE` (origem
> PROD-CAL-01). Hoje o predicate `cmc_cobre` é STUB fail-open (retorna sempre
> `True`), deixando passar emissão RBC fora do escopo acreditado. `escopos-cmc`
> torna o bloqueio real (412 `EscopoNaoCobreFaixa`), satisfazendo a métrica de
> produto "Zero calibrações RBC emitidas fora do escopo (100%)" e o diferencial
> competitivo vs Calibre.Software. É o primeiro dos dois módulos que ADR-0066
> deixou em fail-open lazy (o irmão é `procedimentos-calibracao`).

## 1. Objetivo

Construir o cadastro, versionamento e validação do **Escopo de Acreditação
CGCRE** (perfil A) e da **capacidade declarada** (perfis B/C/D) de um tenant: o
catálogo de **grandezas, faixas, métodos e CMC** (Capacidade de Medição e
Calibração — a menor incerteza declarável em rotina por par grandeza/faixa,
NIT-DICLA-031) que define o que pode sair com selo RBC. Transforma o contrato já
cravado `EscopoCMCSnapshot` (query M4, sem persistência) em entidade Django
persistida, ligando o predicate `cmc_cobre` à leitura real e tornando o bloqueio
efetivo. Perfil-aware (ADR-0067), vigência canônica (ADR-0030), WORM Padrão B
(ADR-0031), path aninhado (ADR-0072). **Entrada por extração automática do PDF da
CGCRE com conferência humana obrigatória** (decisão Roldão 2026-05-29).

## 2. Escopo (deriva do dossiê §2/§8 — não duplicar AC aqui)

- CRUD de `EscopoCMC` (colunas tipadas — não JSONField — p/ índice grandeza+range).
- Versionamento: revisão preserva versão anterior (AC-CAL-015-2 — auditoria retroativa).
- Revogação WORM Padrão B (`revogado_em` + `motivo_revogacao`; DELETE bloqueado por trigger).
- `cmc_cobre` real fail-CLOSED: RBC (perfil A) fora do escopo → 412 `EscopoNaoCobreFaixa` na **configuração**; aviso degradante NÃO-RBC na **recepção**.
- Capacidade interna perfis B/C/D (`rbc_acreditado=false` **forçado** — anti-fraude).
- **Extração do PDF da CGCRE → tela de conferência humana → persistência** (nunca auto-persiste).
- Snapshot `EscopoUsado` congelado na configuração da calibração (alimenta `escopos_acreditados_vigentes_no_momento` JSONB — ADR-0014/Sprint 4 SAN-PERFIL).
- Porta `repository.escopo_repo.cobre()` consumida pelo predicate `cmc_cobre`.
- Rótulos que o cliente lê: **"CMC (menor incerteza declarada)"** + **"Nº do escopo CGCRE"** (decisões Roldão).

## 3. Non-goals (explícito)

NÃO: o "como medir" / procedimento técnico vigente (é `procedimentos-calibracao`
— AC-CAL-016 + 412 `ProcedimentoVigenteAusente`); gerência da acreditação/
credenciamento CGCRE da empresa (é `Licenças e Acreditações` — US-LIC; aqui só
FK `documento_regulatorio_id`); quem assina dentro do escopo (é
`responsavel_tecnico`/RTCompetencia); padrão físico/Shewhart/PT (é
`metrologia/padroes`); emissão de certificado (é `certificados`); PDF/A de
relatório; substituir SGQ. **Extração PDF NÃO dispensa conferência humana** —
nunca persistir escopo regulatório auto-extraído sem confirmação.

## 4. Entidade + agregado (contrato cravado em EscopoCMCSnapshot)

**Agregado raiz `EscopoCMC`** (model Django espelha 1:1 o `EscopoCMCSnapshot` de
`escopo.py:22-52`, com colunas tipadas). Campos canônicos: `grandeza`,
`faixa_min/max`, `unidade`, `cmc_valor` (= o CMC), `cmc_unidade`,
`procedimento_id` (FK→ProcedimentoCalibracao, NULL hoje — §9 F),
`rbc_acreditado`, `documento_regulatorio_id` (FK→Licenças, INV-012),
`numero_escopo_cgcre` (NOVO — decisão K), `versao` + `vigente_a_partir`
(AC-CAL-015-2). Vigência canônica ADR-0030 (`vigencia_inicio` NOT NULL /
`vigencia_fim` NULL=aberta / `revogado_em` / `motivo_revogacao` ≥10 chars).
Soft-delete Padrão B WORM (ADR-0031 / INV-SOFT-002 / trigger PG). `revision`
(CAS) + `correlation_id` (molde M5).

**Estado de extração (decisão N):** `EscopoCMC` ganha um estágio de ciclo de vida
`RASCUNHO_EXTRAIDO` → `CONFIRMADO` (vigente). Só `CONFIRMADO` entra na consulta
`cobre()`. Rascunho extraído do PDF é editável; ao confirmar, vira vigente e
imutável (Padrão B). Modelar como sub-entidade `EscopoExtraido` (staging) vs flag
no agregado = decisão tech-lead no /plan (§9 R).

VOs reusados de `src/domain/metrologia/value_objects.py` (`Grandeza`,
`FaixaMedicao`, `IncertezaExpandida`). **Não recriar.** Domínio puro sem Django
(ADR-0007).

## 5. User Stories → mapa de implementação (AC detalhado no /plan + retrofit PRD)

| US | Tema | Bloqueia / herda | Perfil |
|----|------|------------------|--------|
| US-ECMC-001 | Cadastrar escopo/capacidade (form base, editável) | herda US-CAL-015 | A=RBC / B/C/D=interno |
| US-ECMC-002 | Revisar escopo (versão preservada) | AC-CAL-015-2 | todos |
| US-ECMC-003 | Revogar escopo (WORM Padrão B) | ADR-0031 | todos |
| US-ECMC-004 | Validar cobertura na configuração (`cmc_cobre` real → 412) | AC-CAL-002-2/015-1 + GATE-CAL-CMC-PREDICATE | **A (RBC)** |
| US-ECMC-005 | Aviso degradante na recepção (escopo não cobre → NÃO-RBC) | AC-CAL-001-2 | **A** |
| US-ECMC-006 | Importar escopo do PDF CGCRE + conferência humana | decisão N (Roldão) | **A** (escopo CGCRE) |
| US-ECMC-007 | Declarar capacidade interna (`rbc_acreditado=false` forçado) | decisão O (Roldão) | **B/C/D** |
| US-ECMC-008 | Snapshot `EscopoUsado` congelado na calibração | ADR-0014 / §9 J | **A** |

## 6. Invariantes (a cravar em REGRAS-INEGOCIÁVEIS no `implement`)

- **INV-ECMC-001** — UNIQUE tenant-scoped da chave natural do escopo (provisório `(tenant_id, grandeza, faixa_min, faixa_max, procedimento_id, versao)` — granularidade método×escopo a confirmar com RBC, §9 F/M).
- **INV-ECMC-002** — `rbc_acreditado=true` exige `tenant_perfil_e(["A"])` (ADR-0067). Perfis B/C/D: `rbc_acreditado` **forçado false** server-side (anti-fraude INV-015 — não-A nunca se passa por RBC). Paralelo a INV-PAD-005.
- **INV-ECMC-003** — escopo CONFIRMADO é WORM Padrão B: muta só via revogação (`revogado_em`+`motivo_revogacao`); DELETE bloqueado por trigger; revisão cria nova `versao` preservando a anterior (AC-CAL-015-2).
- **INV-ECMC-004** — `cmc_cobre` fail-CLOSED real: calibração RBC (perfil A) com grandeza+faixa fora de escopo CONFIRMADO vigente → DENY `cmc_fora_do_escopo` → view 412 `EscopoNaoCobreFaixa`. Substitui o fail-open ADR-0066. (NÃO replicar fail-open — escopo é barreira de fraude.)
- **INV-ECMC-005** — semântica de cobertura por **contenção total** (`faixa_solicitada ⊆ faixa_escopo`) para o bloqueio RBC (interseção parcial deixaria passar fora do CMC = fraude) — **provisório, decisão RBC §9 A**.
- **INV-ECMC-006** — vigência canônica ADR-0030 (tz-aware, CHECK INV-VIG-001..004).
- **INV-ECMC-007** — escopo extraído de PDF nunca auto-persiste vigente: estado `RASCUNHO_EXTRAIDO` exige confirmação humana (ação `escopos_cmc.confirmar_extraido`) para virar `CONFIRMADO`. Trilha de auditoria registra extração + confirmação (quem/quando).
- **INV-ECMC-008** — snapshot `EscopoUsado` congelado na configuração (VO WORM + canonicalização ADR-0029) alimenta `escopos_acreditados_vigentes_no_momento` (ADR-0014/INV-INT-003). **v2:** conteúdo mínimo probatório (RBC-NC-06) = `versao` do escopo + CMC-da-época com forma (abs vs `a+b·X`) + comparação U×CMC + RT competente da época + `perfil_no_evento`.
- **INV-ECMC-009 (v2 — ADR-0074):** calibração RBC (perfil A) com incerteza expandida reportada (k=2, ~95,45%) MENOR que a CMC vigente do escopo para a grandeza+faixa (normalizadas à mesma unidade/forma) → bloqueia emissão (412 `IncertezaAbaixoDoCMC`). ILAC-P14:09/2020 §5.5 — NC nº 1 de auditoria CGCRE. Avaliada na EMISSÃO (não na config) via 2ª porta `cmc_para()`. Múltiplos métodos por faixa → usa a MENOR CMC vigente (NIT-DICLA-012). `U` sempre do orçamento de incerteza, nunca `U=CMC` cego (RBC-NC-07).
- **Reusadas:** INV-CAL-CMC-001 (vínculo RBC↔escopo `escopo_id NOT NULL`),
  INV-015, INV-CAL-RAST-002, INV-VIG-001..004, INV-SOFT-001/002,
  INV-TENANT-001..004, INV-TENANT-PERFIL-001/003/004, INV-DOC-CANON-001,
  INV-HMAC-001..005 (se eventos hash-chain — §9 S).

## 7. Integração com `cmc_cobre` (porta consumida pelo predicate)

Drop-in já escrito (`predicates_calibracao.py:170-178`): importa
`escopo_repo.cobre(tenant_id, grandeza, faixa_min, faixa_max, data) -> bool`.
**Contrato exato a honrar:**
- `escopo_repo` exposto como **singleton module-level** em
  `src/infrastructure/metrologia/escopos_cmc/repository.py` (o drop-in exige o
  símbolo — §9 Q).
- `cobre()` filtra `tenant_id` EXPLÍCITO além da RLS (defesa em profundidade,
  molde M5); só CONFIRMADO + vigente em `data`; cobertura por contenção total
  (INV-ECMC-005); preserva o **short-circuit perfil A** (não-A já retorna
  `(True,"")` antes de chamar a porta).
- Resolver o choque anti-PII do provider (`_validar_resource_sem_pii` rejeita
  chaves de topo `grandeza/faixa_*/data`): **aninhar sob `resource={'escopo':
  {...}}`** (`escopo` já está na allowlist — §9 C) + adaptar `cmc_cobre`.
- A view injeta grandeza/faixa/data **server-side** (não do payload — SEG-CAL-10),
  derivadas de um campo de 1ª classe na Calibracao (§9 D).
- **GATE-CAL-CMC-PREDICATE:** wire-in real + testes NOVOS do caminho bloqueado +
  teste de transição fail-open→fail-closed sem quebrar legado (TST-005) + suíte
  M4 chave (629) reverde.

## 8. Extração do PDF da CGCRE (decisão N — fatia própria)

Escopos CGCRE são documentos **públicos** (inmetro.gov.br). Fluxo:
upload PDF → motor de extração de tabela → preenche rascunho `RASCUNHO_EXTRAIDO`
→ **tela de conferência humana** (lab edita/corrige) → `confirmar_extraido` →
`CONFIRMADO`. **Nunca persiste vigente sem confirmação (INV-ECMC-007).**

**Decisão de arquitetura para o /plan (GATE-ECMC-EXTRACT-ENGINE — tech-lead):**
motor **determinístico** (leitor de tabela tipo pdfplumber/camelot — contido,
sem dependência externa, frágil a layout) **vs IA** (extração por LLM — robusto a
layout, mas **ativa ADR-0059 LLMProvider reservada** + INV-LLM-001..010 + custo
por chamada + porta `LLMProvider`). Validação cl. 7.11 (ADR-0025) aplica se a
extração tocar dado metrológico (cmc_valor/faixa). **Recomendação inicial:
determinístico no MVP** (dogfooding Balanças, layout CGCRE estável) com a
conferência humana cobrindo falhas de extração; IA só se o tech-lead/RBC julgar
o parser frágil demais — e aí volta como decisão de custo/privacidade ao Roldão.

## 9. Questões abertas → roteamento /plan (rec. no dossiê §9)

| Q | Tema | Decisor | Recomendação |
|---|------|---------|--------------|
| A | cobertura: contenção total vs interseção | RBC | contenção total |
| B | faixa vs `U_serviço < CMC` | RBC | MVP só faixa; U<CMC INV adicional se RBC exigir |
| C | shape resource anti-PII | tech-lead | aninhar sob `escopo` |
| D | fonte server-side de grandeza/faixa/data | tech-lead+RBC | campo de 1ª classe na Calibracao |
| F | granularidade escopo×método 1:1 vs N | RBC+tech-lead | 1 método/linha; RTCompetencia fonte de verdade |
| G | `RTCompetenciaParaEscopo` nova vs reuso | RBC+tech-lead | reuso; sem RT vivo → bloqueia uso RBC |
| H | WORM Padrão B vs C | tech-lead | Padrão B (apontado pelos ADRs) |
| I | orquestração validação composta (escopo×procedimento) | tech-lead+produto | ordem escopo→procedimento, 1ª falha |
| J | snapshot `EscopoUsado` WORM vs só FK | produto/RBC | congelar VO WORM (ADR-0014) |
| M | múltiplos métodos por linha | RBC | cada (grandeza,faixa,método) = linha |
| P | slug físico `escopos_cmc` | tech-lead | confirmar (cravado no drop-in) |
| Q | singleton `escopo_repo` | tech-lead | singleton module-level |
| R | staging extração: sub-entidade vs flag | tech-lead | a decidir no /plan |
| S | eventos hash-chain dedicados vs só audit trail | tech-lead | a decidir no /plan |

**Decididas pelo Roldão (2026-05-29):** L = "CMC (menor incerteza declarada)";
N = extração automática do PDF + conferência humana; O = todos os perfis declaram
(A=RBC, B/C/D=capacidade interna `rbc_acreditado=false`, bloqueio 412 só RBC);
K = capturar `numero_escopo_cgcre` rótulo "Nº do escopo CGCRE".

## 10. Faseamento proposto — 4 fatias (INV-RITUAL-002; detalhar no `tasks`)

- **Fatia 1a — Domínio puro (v2 — split TL-C-09):** entities/enums/repository
  Protocols + `cobertura.py` (contenção total + comparação U≥CMC pura, Decimal) +
  invariantes puras. Testes de domínio.
- **Fatia 1b — Schema + persistência (v2):** model colunas tipadas + UNIQUE
  tenant-scoped + migrations irmãs (initial → RLS v2 → triggers WORM Padrão B →
  grants → seed authz) + repositório/query_service `cobre()`+`cmc_para()` (funções de
  módulo, NÃO singleton — TL-C-04) + CAS + drill estrutural `validar_escopos_cmc`.
- **Fatia 2 — Use cases + API + versionamento (P5-P7):** `cadastrar_escopo` /
  `revisar_escopo` (versão preservada) / `revogar_escopo` / `declarar_capacidade`
  (B/C/D); ViewSet REST + serializers + idempotência (IDEMP-001) + urls plugadas
  na **raiz** (lição T-CAL-124); vínculo `documento_regulatorio_id`.
- **Fatia 3 — Wire-in do predicate + GATE-CAL-CMC-PREDICATE (P8):** `cmc_cobre`
  real (drop-in), shape resource anti-PII (§9 C) + injeção server-side (§9 D),
  teste transição fail-open→fail-closed (TST-005) sem quebrar legado, snapshot
  `EscopoUsado` (ADR-0014), suíte M4 reverde, INV-ECMC-* em REGRAS +
  `TestINV_ECMC_NNN`, validação software cl. 7.11 perfil-aware.
- **Fatia 4 — Extração PDF + conferência humana (P9):** upload, motor de extração
  (GATE-ECMC-EXTRACT-ENGINE), estado `RASCUNHO_EXTRAIDO`→`CONFIRMADO`
  (INV-ECMC-007), tela de conferência, validação cl. 7.11 do motor.

Ordem entrega valor regulatório primeiro (Fatia 3 fecha o gate) e a conveniência
de extração por último. Cada fatia passa pelo ritual completo (auditores
essenciais + roteados, MÉDIO+ bloqueia — INV-RITUAL-001).

## 11. Gates

- **GATE-CAL-CMC-PREDICATE** — `cmc_cobre` real plugado em `configurar_calibracao`
  + recepção + suíte M4 reverde + teste do caminho bloqueado (ADR-0066). **Gate
  central deste módulo.**
- **GATE-ECMC-DRILL-LOCAL** — drill PG real (RLS isolamento cross-tenant +
  triggers WORM + UNIQUE + perfil A bloqueia RBC em B/C/D).
- **GATE-ECMC-EXTRACT-ENGINE** — decisão tech-lead motor de extração
  (determinístico vs IA/ADR-0059) + validação cl. 7.11 do motor.
- **GATE-ECMC-COBERTURA-RBC** — semântica de cobertura (contenção total + U≥CMC +
  menor-CMC-por-faixa) revisada por `consultor-rbc-iso17025` (ADR-0074).
- **GATE-ECMC-U-MAIOR-CMC (v2)** — consumo da 2ª porta `cmc_para()` no ponto de
  emissão/aprovação onde o U é final (M4 `aprovar_2a_conferencia` ou módulo
  `certificados` Wave A). Porta entregue no M6; ponto de consumo investigado no
  `/tasks` (regra #0) e fechado onde o U existir.
- **GATE-ECMC-RT-VINCULO (v2)** — vínculo RT↔escopo fail-open lazy no MVP (paralelo
  ADR-0063) até retrofit ADR-0022 v2; bloqueio real (escopo sem RT competente vivo →
  DENY uso RBC) obrigatório antes do 1º tenant RBC externo. Fail-open documentado +
  teste nomeado (TL-C-05 / RBC-NC-04).

## 12. Critérios de validação (drill `validar_escopos_cmc`)

Estrutural (sem PG): entidades + invariantes puras + máquina de estados
(RASCUNHO_EXTRAIDO/CONFIRMADO/REVOGADO) + porta `cobre()` declarada. PG real
(GATE-ECMC-DRILL-LOCAL): UNIQUE tenant-scoped + RLS isolamento cross-tenant +
trigger WORM (DELETE bloqueado, UPDATE de campo imutável bloqueado) + perfil A
declara RBC e B/C/D forçado `rbc_acreditado=false` + `cmc_cobre` bloqueia faixa
fora do escopo só em RBC + extração nunca persiste vigente sem confirmação.

## 13. Dependências e ordem na Wave A

`escopos-cmc` depende de:
- `metrologia/padroes` (M5 fechado) — escopo referencia padrões (FK opcional).
- `responsavel_tecnico`/RTCompetencia (existe; retrofit ADR-0022 v2 é Wave A — §9 G).
- `Licenças e Acreditações` (FK `documento_regulatorio_id`; módulo Wave A — vínculo
  NULLABLE até existir, não bloqueia).
- Calibracao (M4) — campo de 1ª classe de faixa solicitada para o resource (§9 D).

Habilita / fecha: **GATE-CAL-CMC-PREDICATE** (o irmão GATE-CAL-PROC-VIGENTE-PREDICATE
fica para `procedimentos-calibracao`).

## 14. Próximo passo do ritual

`plan` (M6-escopos-cmc/plan.md) com revisão dos subagentes — em especial
`consultor-rbc-iso17025` (semântica de cobertura A/B, granularidade método×escopo
F/M, perfil-aware O, RT competente G) e `tech-lead-saas-regulado` (shape resource
C, fonte server-side D, motor de extração N/ADR-0059, staging R, eventos S,
singleton Q). `advogado` + `corretora` só se a extração por IA acender risco.
**Sem código antes do plan aprovado.**
