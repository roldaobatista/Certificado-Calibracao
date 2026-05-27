---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
diataxis: explanation
audiencia: agente
modulo: procedimentos
dominio: metrologia
historico:
  - 2026-05-27 — Onda PRE-A.3 saneamento pré-Wave A (BATCH B3): perfil ADR-0067 declarado;
    AC binário GIVEN-WHEN-THEN com ID; ADR-0066 (fail-open lazy → fail-closed Wave A);
    ADR-0025 v2 (URS/IQ/OQ/PQ para procedimentos + validação de método cl. 7.2.2);
    nova US-PROC-006 (validação de método quando lab modifica norma); matriz feature×perfil;
    personas inline; non-goals expandidos; métricas inline; glossário §11.
  - 2026-05-23 — versão inicial Onda 7 — A5-CAL.
relacionados:
  - docs/dominios/metrologia/modulos/calibracao/prd.md
  - docs/dominios/metrologia/modulos/calibracao/modelo-de-dominio.md
  - docs/dominios/metrologia/modulos/calibracao/validacao-software.md
  - docs/dominios/metrologia/modulos/padroes/prd.md
  - docs/adr/0022-rt-tenant.md
  - docs/adr/0024-regra-de-decisao-iso-17025.md
  - docs/adr/0025-validacao-software-iso-17025.md
  - docs/adr/0026-segunda-conferencia-independencia.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-3-padroes.md
  - docs/adr/0040-padrao-metrologico-entidade-separada.md
  - docs/adr/0064-rotacao-chave-hmac-retencao-metrologica-25a.md
  - docs/adr/0065-concorrencia-calibracao-metrologica.md
  - docs/adr/0066-predicates-cmc-procedimento-fail-open-lazy-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/adr/0068-sucessao-substituicao-rt.md
  - docs/conformidade/comum/matriz-feature-perfil.md
---

# PRD — Módulo Procedimentos de Calibração

> Módulo dedicado ao controle documentado dos procedimentos técnicos usados em calibração metrológica. Atende ISO 17025 cl. 7.2.1 (procedimento documentado controlado), cl. 7.2.2 (validação de método quando o lab modifica norma) e ADR-0030 (vigência temporal canônica). Cada calibração executada referencia a versão do procedimento vigente na data de execução.

---

## 1. O que este módulo é

Catálogo versionado de procedimentos técnicos por grandeza/faixa/método, com aprovação formal pelo RT do tenant (ADR-0022 + ADR-0068), vigência temporal canônica (`vigencia_inicio`/`vigencia_fim` — ADR-0030), anexo PDF do procedimento técnico em si (imutável + hash SHA-256), escopo de aplicação (grandezas + faixas + métodos atendidos), referência normativa (NIT-DICLA / norma técnica que ele instancia) e — quando o lab modifica a norma — **protocolo de validação de método ISO 17025 cl. 7.2.2** anexado.

Procedimento é entidade Padrão B do `ADR-0031` (`revogado_em` + `motivo_revogacao` — soft-delete imutável WORM).

## 2. Por que este módulo existe

ISO 17025 cl. 7.2.1 exige procedimento documentado e controlado por escrito para toda atividade laboratorial. Cl. 7.2.2 exige validação documentada quando o lab cria, modifica ou usa método fora do escopo normativo. Hoje (mystery shopping Calibre.Software) procedimentos vivem em Word + pasta de rede — versionamento ad-hoc, vigência opaca, calibração X usou procedimento Y de QUAL data ninguém sabe, modificação de norma sem validação formal.

Sem módulo dedicado:
- Auditor CGCRE pergunta "qual procedimento foi usado em cert N de 2024?" → tenant não responde.
- RT aprova nova versão mid-calibração → calibração em andamento não sabe qual usa.
- Procedimento revogado por NC (descoberto erro na fórmula) → cert antigos ficam sem referência válida.
- Lab modifica norma sem validação cl. 7.2.2 → supervisão CGCRE flagra como NC ALTO.

## 3. Personas

- **P-OP-04 — Gestor de qualidade do tenant** (principal): mantém catálogo, abre fluxo de aprovação, dispara revogação.
- **P-OP-03 — RT do tenant** (ADR-0022 + ADR-0068): aprova procedimento com A3, define vigência, assina validação de método cl. 7.2.2.
- **P-OP-02 — Metrologista de bancada**: consome o procedimento vigente em runtime (via `procedimento_vigente_para`).
- **P-COM-02 — Auditor / supervisor CGCRE** (perfil A): consulta histórico para supervisão.

## 4. Perfil regulatório (ADR-0067)

| Perfil | Status do módulo | Predicate de entrada |
|---|---|---|
| **A — Acreditado RBC** | ✅ OBRIGATÓRIO (cl. 7.2.1 + 7.2.2 + 8.3 controle de documentos) | `tenant_perfil_e(["A"])` aplicado a US-PROC-002/005/006 |
| **B — Rastreável** | ✅ OBRIGATÓRIO (recomendado para preparar D→A) | `tenant_perfil_e(["A", "B"])` em US-PROC-002 |
| **C — Em preparação D→A** | ✅ OBRIGATÓRIO_PARCIAL (catálogo mínimo + 1 procedimento vigente por grandeza/faixa coberta) | `tenant_perfil_e(["A", "B", "C"])` em US-PROC-002 |
| **D — Comercial puro** | ⚪ OPCIONAL | sem bloqueio (mas habilitado para tenants que queiram preparar promoção D→C) |

A linha "Procedimento de calibração vigente" da matriz `docs/conformidade/comum/matriz-feature-perfil.md` é fonte da verdade. **Predicate `procedimento_vigente_para` invocado em runtime após Wave A** (ver §"ADR-0066").

## 5. Escopo (o que ESTÁ neste módulo)

- Cadastro de procedimento (código, versão, escopo `(grandeza, faixa_min, faixa_max, metodo)[]`, norma de referência, anexo PDF, RT aprovador, datas de aprovação e vigência).
- Versionamento sequencial por código (`PROC-MASSA-001 v1.0`, `v1.1`, `v2.0`).
- Aprovação formal pelo RT do tenant (vincula assinatura A3 — INV-017).
- **Validação de método cl. 7.2.2** quando lab modifica norma (URS/OQ/PQ específicos do procedimento — ADR-0025 v2 estendida ao módulo).
- Vigência temporal canônica (`vigencia_inicio` / `vigencia_fim` — ADR-0030 + INV-VIG-001..004).
- Revogação com motivo (`revogado_em`, `motivo_revogacao` ≥10 chars — INV-VIG-002).
- Snapshot na calibração (`Calibracao.procedimento_versao_snapshot` — US-CAL-016).
- Consulta histórica "qual procedimento estava vigente em data X para grandeza Y faixa F método M" (predicate `procedimento_vigente_para`).
- Auditoria de uso (lista de calibrações que usaram cada procedimento).
- Anexo PDF imutável após aprovação (hash SHA-256 registrado + B2 WORM).

## 6. Non-objetivos

- NÃO edita o procedimento técnico em si (é PDF anexo gerado fora — Word/LaTeX/Markdown).
- NÃO substitui sistema de gestão da qualidade ISO 9001.
- NÃO é template de execução (template é `ConfiguracaoCalibracao` no módulo Calibração).
- NÃO gerencia revisão técnica do conteúdo do procedimento (revisão acontece offline; aqui só registra aprovação).
- NÃO entrega LMS / EAD de procedimento (treinamento dos técnicos sobre o procedimento vive em `rh-frota-qualidade/treinamentos`).

## 7. User Stories

### US-PROC-001: Cadastrar procedimento de calibração

**Como** gestor de qualidade do tenant, **quero** cadastrar procedimento (código, versão, escopo, norma, anexo PDF), **para** ter base documentada do que o lab faz.

**Critérios de aceite:**
- **AC-PROC-001-1**: GIVEN gestor de qualidade autenticado + tenant `perfil_regulatorio ∈ {A, B, C, D}`, WHEN cadastra (código, versão, escopo_grandezas_faixas_metodos[], norma_referencia, anexo_pdf), THEN sistema valida unicidade `(tenant_id, codigo, versao)` + persiste em status `RASCUNHO`.
- **AC-PROC-001-2**: GIVEN anexo PDF, WHEN upload, THEN sistema calcula `anexo_pdf_hash` SHA-256 + persiste em B2 WORM + bloqueia mutação após aprovação (INV-PROC-003).

**Invariantes:** `INV-PROC-001`, `INV-TENANT-001`.

---

### US-PROC-002: Aprovar procedimento + estabelecer vigência + bloquear calibração sem procedimento vigente

**Como** RT do tenant, **quero** aprovar procedimento em `RASCUNHO` definindo `vigencia_inicio` (e opcionalmente `vigencia_fim`), **para** que calibrações comecem a usá-lo. **E** que o sistema bloqueie novas calibrações sem procedimento vigente para a grandeza/faixa/método solicitados.

**Critérios de aceite:**
- **AC-PROC-002-1**: GIVEN procedimento em RASCUNHO + RT com `RTCompetencia.{grandeza, metodo}` vigente (ADR-0022 v2) cobrindo o escopo declarado, WHEN RT aprova com assinatura A3 ICP-Brasil, THEN sistema seta `aprovado_por_rt_id`, `data_aprovacao`, `vigencia_inicio` + status `VIGENTE`.
- **AC-PROC-002-2**: GIVEN procedimento aprovado, WHEN sistema valida, THEN exige `vigencia_inicio >= data_aprovacao` (não aprovar com vigência retroativa); `vigencia_fim` opcional respeitando INV-VIG-001/003.
- **AC-PROC-002-3**: GIVEN aprovação concluída, WHEN persistido, THEN dispara evento `ProcedimentoAprovado(procedimento_id, codigo, versao, vigencia_inicio, escopo[], correlation_id)` em WORM com hash-chain HMAC ADR-0064.
- **AC-PROC-002-4**: GIVEN tenant `perfil_regulatorio ∈ {A, B, C}` + tenta configurar calibração com `(grandeza=G, faixa=F, metodo=M)` SEM procedimento vigente cobrindo `(G, F, M)`, THEN sistema bloqueia com 412 `ProcedimentoVigenteAusente`. **ADR-0066 (paralelo a ADR-0063 do M3 OS):** predicate `procedimento_vigente_para(tenant_id, grandeza, faixa, metodo, em_data)` declarado em P4 Fase 2 com fail-open lazy controlado em Marco 4 dogfooding; bloqueio efetivo entra em vigor automaticamente quando módulo `metrologia/procedimentos-calibracao` for plugado em Wave A via `AtividadeDaOS.procedimento_versao_id` (`GATE-CAL-PROC-VIGENTE-PREDICATE`).
- **AC-PROC-002-5**: GIVEN tenant `perfil_regulatorio = D`, WHEN configura calibração sem procedimento vigente, THEN sistema permite mas registra warning operacional no log (não bloqueia — perfil D é OPCIONAL na matriz feature×perfil).

**Invariantes:** `INV-PROC-001`, `INV-PROC-002` (RT do tenant aprovador + assinatura A3), `INV-VIG-001..004`, `INV-017`.

---

### US-PROC-003: Resolver procedimento vigente para grandeza/faixa/método em data

**Como** módulo Calibração (US-CAL-016) ou auditor CGCRE, **quero** consultar qual procedimento estava vigente em data T para grandeza G + faixa F + método M, **para** vincular calibração ou auditar retroativamente.

**Critérios de aceite:**
- **AC-PROC-003-1**: GIVEN predicate `procedimento_vigente_para(tenant_id, grandeza, faixa, metodo, em_data)`, WHEN chamado, THEN retorna procedimento único OU None; ambiguidade (2 vigentes ao mesmo tempo cobrindo mesma grandeza/faixa/método) é erro de configuração + alerta P1 + flag `GATE-CAL-PROC-VIGENTE-AMBIGUIDADE`.
- **AC-PROC-003-2**: GIVEN procedimento revogado, WHEN consulta em data anterior à revogação, THEN ainda retorna como vigente naquela data (consulta histórica preservada — ISO 17025 cl. 8.4).
- **AC-PROC-003-3**: GIVEN cache local invalido após mudança em `Procedimento.vigencia_fim`, WHEN próxima consulta, THEN miss + reload em ≤50ms p95.

**Invariantes:** `INV-PROC-001`, `INV-VIG-001..004`.

---

### US-PROC-004: Revogar procedimento

**Como** RT do tenant (ADR-0068 — incluindo RT sucessor), **quero** revogar procedimento (descoberto erro, substituição por nova versão), **para** parar novas calibrações de usá-lo sem invalidar cert antigos.

**Critérios de aceite:**
- **AC-PROC-004-1**: GIVEN procedimento VIGENTE + RT autenticado com A3, WHEN RT revoga com `motivo_revogacao` (≥10 chars — INV-VIG-002) + tipo (`ERRO_TECNICO_DESCOBERTO` / `SUBSTITUIDO_POR_NOVA_VERSAO` / `NORMA_REFERENCIA_REVOGADA_INMETRO`), THEN sistema seta `revogado_em` + `motivo_revogacao` + status `REVOGADO`; calibrações novas não usam mais (US-CAL-016 AC-1); evento `ProcedimentoRevogado` em WORM.
- **AC-PROC-004-2**: GIVEN procedimento REVOGADO, WHEN consulta histórica em data anterior à revogação, THEN ainda retorna (US-PROC-003 AC-3-2).
- **AC-PROC-004-3**: GIVEN cert emitidos usando procedimento revogado + tipo=`ERRO_TECNICO_DESCOBERTO`, WHEN RT revoga, THEN sistema dispara análise de impacto (similar US-CAL-014 AC-3) + bloqueio temporário de novas calibrações na mesma grandeza/faixa até procedimento substituto VIGENTE existir.

**Invariantes:** `INV-PROC-001`, `INV-VIG-001..004`, `INV-SOFT-002` (WORM físico em entidade Padrão B).

---

### US-PROC-005: Auditoria de uso

**Como** auditor CGCRE ou RT, **quero** listar calibrações que usaram cada procedimento + versão, **para** comprovar uso documentado em supervisão (perfil A obrigatório).

**Critérios de aceite:**
- **AC-PROC-005-1**: GIVEN procedimento + tenant `perfil_regulatorio = A`, WHEN auditor consulta, THEN sistema lista todas as `Calibracao` que vinculam `procedimento_id` daquela versão + período de uso (datas execução) + IDs de certificado emitido.
- **AC-PROC-005-2**: GIVEN export para dossiê CGCRE, WHEN gerado, THEN inclui hash SHA-256 do PDF anexo + cadeia HMAC (ADR-0064) cobrindo todas as `Calibracao` vinculadas.

**Invariantes:** `INV-PROC-001`, `INV-TENANT-001`, `INV-HMAC-001..005`.

---

### US-PROC-006: Validar método quando lab modifica norma (cl. 7.2.2)

**Como** RT do tenant em perfil A ou C, **quero** registrar protocolo de validação documentada quando o lab modifica método normativo (faixa estendida, ponto não previsto, mudança na fórmula), **para** atender ISO 17025 cl. 7.2.2 e ADR-0025 v2 (validação de software/método estendida a 4 módulos metrologia).

**Critérios de aceite:**
- **AC-PROC-006-1**: GIVEN procedimento em RASCUNHO + flag `modifica_norma=TRUE`, WHEN gestor de qualidade tenta enviar para aprovação SEM `protocolo_validacao_metodo_pdf_id` anexado, THEN sistema bloqueia com 412 `ValidacaoMetodoAusente` citando cl. 7.2.2.
- **AC-PROC-006-2**: GIVEN protocolo de validação anexado, WHEN sistema valida estrutura, THEN exige 4 seções obrigatórias (URS — requisitos do usuário; OQ — testes operacionais; PQ — performance qualification; conclusão com aceitação por RT) conforme ADR-0025 v2 §"Extensão módulo procedimentos".
- **AC-PROC-006-3**: GIVEN procedimento `modifica_norma=TRUE` aprovado, WHEN consumido em `Calibracao`, THEN snapshot da `Calibracao.procedimento_versao_snapshot` inclui hash SHA-256 do `protocolo_validacao_metodo_pdf` (imutável WORM).
- **AC-PROC-006-4**: GIVEN tenant `perfil_regulatorio = A` + procedimento `modifica_norma=TRUE` aprovado, WHEN dossiê CGCRE exportado, THEN protocolo de validação aparece junto com o procedimento (cadeia documental cl. 7.2.2 + cl. 8.4).

**Invariantes:** `INV-PROC-004` (nova), `INV-VAL-METODO-001` (nova — protocolo obrigatório quando `modifica_norma=TRUE`), `INV-017`.

---

## 8. Métricas de sucesso

- **Zero calibração RBC (perfil A) sem `procedimento_id` vinculado** (target 100% — bloqueio AC-PROC-002-4 garante).
- **Zero ambiguidade de procedimento vigente** (target: 0 alertas P1/mês).
- **Tempo médio resolução `procedimento_vigente_para`** ≤ 50ms p95.
- **% procedimentos `modifica_norma=TRUE` com protocolo de validação anexado** (perfil A): 100%.

## 9. NFR

- **Performance:** consulta `procedimento_vigente_para` indexada por `(tenant_id, grandeza, metodo, vigencia_inicio)` + cache em memória 5min com invalidação por evento.
- **Disponibilidade:** 99.9%.
- **Segurança:** SEC-001, SEC-002; anexo PDF em B2 WORM; tenant-scoped via RLS (ADR-0002); evento `ProcedimentoAprovado` / `ProcedimentoRevogado` em hash-chain HMAC ADR-0064 (rotação anual, retenção 25a).
- **Acessibilidade:** WCAG 2.1 AA (ADR-0057) — painel catálogo + tela de aprovação A3.

## 10. Invariantes

- **INV-PROC-001:** toda `Calibracao` configurada (perfil A/B/C — predicate efetivo Wave A via ADR-0066) referencia `ProcedimentoCalibracao` vigente na data de execução (predicate `procedimento_vigente_para`); ausência bloqueia configuração com 412 `ProcedimentoVigenteAusente`.
- **INV-PROC-002:** aprovação de procedimento exige RT do tenant + assinatura A3 (INV-017) + `data_aprovacao` ≤ `vigencia_inicio` + RT com `RTCompetencia.{grandeza, metodo}` vigente cobrindo o escopo declarado (ADR-0022 v2).
- **INV-PROC-003:** anexo PDF do procedimento imutável após aprovação (hash SHA-256 registrado + B2 WORM).
- **INV-PROC-004:** procedimento `modifica_norma=TRUE` exige `protocolo_validacao_metodo_pdf_id` anexado antes da aprovação (cl. 7.2.2 — ADR-0025 v2).

## 11. Glossário e referências

- **CMC** — Capacidade de Medição e Calibração declarada pelo lab à CGCRE (ver módulo `metrologia/escopos-cmc` Wave A).
- **Procedimento vigente** — instância de `ProcedimentoCalibracao` com `vigencia_inicio <= em_data` AND (`vigencia_fim IS NULL` OR `vigencia_fim > em_data`) AND `revogado_em IS NULL`.
- **Validação de método (cl. 7.2.2)** — protocolo formal exigido pela ISO 17025 quando lab cria/modifica método fora do escopo normativo. Estrutura URS/OQ/PQ + aceitação RT — ADR-0025 v2 §"Extensão módulo procedimentos".
- **Norma de referência** — NIT-DICLA-XXX, ISO XXX, OIML R-XXX que o procedimento instancia.
- **Snapshot** — cópia imutável em `Calibracao.procedimento_versao_snapshot` no momento da execução (rastreabilidade cl. 8.4).
- Glossário do módulo Calibração: `docs/dominios/metrologia/modulos/calibracao/glossario.md`.

## 12. Dependências ADR

ADR-0002 (RLS) · ADR-0007 (codegen) · ADR-0022 v2 (RT competência por método) · ADR-0024 (regra de decisão) · ADR-0025 v2 (validação software/método estendida) · ADR-0026 (2ª conferência) · ADR-0030 (vigência canônica) · ADR-0031 (soft-delete padrão B) · ADR-0040 (padrões entidade separada) · ADR-0064 (HMAC 25a) · ADR-0065 (concorrência) · ADR-0066 (fail-open lazy → fail-closed Wave A) · ADR-0067 (perfil regulatório) · ADR-0068 (sucessão RT).

## 13. Como este PRD evolui

- US nova → próximo `US-PROC-NNN`.
- Mudança no schema → ADR + migration.
- Mudança em AC binário implementado → ADR + novo teste de regressão.
