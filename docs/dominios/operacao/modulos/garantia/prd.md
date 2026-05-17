---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
modulo: garantia
dominio: operacao
---

# PRD — Módulo Garantia

## 1. O que este módulo é

Centraliza toda garantia oferecida pela empresa: serviço executado, peça aplicada e equipamento vendido. Recebe OS marcada como "em garantia", separa custo de retrabalho, bloqueia cobrança quando a garantia for procedente e mede reincidência por cliente, técnico, peça ou equipamento. Também controla a garantia repassada pelo Fornecedor (envio da peça defeituosa, retorno e ressarcimento).

## 2. Por que este módulo existe

Sem módulo de garantia, retrabalho some na rotina, custo oculto não é medido e defeitos recorrentes só aparecem por reclamação do cliente. Cobre dor de "não saber quanto retrabalho custa" e "cobrar cliente por serviço que estava em garantia" (`docs/novas funcionalidades.txt` linhas 1286-1308, Adicional 7).

## 3. Personas

Ver `personas.md`. Transversais em `../../personas.md` e `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Cadastro de prazo de garantia por tipo de item (serviço, peça, equipamento) e por tenant
- Marcação de OS como "em garantia" referenciando OS-mãe / venda / peça
- Workflow de análise procedente vs improcedente, com laudo obrigatório
- Custo da garantia segregado (mão de obra + peça + deslocamento), não vai pro faturamento
- Bloqueio automático de cobrança quando garantia procedente
- Controle de garantia do fornecedor: envio da peça, NF de remessa, retorno, ressarcimento
- Indicador de reincidência (cliente, técnico, peça-modelo, equipamento-serial)
- Eventos `GarantiaAberta`, `GarantiaAnalisada`, `GarantiaProcedente`, `GarantiaImprocedente`, `GarantiaFornecedorAberta`, `GarantiaFornecedorRetornada`

## 5. Non-goals

- Não emite NF-e (Financeiro/Fiscal cuida — Garantia só sinaliza "não cobrar")
- Não calcula provisão contábil da garantia (vai pra Financeiro num evolutivo)
- Não substitui o módulo de Não Conformidade da Calibração (INV-012) — quando OS de calibração entra em garantia COM NC, os dois módulos coexistem
- Não cobre recall em massa (módulo separado, futuro)

## 6. User Stories

### US-GAR-001: registrar prazo de garantia por tipo de item

**Como** gerente operacional, **quero** definir prazo de garantia por tipo (serviço X dias, peça Y dias, equipamento vendido Z meses), **para** ter regra clara aplicada automaticamente em toda OS de garantia.

**AC:**
- **AC-GAR-001-1:** GIVEN tenant ativo, WHEN cadastra prazo por tipo, THEN sistema valida prazo > 0 e armazena versionado (mudança não retroage — INV-026 análogo).
- **AC-GAR-001-2:** GIVEN prazo cadastrado, WHEN OS é concluída, THEN data-limite-garantia = data-conclusão + prazo.

**Invariantes:** `INV-001` (audit trail), `INV-026` (preservação histórica).

---

### US-GAR-002: abrir OS em garantia referenciando OS-mãe

**Como** atendente, **quero** abrir OS marcada como "em garantia" apontando a OS original / venda / peça, **para** rastrear o vínculo e não cobrar o cliente até a análise.

**AC:**
- **AC-GAR-002-1:** GIVEN OS original concluída há ≤ prazo-garantia, WHEN abre OS-filha "em garantia", THEN sistema vincula e marca status financeiro como BLOQUEADO_GARANTIA.
- **AC-GAR-002-2:** GIVEN OS original fora do prazo, WHEN tenta abrir como garantia, THEN sistema avisa "fora do prazo" e exige aprovação do gerente para forçar.

**Invariantes:** `INV-001`.

---

### US-GAR-003: analisar garantia procedente ou improcedente

**Como** técnico/metrologista, **quero** registrar análise (procedente, improcedente, parcial) com laudo, **para** decidir cobrança e alimentar reincidência.

**AC:**
- **AC-GAR-003-1:** GIVEN OS em garantia EM_EXECUCAO, WHEN técnico fecha análise como PROCEDENTE com laudo, THEN cobrança permanece BLOQUEADA e dispara `GarantiaProcedente`.
- **AC-GAR-003-2:** GIVEN análise IMPROCEDENTE com laudo, THEN cobrança é LIBERADA com custo total e dispara `GarantiaImprocedente`.
- **AC-GAR-003-3:** GIVEN análise PARCIAL, THEN sistema permite cobrar apenas parcela definida em laudo (revisada por gerente).

**Invariantes:** `INV-001`, `INV-013` (laudo é dado sensível do cliente do lab).

---

### US-GAR-004: separar custo da garantia

**Como** gerente operacional, **quero** que custo de mão de obra, peça e deslocamento da OS em garantia procedente fique segregado, **para** medir custo real de retrabalho.

**AC:**
- **AC-GAR-004-1:** GIVEN OS em garantia procedente concluída, WHEN apropria custos, THEN sistema lança em conta CUSTO_GARANTIA (não em RECEITA_PERDIDA nem em CUSTO_SERVIÇO normal).
- **AC-GAR-004-2:** GIVEN custo lançado, WHEN consulta dashboard, THEN custo aparece por mês, por tipo, por cliente, por técnico.

---

### US-GAR-005: bloquear cobrança em OS de garantia

**Como** sistema, **quero** bloquear emissão de NF/cobrança quando OS está marcada em garantia procedente, **para** evitar erro humano de faturamento.

**AC:**
- **AC-GAR-005-1:** GIVEN OS em garantia procedente, WHEN financeiro tenta emitir NF, THEN sistema bloqueia com mensagem "OS em garantia — cobrança bloqueada — aprove desbloqueio com motivo".
- **AC-GAR-005-2:** GIVEN desbloqueio manual aprovado por gerente com motivo, THEN audit log grava quem, quando e por quê (`INV-001`).

**Invariantes:** `INV-001`.

---

### US-GAR-006: controlar garantia do fornecedor (envio e retorno)

**Como** comprador, **quero** registrar envio de peça defeituosa ao fornecedor, NF de remessa, prazo de retorno e ressarcimento, **para** não perder dinheiro com peça em garantia do fornecedor.

**AC:**
- **AC-GAR-006-1:** GIVEN peça substituída em garantia procedente, WHEN abre garantia-fornecedor, THEN sistema registra fornecedor, nota de remessa, data envio, prazo de retorno esperado.
- **AC-GAR-006-2:** GIVEN prazo de retorno vencido, WHEN dispara cron, THEN sistema notifica comprador.
- **AC-GAR-006-3:** GIVEN retorno do fornecedor (peça nova ou crédito), THEN registra valor ressarcido e fecha o ciclo.

---

### US-GAR-007: medir reincidência

**Como** gerente operacional, **quero** ver indicador de reincidência (cliente que abre 3+ garantias em 6 meses, peça-modelo com 5+ garantias procedentes, técnico com 4+ garantias procedentes), **para** agir em causa raiz.

**AC:**
- **AC-GAR-007-1:** GIVEN N+ garantias procedentes em janela X, WHEN consulta dashboard, THEN entidade aparece marcada como REINCIDENTE com link pras OS-fonte.
- **AC-GAR-007-2:** GIVEN flag REINCIDENTE em peça-modelo, WHEN nova OS usa essa peça, THEN sistema avisa o técnico no app.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Primárias: custo total de garantia / mês; % OS em garantia procedente; taxa de reincidência por peça-modelo.

## 8. NFR

- Audit log imutável (`INV-001`)
- Confidencialidade do laudo (`INV-013`)
- WCAG 2.1 AA (`INV-016`) na tela de análise e portal-cliente quando exposto
- Mobile precisa marcar "em garantia" no app do técnico (offline ok)

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

US nova → próximo ID `US-GAR-NNN`. Mudança em AC implementado → ADR.
