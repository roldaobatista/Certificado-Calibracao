---
owner: roldao
revisado-em: 2026-05-29
proximo_review: 2026-08-29
status: aceito
aceito-em: 2026-05-29
diataxis: explanation
audiencia: agente
tipo: adr
---

# ADR-0075 — Capacidade interna declarada (perfis B/C/D) é distinta da CMC acreditada (perfil A) — separação terminológica obrigatória

## Contexto

Decisão do Roldão (2026-05-29, AskUserQuestion): **todos os perfis declaram
capacidade** no módulo `escopos-cmc` (contra a recomendação inicial de gated-A). A
revisão do `consultor-rbc-iso17025` (NC-02 ALTO) confirmou que a **modelagem** está
correta — `rbc_acreditado=false` forçado server-side para não-A (anti-fraude INV-015
/ ADR-0067 / FAIL L6 do SAN-PERFIL); bloqueio 412 só para A — **mas alertou um risco
de RÓTULO**:

O termo **"CMC" / "Capacidade de Medição e Calibração"** é **regulado**: na cultura
RBC, é termo do **escopo de acreditação CGCRE**. Usar "CMC" para um tenant perfil
B/C/D **não acreditado** pode induzir o cliente (e um auditor casual) a achar que o
número tem lastro CGCRE. Isso é exatamente o tipo de **declaração enganosa de
competência** que a ISO 17025 cl. 8.1.3 (uso indevido de acreditação) e o INMETRO
repudiam.

## Decisão

1. **A modelagem de dados é compartilhada, a apresentação é separada.** A mesma
   coluna `cmc_valor`/entidade `EscopoCMC` serve A e B/C/D; o discriminador é
   `rbc_acreditado` (true só para A, fail-closed `tenant_perfil_e(['A'])`; **forçado
   false** server-side para B/C/D).
2. **Separação terminológica obrigatória na UI / certificado:**
   - **Perfil A (acreditado RBC):** rótulo **"CMC (menor incerteza declarada)"**
     (decisão L do Roldão) + ao lado **"Escopo CGCRE nº [numero_escopo_cgcre]"**.
     Tela: "Escopo de Acreditação CGCRE".
   - **Perfis B/C/D (não acreditado):** rótulo **"Capacidade interna declarada
     (sem acreditação RBC)"** / "Menor incerteza interna (não acreditada)" +
     **badge explícito "NÃO ACREDITADO (sem selo RBC)"**. Tela: "Capacidade interna
     declarada". **NÃO usar o termo "CMC" nem o selo RBC no caminho não-acreditado.**
3. **Bloqueio 412 `EscopoNaoCobreFaixa` / `IncertezaAbaixoDoCMC` é RBC-only**
   (perfil A). Para B/C/D, no máximo um **aviso suave** ("faixa fora da sua
   capacidade interna declarada"), nunca bloqueio duro (calibração não-A não carrega
   selo RBC).
4. **Mensagens canônicas** (terminologia que o cliente lê):
   - 412 RBC: "Faixa fora do escopo acreditado CGCRE nº XXXX — não é possível emitir
     como RBC. CMC declarada: [valor]."
   - 412 U<CMC (ADR-0074): "Incerteza calculada ([U]) é menor que a CMC declarada
     ([CMC]) — não permitido em RBC (ILAC-P14). Revise o orçamento de incerteza."
   - Aviso B/C/D: "Faixa fora da sua capacidade interna declarada."

## Non-goals desta ADR

- NÃO reabre a decisão do Roldão (todos declaram) — confirma a modelagem.
- NÃO altera a trava anti-fraude (`rbc_acreditado` forçado false p/ não-A continua).
- NÃO define a matriz feature×perfil completa (entra em `matriz-feature-perfil.md`
  no `/implement`).

## Consequências

**Positivas:**
- Honra a decisão do Roldão (todos declaram, label "CMC" p/ A) sem criar risco de
  declaração enganosa de competência (cl. 8.1.3) para B/C/D.
- O dado é reusado (uma entidade), a confusão é evitada (rótulo+badge distintos).

**Negativas (aceitas):**
- UI condicional por perfil (rótulo/badge mudam) — complexidade de template a mais.
  Aceito: é proteção regulatória, não cosmética.

## Decisão de produto reportada ao Roldão

Esta ADR **refina** a decisão L ("CMC (menor incerteza declarada)") + O (todos
declaram) do Roldão, mantendo o rótulo dele para perfil A e adicionando rótulo
distinto para B/C/D **por exigência normativa** (cl. 8.1.3). Reportado ao Roldão com
**veto aberto** — se ele preferir terminologia diferente para o caminho não-acreditado,
ajusta-se; o que NÃO se abre mão é da separação visível entre acreditado e não-acreditado.

## Dependências

- **Depende de:** ADR-0067 (perfil regulatório), ADR-0040 (entidade separada),
  INV-015 (anti-fraude RBC).
- **Relaciona:** ADR-0074 (cobertura RBC — só A), ADR-0066 (fail-open lazy).

## Status

ACEITO em 2026-05-29 como conserto da NC-02 (ALTO) da revisão RBC do plan M6
`escopos-cmc`. Reconciliação em `docs/faseamento/M6-escopos-cmc/reviews-consolidado.md`.
