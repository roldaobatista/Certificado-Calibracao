---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/prd.md
  - docs/dominios/financeiro/README.md
  - docs/dominios/financeiro/modulos/caixa-tecnico/prd.md
  - docs/dominios/financeiro/modulos/contas-pagar/prd.md
---

# PRD — Módulo Despesas

> Despesas corporativas: lançamento, comprovante, aprovação, reembolso e vínculo a OS / viagem / técnico.
>
> **Recorte deste módulo:** despesa formal **corporativa** (qualquer colaborador / qualquer área), incluindo despesa de técnico em campo que vira pedido de reembolso. O fluxo operacional de **adiantamento + saldo em tempo real do técnico** continua em `caixa-tecnico/` — este módulo consome aquele como sub-componente quando a despesa do técnico for prestada via caixa.

---

## 1. O que este módulo é

Hub único de **despesas corporativas** do ERP: qualquer colaborador (técnico, administrativo, vendedor, gestor) registra despesa, anexa comprovante, manda pra aprovação e — se aprovada — vira reembolso ou compensa adiantamento. Cada despesa pode ter vínculo opcional com **OS**, **viagem** e **técnico**, o que alimenta custo real (`custeio-real/`), resultado por OS e indicadores de Relatórios Financeiros.

Hoje parte do fluxo está parcial em `caixa-tecnico/` (técnico em campo). Este módulo é o **fluxo formal corporativo**: despesas administrativas, despesas de vendedores, despesas de viagem agendada, reembolso pós-fato — tudo que não passa por adiantamento ao caixa do técnico.

## 2. Por que este módulo existe

Dor mapeada em `docs/discovery/dores-mapeadas.md` (DOR-FIN-DSP): hoje despesas vivem em planilha + WhatsApp + foto de nota fiscal solta. Sem aprovação rastreável, sem vínculo com OS (impossível saber custo real do atendimento), sem reembolso auditável.

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- Lançamento de despesa (data, valor, categoria, descrição, centro de custo).
- Anexo de comprovante (foto, PDF, XML de cupom fiscal).
- Fluxo de aprovação configurável (1 ou N níveis, alçada por valor).
- Reembolso ao colaborador (gera pagamento em `contas-pagar/`).
- Compensação contra adiantamento existente (consulta `caixa-tecnico/`).
- Vínculo opcional com OS, viagem e técnico.
- Categorização (combustível, alimentação, hospedagem, peça, terceiros, outros).
- Histórico de aprovação / rejeição com motivo.
- Exportação para conciliação contábil.

## 5. Non-goals (o que NÃO está neste módulo)

- Adiantamento ao técnico e saldo em tempo real (vive em `caixa-tecnico/`).
- Pagamento efetivo da despesa (vive em `contas-pagar/`).
- Cálculo de impostos retidos no reembolso (vive em `fiscal/`).
- Política de viagem (diárias, classes, tetos) — vive em RH/Compliance, fora do MVP.
- Cartão corporativo com extrato automático — fase posterior.
- OCR de cupom fiscal para preenchimento automático — fase posterior.

## 6. User Stories

### US-DSP-001: Lançar despesa com comprovante

**Como** colaborador, **quero** registrar uma despesa anexando o comprovante, **para** solicitar reembolso ou prestar conta de adiantamento.

**Critérios de aceite:**
- **AC-DSP-001-1**: GIVEN colaborador autenticado, WHEN cria despesa com data, valor, categoria, descrição e arquivo de comprovante, THEN despesa é gravada em status `pendente_aprovacao` e comprovante fica armazenado.
- **AC-DSP-001-2**: GIVEN despesa sem comprovante anexo, WHEN tenta enviar para aprovação, THEN sistema bloqueia com mensagem clara.
- **AC-DSP-001-3**: GIVEN comprovante anexado, WHEN salvo, THEN hash do arquivo é registrado para trilha de auditoria.

**Non-goals desta story:**
- OCR automático do comprovante.

**Invariantes:** `INV-MULTI-TENANT-001`, `INV-WORM-001` (trilha imutável do comprovante).

**Dependências:** Bloqueado por: ADR-0001 (stack), ADR-0002 (multi-tenant), módulo Storage.

---

### US-DSP-002: Aprovar / rejeitar despesa por alçada

**Como** gestor com alçada, **quero** aprovar ou rejeitar despesas dentro do meu limite, **para** controlar gasto antes de gerar pagamento.

**Critérios de aceite:**
- **AC-DSP-002-1**: GIVEN despesa pendente dentro da alçada do gestor, WHEN aprova, THEN despesa muda para `aprovada` e dispara evento `Despesa.Aprovada`.
- **AC-DSP-002-2**: GIVEN valor acima da alçada, WHEN gestor abre, THEN sistema escalona para próximo nível e bloqueia ação dele.
- **AC-DSP-002-3**: GIVEN rejeição, WHEN gestor confirma com motivo obrigatório, THEN despesa muda para `rejeitada` e colaborador é notificado.

**Invariantes:** `INV-AUDIT-001`.

**Dependências:** Bloqueia: US-DSP-003.

---

### US-DSP-003: Gerar reembolso da despesa aprovada

**Como** financeiro, **quero** que despesa aprovada gere conta a pagar para o colaborador, **para** efetuar o reembolso.

**Critérios de aceite:**
- **AC-DSP-003-1**: GIVEN despesa aprovada sem adiantamento vinculado, WHEN financeiro confirma reembolso, THEN cria registro em `contas-pagar/` com favorecido = colaborador.
- **AC-DSP-003-2**: GIVEN despesa aprovada com adiantamento vinculado em `caixa-tecnico/`, WHEN financeiro compensa, THEN despesa abate o saldo do adiantamento e só gera reembolso da diferença, se houver.

**Dependências:** Bloqueado por: `contas-pagar/`, `caixa-tecnico/`.

---

### US-DSP-004: Vincular despesa a OS / viagem / técnico

**Como** colaborador, **quero** vincular a despesa a uma OS, viagem ou técnico, **para** alimentar o custo real do atendimento.

**Critérios de aceite:**
- **AC-DSP-004-1**: GIVEN despesa em lançamento, WHEN escolhe OS aberta, THEN OS aparece como referência e custo entra em `custeio-real/`.
- **AC-DSP-004-2**: GIVEN vínculo com técnico, WHEN despesa aprovada, THEN entra na composição de custo do técnico em `relatorios-financeiros/`.
- **AC-DSP-004-3**: vínculos são opcionais e mutuamente compatíveis.

---

### US-DSP-005: Consultar histórico e situação das despesas

**Como** colaborador ou gestor, **quero** ver despesas filtradas por status, período, categoria e vínculo, **para** acompanhar reembolsos e gasto por centro de custo.

**Critérios de aceite:**
- **AC-DSP-005-1**: GIVEN filtros aplicados, WHEN lista carrega, THEN traz colunas: data, valor, categoria, vínculo, status, aprovador.
- **AC-DSP-005-2**: GIVEN export, WHEN colaborador gera CSV/PDF, THEN respeita os filtros aplicados.

## 7. Métricas

Ver `metricas.md`. Resumo:
- Tempo médio entre lançamento e aprovação ≤ 3 dias úteis.
- % despesas com comprovante anexado = 100% (invariante).
- % despesas vinculadas a OS quando categoria for de campo ≥ 90%.

## 8. NFR

- **Performance:** lista de despesas (até 1000 registros) carrega em < 800 ms p95.
- **Disponibilidade:** SLO igual ao do domínio financeiro.
- **Segurança:** comprovante armazenado em storage com URL pré-assinada e validade curta; `SEC-LGPD-003` (anonimização do CPF do colaborador em export agregado).
- **Acessibilidade:** WCAG AA.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-DSP-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança em AC implementado → ADR + novo teste.
