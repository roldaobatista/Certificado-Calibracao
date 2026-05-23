---
owner: roldao
revisado_em: 2026-05-23
proximo_review: 2026-08-23
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/modelo-de-dominio.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0030-vigencia-temporal-canonica.md
---

# PRD — Módulo Procedimentos de Calibração (novo Onda 7 — A5-CAL)

> Módulo dedicado ao controle documentado dos procedimentos técnicos usados em calibração metrológica. Atende ISO 17025 cl. 7.2.1 (procedimento documentado controlado) e ADR-0030 (vigência temporal canônica). Cada calibração executada referencia a versão do procedimento vigente na data de execução.

---

## 1. O que este módulo é

Catálogo versionado de procedimentos técnicos por grandeza/faixa, com aprovação formal pelo RT do tenant, vigência temporal canônica (`vigencia_inicio`/`vigencia_fim` — ADR-0030), anexo PDF do procedimento técnico em si, escopo de aplicação (grandezas atendidas) e referência normativa (NIT-DICLA / norma técnica que ele instancia).

Procedimento é entidade Padrão B do `ADR-0031` (`revogado_em` + `motivo_revogacao` — soft-delete imutável).

## 2. Por que este módulo existe

ISO 17025 cl. 7.2.1 exige procedimento documentado e controlado por escrito para toda atividade laboratorial. Hoje (mystery shopping Calibre.Software) procedimentos vivem em Word + pasta de rede — versionamento ad-hoc, vigência opaca, calibração X usou procedimento Y de QUAL data ninguém sabe.

Sem módulo dedicado:
- Auditor CGCRE pergunta "qual procedimento foi usado em cert N de 2024?" → tenant não responde.
- RT aprova nova versão mid-calibração → calibração em andamento não sabe qual usa.
- Procedimento revogado por NC (ex: descoberto erro na fórmula) → cert antigos ficam sem referência válida.

## 3. Personas

Ver `../personas.md` (RT, gestor qualidade, metrologista, auditor CGCRE).

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de procedimento (código, versão, escopo de grandezas, norma de referência, anexo PDF, RT aprovador, datas de aprovação e vigência).
- Versionamento sequencial por código (`PROC-MASSA-001 v1.0`, `v1.1`, `v2.0`).
- Aprovação formal pelo RT do tenant (vincula assinatura A3 — INV-017).
- Vigência temporal canônica (`vigencia_inicio` / `vigencia_fim` — ADR-0030 + INV-VIG-001..004).
- Revogação com motivo (`revogado_em`, `motivo_revogacao` ≥10 chars — INV-VIG-002).
- Snapshot na calibração (`Calibracao.procedimento_versao_snapshot` — US-CAL-016).
- Consulta histórica "qual procedimento estava vigente em data X para grandeza Y" (predicate `procedimento_vigente_para`).
- Auditoria de uso (lista de calibrações que usaram cada procedimento).
- Anexo PDF imutável após aprovação (hash SHA-256 registrado).

## 5. Non-goals

- NÃO edita o procedimento técnico em si (é PDF anexo gerado fora do sistema — Word/LaTeX).
- NÃO substitui sistema de gestão da qualidade ISO 9001.
- NÃO é template de execução (template é `ConfiguracaoCalibracao` no módulo Calibração).
- NÃO gerencia revisão técnica do conteúdo do procedimento (revisão acontece offline; aqui só registra aprovação).

## 6. User Stories

### US-PROC-001: Cadastrar procedimento de calibração

**Como** RT do tenant, **quero** cadastrar procedimento (código, versão, escopo, norma, anexo PDF), **para** ter base documentada do que o lab faz.

**Critérios de aceite:**
- **AC-PROC-001-1**: GIVEN RT autenticado, WHEN cadastra (código, versão, escopo_grandezas[], norma_referencia, anexo_pdf), THEN sistema valida unicidade `(tenant_id, codigo, versao)` + persiste em status `RASCUNHO`.
- **AC-PROC-001-2**: GIVEN anexo PDF, WHEN upload, THEN sistema calcula `anexo_pdf_hash` SHA-256 + persiste imutável + persiste em B2 WORM.

**Invariantes:** `INV-PROC-001`, `INV-TENANT-001`.

---

### US-PROC-002: Aprovar procedimento + estabelecer vigência

**Como** RT do tenant, **quero** aprovar procedimento em `RASCUNHO` definindo `vigencia_inicio` (e opcionalmente `vigencia_fim`), **para** que calibrações comecem a usá-lo.

**Critérios de aceite:**
- **AC-PROC-002-1**: GIVEN procedimento em RASCUNHO, WHEN RT aprova com assinatura A3, THEN sistema seta `aprovado_por_rt_id`, `data_aprovacao`, `vigencia_inicio` + status `VIGENTE`.
- **AC-PROC-002-2**: GIVEN procedimento aprovado, WHEN sistema valida, THEN exige `vigencia_inicio >= data_aprovacao` (não aprovar com vigência retroativa); `vigencia_fim` opcional respeitando INV-VIG-001/003.
- **AC-PROC-002-3**: GIVEN aprovação concluída, WHEN persistido, THEN dispara evento `ProcedimentoAprovado(procedimento_id, codigo, versao, vigencia_inicio, correlation_id)`.

**Invariantes:** `INV-PROC-001`, `INV-PROC-002` (RT do tenant aprovador + assinatura A3), `INV-VIG-001..004`, `INV-017`.

---

### US-PROC-003: Resolver procedimento vigente para grandeza/faixa em data

**Como** módulo Calibração (US-CAL-016) ou auditor CGCRE, **quero** consultar qual procedimento estava vigente em data T para grandeza G + faixa F, **para** vincular calibração ou auditar retroativamente.

**Critérios de aceite:**
- **AC-PROC-003-1**: GIVEN predicate `procedimento_vigente_para(tenant_id, grandeza, faixa, em_data)`, WHEN chamado, THEN retorna procedimento único OU None; ambiguidade (2 vigentes ao mesmo tempo cobrindo mesma grandeza/faixa) é erro de configuração + alerta P1.
- **AC-PROC-003-2**: GIVEN procedimento revogado, WHEN consulta em data anterior à revogação, THEN ainda retorna como vigente naquela data (consulta histórica preservada).

**Invariantes:** `INV-PROC-001`, `INV-VIG-001..004`.

---

### US-PROC-004: Revogar procedimento

**Como** RT do tenant, **quero** revogar procedimento (descoberto erro, substituição por nova versão), **para** parar novas calibrações de usá-lo sem invalidar cert antigos.

**Critérios de aceite:**
- **AC-PROC-004-1**: GIVEN procedimento VIGENTE, WHEN RT revoga com motivo (≥10 chars — INV-VIG-002), THEN sistema seta `revogado_em` + `motivo_revogacao` + status `REVOGADO`; calibrações novas não usam mais (US-CAL-016 AC-1).
- **AC-PROC-004-2**: GIVEN procedimento REVOGADO, WHEN consulta histórica em data anterior à revogação, THEN ainda retorna (US-PROC-003).
- **AC-PROC-004-3**: GIVEN cert emitidos usando procedimento revogado, WHEN RT revoga, THEN sistema NÃO invalida cert; opcionalmente dispara análise de impacto (similar US-CAL-014 AC-3) se motivo indica erro técnico.

**Invariantes:** `INV-PROC-001`, `INV-VIG-001..004`, `INV-SOFT-002` (WORM físico em entidade Padrão B).

---

### US-PROC-005: Auditoria de uso

**Como** auditor CGCRE ou RT, **quero** listar calibrações que usaram cada procedimento + versão, **para** comprovar uso documentado.

**Critérios de aceite:**
- **AC-PROC-005-1**: GIVEN procedimento, WHEN auditor consulta, THEN sistema lista todas as `Calibracao` que vinculam `procedimento_id` daquela versão + período de uso (datas execução).

**Invariantes:** `INV-PROC-001`, `INV-TENANT-001`.

---

## 7. Métricas de sucesso

- Zero calibração RBC sem `procedimento_id` vinculado (target 100%).
- Zero ambiguidade de procedimento vigente (target: 0 alertas P1).
- Tempo médio resolução `procedimento_vigente_para` ≤ 50ms p95.

## 8. NFR

- **Performance:** consulta `procedimento_vigente_para` indexada por (tenant_id, grandeza, vigencia_inicio).
- **Disponibilidade:** 99.9%.
- **Segurança:** SEC-001, SEC-002; anexo PDF em B2 WORM; tenant-scoped.

## 9. Invariantes (novo Onda 7 — A5-CAL)

- **INV-PROC-001:** toda `Calibracao` configurada como RBC referencia `ProcedimentoCalibracao` vigente na data de execução (predicate `procedimento_vigente_para`); ausência bloqueia configuração com 412.
- **INV-PROC-002:** aprovação de procedimento exige RT do tenant + assinatura A3 (INV-017) + `data_aprovacao` ≤ `vigencia_inicio`.
- **INV-PROC-003:** anexo PDF do procedimento imutável após aprovação (hash SHA-256 registrado + B2 WORM).

## 10. Como este PRD evolui

- US nova → próximo `US-PROC-NNN`.
- Mudança no schema → ADR + migration.
