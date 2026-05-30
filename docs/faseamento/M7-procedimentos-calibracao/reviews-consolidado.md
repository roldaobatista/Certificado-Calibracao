---
owner: roldao
revisado-em: 2026-05-30
status: stable
fase: M7-procedimentos-calibracao
ritual: reviews
relacionados:
  - docs/faseamento/M7-procedimentos-calibracao/spec.md
  - docs/faseamento/M7-procedimentos-calibracao/plan.md
---

# Revisões consolidadas — M7 `procedimentos-calibracao` (spec v1)

> Revisões `consultor-rbc-iso17025` + `tech-lead-saas-regulado` (2026-05-30) da
> spec v1. **Veredito conjunto: APROVA COM CORREÇÕES** — correções ADITIVAS, não
> redesenho. **Nenhuma ADR nova obrigatória** (cabe em 0072/0073/0076/0031/0064/
> 0065 + emenda US-CAL-016). 6 decisões cravadas para o /plan.

## Decisões cravadas (vão para o plan v2)

| # | Decisão | Origem | Severidade |
|---|---------|--------|------------|
| **D-PROC-1** | **Aplicabilidade por perfil:** bloqueio 412 `ProcedimentoVigenteAusente` **SÓ perfil A** (RBC). C ("em preparação") NÃO entra no bloqueio duro. B/C/D recebem **aviso degradante recomendado** (não silêncio, não bloqueio) — cl. 7.2.1 educa a trilha D→A. US-PROC-005 ganha ramo NÃO-RBC = aviso. | RBC item 1 / NC-PROC-04 | BAIXO |
| **D-PROC-2** | **Separar chave documental da chave de resolução.** `codigo` = identidade do documento controlado (cl. 8.3); chave de unicidade `(tenant, codigo, versao)`. Resolução `vigente_em` por grandeza+faixa (contenção). **MVP: 1 grandeza + faixa contígua única por código** (Balanças/massa cabe), extensível a N-faixas. NÃO um código para múltiplas grandezas. | RBC item 2 / NC-PROC-05 | BAIXO |
| **D-PROC-3** | **Superseção automática na publicação, MESMA transação:** ao publicar N+1, encerra `vigencia_fim` da versão N vigente (mesma grandeza+faixa). **advisory lock `pg_advisory_xact_lock(hash(tenant, codigo, grandeza, faixa))`** (molde ADR-0065) + **UNIQUE parcial** `(tenant, codigo, grandeza, faixa_min, faixa_max) WHERE estado='PUBLICADO' AND vigencia_fim IS NULL AND revogado_em IS NULL` (cinto-e-suspensório). **NÃO só CAS `revision`** — race deixa 2 vigentes. → **INV-PROC-008** (não-overlap de vigência). | RBC item 3 + TL item 4 / NC-PROC-03 | **ALTO** |
| **D-PROC-4** | **3 campos de controle documental cl. 8.3.1:** `numero_revisao` (ex. "Rev. 03" — distinto de `versao`), `aprovado_em` (data do ato de aprovação ≠ `vigente_a_partir`), `aprovado_por_id` (+ snapshot do nome). Propagados ao snapshot da calibração. → **INV-PROC-009**. | RBC item 5 / NC-PROC-02 | MÉDIO |
| **D-PROC-5** | **Qualificação de método cl. 7.2.2:** campo `tipo_metodo` (NORMALIZADO / NAO_NORMALIZADO / MODIFICADO) + FK opcional `registro_validacao_id`. Perfil A + método NÃO-NORMALIZADO exige evidência de validação antes de publicar — **fail-open lazy** (paralelo ADR-0066) até `licencas-acreditacoes`. → **INV-PROC-010** + **GATE-PROC-METODO-VALIDADO**. Emenda US-CAL-016 (não ADR nova). | RBC NC-PROC-01 | **ALTO** |
| **D-PROC-6** | **Geometria de faixa compartilhada:** extrair **só** `faixa_contida` + `avaliar_contencao` (escopos_cmc/cobertura.py:32-54) → `src/domain/metrologia/faixa_cobertura.py`; escopos_cmc re-exporta (zero mudança de assinatura). **Suíte M6 reverde idêntica** (gate anti-regressão). NÃO mover `cmc_*`/`u_*` (CMC tridimensional — M7 não tem). Erros de domínio distintos (`ProcedimentoVigenteAusente` ≠ `EscopoNaoCobreFaixa`). | RBC item 4 + TL item 1 | **ALTO** |

## Correções factuais na spec (causa-raiz — Regra #0)

- **C-1:** `procedimento_versao_snapshot` **JÁ EXISTE** desde M4 P4 (`ConfigurarCalibracaoInput.procedimento_versao_snapshot: dict` — `configurar_calibracao.py:187`, validado `{codigo, versao, hash_anexo}` no `__post_init__`, cravado no snapshot linha 334). **M7 PREENCHE o existente, NÃO cria coluna** na Calibracao. (TL R-A2 / item 3.2)
- **C-2:** anexo PDF = **`sha256` puro server-side** (integridade de conteúdo, molde OS `termo_pdf_sha256`), **NÃO HashVersionado/HMAC ADR-0064**. HMAC ADR-0064 fica para os **eventos hash-chain** (autenticidade da cadeia). Não misturar. INV-PROC-007 corrigida. (TL item 2 + D6)
- **C-3:** porta = **função de módulo** `query_service.vigente_em(...)` injetada (molde M6 real), **não singleton/`*_repo`**. (já correto na spec §7/§10; reforçar no plan — TL R-A1)
- **C-4:** **1ª porta de storage real do projeto** — `AnexoStoragePort` Protocol (application) + adapter B2/filesystem (infra). View recebe multipart, **recalcula sha256 server-side** (ignora hash do cliente), persiste binário, grava `anexo_pdf_storage_key` opaca + `anexo_pdf_sha256`. Porta "Storage" já está no catálogo de 18 portas do anti-corrosion-layer → **sem ADR nova**. (TL item 2)

## Divergências do molde M6 (NÃO copiar cego)

- D1 — **sem fatia de extração PDF** (procedimento é autorado, não extraído da CGCRE; não ativa ADR-0059 LLM).
- D2 — estados `RASCUNHO→PUBLICADO→REVOGADO` (≠ M6 `RASCUNHO_EXTRAIDO→CONFIRMADO→REVOGADO`).
- D3 — cobertura **só existência+vigência+contenção**; NÃO portar `cmc_para`/`menor_cmc_por_faixa`/`u_atende_cmc` (CMC tridimensional).
- D4 — **só 1 porta** `vigente_em()` (config); SEM 2ª porta de emissão (procedimento não reconcilia por pontos).
- D5 — sem `rbc_acreditado` forçado / INV-ECMC-002 anti-fraude (procedimento não é selo RBC; perfil-aware só decide QUEM bloqueia).

## Sequenciamento

D-PROC-2 (granularidade, RBC) decide a chave natural → **antes** do UNIQUE parcial de superseção D-PROC-3 (TL R-A3). Já resolvido: 1 grandeza + faixa contígua por código → UNIQUE parcial `(tenant, codigo, grandeza, faixa_min, faixa_max)`.

## Limite de honestidade (TL)

Concorrência de superseção (D-PROC-3) é race que passa em code review e só aparece com publicações simultâneas reais. UNIQUE parcial + advisory lock mitiga na arquitetura; recomendar **drill cronometrado de concorrência em PG real** antes do 1º tenant RBC externo (GATE-PROC-DRILL-LOCAL).

## Veredito

**APROVA COM CORREÇÕES.** Fatiamento (4 fatias) mantido. As 6 decisões + 4 correções factuais entram no plan v2. Sem ADR nova. INVs do módulo: INV-PROC-001..010.
