---
owner: roldao
revisado-em: 2026-05-29
status: draft
fase: M6-escopos-cmc
dominio: metrologia
modulo: escopos-cmc
ritual: fase-0-entendimento
versao: 1.0
---

# Dossiê de requisitos — metrologia/escopos-cmc

> **Status:** dossiê pré-spec. Base de evidências para escrever `spec.md` no ritual Spec Kit (`/specify → /plan revisado pelos subagentes → /tasks → /implement → auditores Família 5 roteados por risco`). **Todos os requisitos abaixo derivam dos 80 achados dos 5 leitores paralelos + 24 questões abertas (workflow `entender-escopos-cmc`, 2026-05-29) — nada foi inventado.** Onde um achado não cobre uma decisão, ela aparece na §9 como questão de produto, nunca como requisito assumido.
>
> **Por que este módulo importa:** destrava `GATE-CAL-CMC-PREDICATE` (origem PROD-CAL-01). Hoje o predicate `cmc_cobre` é STUB fail-open e retorna sempre `True`, deixando passar emissão RBC fora do escopo acreditado. O módulo `escopos-cmc` torna o bloqueio real (412 `EscopoNaoCobreFaixa`), satisfazendo a métrica de produto "Zero calibrações RBC emitidas fora do escopo (target 100%)". Diferencial competitivo declarado vs Calibre.Software.

---

## 1. O que o módulo é

O `metrologia/escopos-cmc` persiste, versiona e valida o **Escopo de Acreditação CGCRE** de um laboratório acreditado: o catálogo oficial das **grandezas, faixas, métodos e CMC** (Capacidade de Medição e Calibração — a menor incerteza que o lab consegue declarar em rotina por par grandeza/faixa) que define o que pode sair com selo RBC. CMC é o limite inferior de incerteza declarado à CGCRE (NIT-DICLA-031). O contrato de dados já existe como dataclass de leitura `EscopoCMCSnapshot` no query service do M4 (sem migration nem repositório); este módulo o transforma em entidade Django persistida com seu próprio repositório, ligando o predicate `cmc_cobre` (hoje fail-open lazy por ADR-0066) à leitura real da entidade `EscopoCMC` vigente, de modo que calibração RBC fora do escopo passe a ser **bloqueada** (412 `EscopoNaoCobreFaixa`). É módulo de domínio metrológico separado (molde ADR-0040), perfil-A-cêntrico, com vigência temporal canônica (ADR-0030) e soft-delete WORM (ADR-0031).

---

## 2. User Stories e ACs herdados (PRD calibração + ADR-0066)

| US / AC | Texto (resumido) | Comportamento exigido | Fonte |
|---|---|---|---|
| **US-CAL-015** | Escopo de acreditação + CMC. Admin tenant cadastra escopo CGCRE + CMC por grandeza/faixa para bloquear emissões fora do escopo RBC. **Coração do módulo.** INV-002, INV-012, INV-CAL-WORM-001. | US central — `gerenciarEscopoCMC`/`cadastrarEscopo`. | prd.md:266-274 |
| **AC-CAL-015-1** | Escopo cadastrado (grandeza, faixa, CMC, método); calibração configurada valida cobertura. Hoje fail-open `True`. | AC binário central: tornar `cmc_cobre` real. | prd.md:271 |
| **AC-CAL-015-2** | Revisão do escopo CGCRE preserva versão anterior (`versao` + `vigente_a_partir`; não apaga — auditoria retroativa). | Entidade temporal versionada. | prd.md:272 |
| **AC-CAL-001-2** | Escopo não cobre instrumento na **recepção** → **avisa e segue NÃO-RBC** (degrada). | Aviso degradante na recepção (≠ bloqueio). | prd.md:96 |
| **AC-CAL-002-2** | Faixa fora do escopo CMC na **configuração** → **bloqueia 412 `EscopoNaoCobreFaixa`** citando CMC oficial. | Bloqueio duro; código canônico do módulo. | prd.md:108-110 |
| **AC-CAL-016-1/2/3** | `procedimento_vigente_para`. **Pertence a procedimentos-calibracao**, não a escopos-cmc (mesmo gatilho, módulo diferente). | NÃO é deste módulo (§7). | prd.md:282-284 |
| **URS-CAL-002 / PQ-CAL-004** | "configuração persiste; validação CMC bloqueia fora de escopo" / "Zero cert RBC fora do escopo". | Validação software cl. 7.11 só plena quando bloqueio CMC real. | validacao-software.md:170,212 |

**Comando de escrita central:** `cadastrarEscopo` — origem UI admin; pré-condição: Acreditação vinculada (módulo Licenças); pós-condição: Escopo vigente.

---

## 3. Requisitos vinculantes de ADRs e REGRAS

| ID | Origem | Requisito |
|---|---|---|
| **ADR-0066** | cmc_cobre fail-open lazy | Criar módulo `escopos_cmc` E invocar `cmc_cobre` em `configurar_calibracao` + `criar_calibracao`; satisfaz `GATE-CAL-CMC-PREDICATE`. 6 ACs saem do fail-open. |
| **ADR-0072** | path infra aninhado | `src/infrastructure/metrologia/escopos_cmc/` (aninhado). **PROIBIDO achatar.** |
| **ADR-0040** | molde entidade separada | Molde de `PadraoMetrologico`: domínio próprio + migration + RLS + QueryService cross-módulo fail-CLOSED + INVs próprias + VOs reusados. NÃO reusar Equipamento. |
| **ADR-0030** | vigência canônica | VO `JanelaVigencia` + `vigencia_inicio`(NOT NULL) / `vigencia_fim`(NULL=aberta) / `revogado_em` / `motivo_revogacao`(≥10 chars). CHECK INV-VIG-001..004; tz-aware. |
| **ADR-0031** | soft-delete Padrão B | Escopo = estado regulatório auditável → **Padrão B WORM** (`revogado_em`+`motivo_revogacao`, nunca DELETE físico). Hook `soft-delete-padrao-check`. |
| **ADR-0025 v2** | validação software cl. 7.11 | Perfil A: dossiê URS/IQ/OQ/PQ + 2º caminho; B/C leve; D dispensado. `metrology-affecting:` em migration metrológica; replay determinístico. |
| **ADR-0067 / INV-TENANT-PERFIL** | perfil regulatório | Gate perfil A via `tenant_perfil_e(['A'])` fail-closed. **Perfil NUNCA do payload.** Evento WORM → `perfil_no_evento CHAR(1)`. Anti-fraude L6. |
| **ADR-0002 / INV-TENANT-001..004** | multi-tenancy RLS | `tenant_id NOT NULL` + ENABLE/FORCE RLS + CREATE POLICY mesma migration. `app_user` NOBYPASSRLS. UNIQUE tenant-scoped. RLS v2 (4 policies). |
| **ADR-0064** | hash-chain HMAC | Se houver eventos: `publicar_evento` + hash-chain HMAC versionado. PII de funcionário como `*_id_hash`. |
| **ADR-0029 / INV-DOC-CANON-001** | texto probatório | Snapshot/justificativa congelados seguem `<<<CORPO INICIO/FIM>>>`, UTF-8 sem BOM, LF, NFC, SHA-256 determinístico. |
| **ADR-0022 v2** | RT por método+faixa | `RTCompetenciaParaEscopo` nomeado (ADR-0066). Retrofit T-RT-V2 ainda Wave A — model atual `RTCompetencia` só tem grandeza (§9 G). |
| **INV-015 / INV-PAD-005 / INV-CAL-RAST-002** | anti-fraude + rastreabilidade | `rbc_acreditado=true` só perfil A. RBC exige `PadraoUsado.vinculacao_si_tipo` rastreável; INTERNO_DECLARADO proibido. |
| **INV-CAL-CMC-001** | vínculo RBC↔escopo | `tipo_acreditacao=RBC` exige `cmc_cobre`=true + `escopo_id NOT NULL`. Hook `cmc-binding-check.sh`. |
| **ADR-0014 / INV-INT-003** | snapshot acreditação | Certificado congela escopo vigente. Coluna `escopos_acreditados_vigentes_no_momento JSONB` em `evento_de_calibracao` já existe (SAN-PERFIL Sprint 4) — **módulo alimenta**. |
| **INV-RITUAL-001/002/003** | ritual | MÉDIO+ bloqueia; fatias ~20-25 tarefas; 6 auditores essenciais + roteados. |
| **TST-004 / TST-005** | testes | ≥1 teste por INV crítico nomeado; teste explícito transição fail-open→fail-closed sem quebrar legado. |

---

## 4. Entidade de domínio EscopoCMC

Contrato já cravado como `EscopoCMCSnapshot` (escopo.py:22-52). Model Django espelha 1:1 com **colunas TIPADAS** (não JSONField — índices PG de grandeza + range).

| Campo | Tipo | Nota |
|---|---|---|
| `id` | UUID | molde migrations M5 |
| `tenant_id` | FK PROTECT NOT NULL | RLS |
| `grandeza` | CharField (lowercase) | filtro `grandeza__iexact` |
| `faixa_min` / `faixa_max` | DecimalField | range numérico |
| `unidade` | CharField | |
| `cmc_valor` | DecimalField | **o CMC** = menor incerteza alcançável |
| `cmc_unidade` | CharField | |
| `procedimento_id` | UUID NULL (FK→ProcedimentoCalibracao) | §9 F |
| `rbc_acreditado` | BooleanField | true exige match estrito; só perfil A |
| `vigencia_inicio` | timestamptz NOT NULL | ADR-0030 |
| `vigencia_fim` | timestamptz NULL | ADR-0030 |
| `revogado_em` | timestamptz NULL | ADR-0031 (gap no snapshot atual) |
| `motivo_revogacao` | str (≥10 chars) | CHECK INV-VIG-002 |
| `versao` + `vigente_a_partir` | int + datetime | AC-CAL-015-2 |
| `documento_regulatorio_id` | FK→Licenças | INV-012 |
| `revision` | int CAS | molde M5 |
| `correlation_id` | UUID | molde M5 |

**Campos novos sob decisão (§9):** nº oficial do escopo CGCRE (K), vínculo RT (G), VO `EscopoUsado` congelado (J).

---

## 5. Integração com `cmc_cobre`

- **Registro ABAC** (não chamada direta): `register_predicate('cmc_cobre', cmc_cobre, actions={'calibracao.configurar','calibracao.iniciar_leituras'})` em `calibracao/apps.py`. View chama `AuthorizationProvider.can('calibracao.configurar', resource={...})` antes do use case.
- **Drop-in já escrito** (predicates_calibracao.py:170-178):
  ```python
  from src.infrastructure.metrologia.escopos_cmc.repository import escopo_repo
  if not escopo_repo.cobre(tenant_id, grandeza, faixa_min, faixa_max, data):
      return False, "cmc_fora_do_escopo"
  ```
- **Short-circuit perfil:** só consulta quando `obter_perfil_tenant_corrente() == 'A'`. `escopo_repo.cobre()` deve preservar.
- **Contrato:** `cobre(tenant_id, grandeza, faixa_min, faixa_max, data) -> bool`. Filtro `tenant_id` EXPLÍCITO além da RLS (defesa em profundidade).
- **Bloqueios a resolver:** (1) `_validar_resource_sem_pii` rejeita chaves de topo `grandeza/faixa_min/faixa_max/data` → §9 C (aninhar sob `escopo`); (2) view precisa injetar grandeza/faixa/data **server-side** → §9 D.

---

## 6. Convenções do molde M5 a replicar

**Pastas (3 árvores aninhadas sob `metrologia/escopos_cmc/` — ADR-0072):** `src/domain/` (puro, sem Django: entities/enums/repository Protocols), `src/application/` (1 arquivo por use case + Input + executar), `src/infrastructure/` (models, migrations, repositories, mappers, query_service, serializers, views, urls, apps, management/commands).

**Frontmatter:** owner, revisado-em, status, fase, dominio, modulo, ritual, versao. spec.md + `fontes:`/`adrs:`; plan.md + `depende-de`/`reviews-concluidas`/`consolidacao`.

**Migrations irmãs (ordem fixa):** 0001 initial (CreateModel + UNIQUE + Index, `# rls-policy: external 0002`) → 0002 RLS v2 (ENABLE+FORCE + 4 policies) → 0003 triggers WORM (Padrão B, BEFORE DELETE RAISE + BEFORE UPDATE imutáveis) → 0004 grants app_user → 0005 seed authz (idempotente, `atomic=False`, ações `escopos_cmc.<verbo>`).

**Hooks:** padrão `.claude/hooks/<nome>.sh` + perl JSON::PP + registro em `settings.json` + casos no `_test-runner.sh`. Os 4 hooks M5 NÃO se aplicam (entidade física). Reusar `cmc-binding-check.sh`. Hooks novos cobrem vínculo escopo↔RBC + transição fail-open→fail-closed.

**Tarefas:** prefixo **`T-ECMC-NNN`** por fase em faixas. Seções `## GATEs`, `## Pendências externas`, `## Próximo passo`. Verificar com `--no-cov --reuse-db`.

**Reuso (não reinventar):** `publicar_evento`+HMAC, `tenant_perfil_e`, CAS `atualizar_com_lock`, RLS v2, VOs metrológicos, paginação F-C3 (teto 200), canonicalização ADR-0029, idempotência, `derivar_user_id_hash`. Drill `validar_escopos_cmc` estrutural espelha `validar_m5_padroes`. urls plugadas na raiz (lição T-CAL-124).

---

## 7. Fronteira escopos-cmc vs procedimentos-calibracao

| NÃO é de escopos-cmc | É de |
|---|---|
| `procedimento_vigente_para` + 412 `ProcedimentoVigenteAusente` (AC-CAL-016) | **procedimentos-calibracao** |
| O "como medir" (método documentado, versão, vigência, cl. 7.2.2) | **procedimentos-calibracao** |
| Gerência da acreditação CGCRE da empresa (US-LIC-001/003) | **Licenças e Acreditações** |
| Autorização de quem assina dentro do escopo (RT credenciado) | **responsavel_tecnico** (RTCompetencia) |
| Shewhart, 2º caminho, intercomparação PT, equipamento auxiliar, máquina física | **metrologia/padroes** |

**É de escopos-cmc:** o "até onde posso oferecer com selo RBC" — grandeza + faixa + CMC numérico + vínculo ao procedimento (FK) + 412 `EscopoNaoCobreFaixa`.

---

## 8. Proposta de fatiamento (INV-RITUAL-002) — 3 fatias

**Fatia 1 — Persistência + schema (P1-P4 ~ T-ECMC-001..032):** domínio (entities/enums/repository), model colunas tipadas + UNIQUE tenant-scoped, migrations irmãs (initial → RLS → WORM → grants → seed authz), repositório `cobre()` + CAS, drill `validar_escopos_cmc`. **Saída:** tabela `escopo_cmc` isolada, WORM, vigência canônica.

**Fatia 2 — Use cases + API + versionamento (P5-P7 ~ T-ECMC-040..061):** `cadastrar_escopo` / `revisar_escopo` (versão preservada) / `revogar_escopo`; ViewSet + serializers + idempotência + urls; vínculo `documento_regulatorio_id`; eventos WORM. **Saída:** admin cadastra/versiona/revoga pela API.

**Fatia 3 — Wire-in do predicate + gate (P8-P9 ~ T-ECMC-070..080):** `cmc_cobre` real (drop-in), resolver shape resource anti-PII + injeção server-side, teste transição fail-open→fail-closed sem quebrar legado, alimentar snapshot JSONB, suite M4 reverde, INVs + `TestINV_ECMC_NNN`, validação software cl. 7.11. **Saída:** `GATE-CAL-CMC-PREDICATE` aceso; 412 em produção.

---

## 9. Questões a decidir (com recomendação)

> **Roteamento:** A,B,F,G,M,O → consultor-rbc-iso17025 (metrologia/normativa). C,D,H,E,I,J,P,Q → tech-lead-saas-regulado (arquitetura). K,L,N → Roldão (produto / terminologia que o cliente lê / escopo MVP).

### Decisões do Roldão (2026-05-29 — AskUserQuestion)

- **L (rótulo CMC):** ✅ **"CMC (menor incerteza declarada)"** (seguiu recomendação).
- **N (cadastro):** ⚠️ **EXTRAÇÃO AUTOMÁTICA DO PDF** (contra recomendação de digitação manual). Implica: upload do PDF do escopo CGCRE + motor de extração + **tela de conferência humana OBRIGATÓRIA antes de persistir** (nunca auto-persistir dado regulatório). Adiciona **Fatia 4 (PDF→extração→conferência)** sobre o use case manual. Sub-decisão de arquitetura para o tech-lead no /plan: motor determinístico (leitor de tabela) vs IA (ativaria ADR-0059 LLMProvider reservada + INV-LLM-001..010 + custo). Nota: escopos CGCRE são documentos PÚBLICOS (inmetro.gov.br) → risco de privacidade baixo. Validação cl. 7.11 (ADR-0025) aplica se a extração tocar dado metrológico.
- **O (quem usa):** ⚠️ **TODOS OS PERFIS DECLARAM** (contra recomendação de gated-A). Desenho seguro confirmado: perfil A declara **escopo RBC** (`rbc_acreditado=true`, lastro CGCRE); B/C/D declaram **capacidade interna** (`rbc_acreditado=false` **forçado** — anti-fraude INV-015, não-A nunca marca RBC). **Bloqueio 412 `EscopoNaoCobreFaixa` continua RBC-only (perfil A)** — preserva a trava SAN-PERFIL/ADR-0067. Para não-A, capacidade declarada é informativa (aviso suave opcional, sem bloqueio duro — calibração não-A não carrega selo RBC). Confirmar matriz feature×perfil com RBC no /plan.
- **K (nº CGCRE):** ✅ decidido por mim (baixo risco) — **capturar campo, rótulo "Nº do escopo CGCRE"**.

> As decisões N e O **expandem o escopo** vs o dossiê original — os subagentes RBC + tech-lead devem validar as implicações no /plan (Fatia 4 + matriz perfil + possível ADR de extração).

**A. Cobertura da faixa (RBC):** contenção total (`faixa_min≥escopo_min E faixa_max≤escopo_max`) vs interseção. **Rec: contenção total** para bloqueio (interseção parcial = fraude). → RBC.
**B. Faixa vs U_expandida<CMC:** MVP valida só faixa, ou também barra `U_serviço < CMC_declarada`. **Rec: MVP valida faixa; U<CMC como INV adicional na Fatia 3 se RBC confirmar.** → RBC.
**C. Shape resource anti-PII:** aninhar sob `resource={'escopo':{...}}` vs expandir allowlist. **Rec: aninhar sob `escopo`** (já na allowlist; mínima). → tech-lead.
**D. Fonte grandeza+faixa+data:** snapshot recepção vs RTCompetencia vs novo campo na Calibracao. **Rec: modelar faixa na Calibracao, derivada server-side.** → tech-lead+RBC.
**E. Dois efeitos do predicate:** recepção avisa+degrada; configuração bloqueia 412. **Rec: sim, dois efeitos** (reflete PRD). → produto (já no PRD).
**F. Granularidade escopo×método e relação RTCompetencia:** 1:1 ou N. **Rec: 1 método por linha (`procedimento_id` NOT NULL p/ RBC); RTCompetencia fonte de verdade do RT, referenciada.** → RBC+tech-lead.
**G. `RTCompetenciaParaEscopo` nova vs reuso:** **Rec: referenciar RTCompetencia (reuso); escopo sem RT competente vivo → bloqueia uso RBC (não revoga auto).** → RBC+tech-lead.
**H. WORM/soft-delete:** Padrão B vs C. **Rec: Padrão B WORM forte** (escopo sustenta certificado RBC). → tech-lead (apontado pelos ADRs).
**I. Orquestração validação composta:** ordem de bloqueio escopo vs procedimento. **Rec: ordem fixa escopo→procedimento, 1ª falha; M4 dono da orquestração.** → tech-lead+produto.
**J. Snapshot `EscopoUsado` congelado:** VO WORM vs só FK. **Rec: congelar VO `EscopoUsado` em evento WORM** (ADR-0014 já criou a coluna). → produto/RBC.
**K. Nº oficial do escopo CGCRE:** capturar campo + rótulo. **Rec: capturar, rótulo "Nº do escopo CGCRE".** → Roldão (terminologia).
**L. Rótulo `cmc_valor`:** "CMC" vs "Menor incerteza declarada". **Rec: "CMC (menor incerteza declarada)".** → Roldão (terminologia).
**M. Múltiplos métodos por linha:** **Rec: cada (grandeza,faixa,método) é linha separada.** → RBC.
**N. Cadastro: digitação vs PDF:** **Rec: digitação manual no MVP** (extração PDF futuro). → Roldão (escopo MVP).
**O. Perfil-aware:** só perfil A vs A/B/C/D declaram capacidade. **Rec: gated a perfil A** (simétrico a procedimentos). → produto/RBC.
**P. Slug físico:** `escopos_cmc` (já cravado no drop-in). **Rec: confirmar.** → tech-lead.
**Q. Singleton `escopo_repo`:** module-level singleton vs DI. **Rec: singleton module-level** (drop-in exige). → tech-lead.
