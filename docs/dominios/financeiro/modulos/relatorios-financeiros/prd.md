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
  - docs/dominios/financeiro/modulos/contas-receber/prd.md
  - docs/dominios/financeiro/modulos/contas-pagar/prd.md
  - docs/dominios/financeiro/modulos/despesas/prd.md
  - docs/dominios/financeiro/modulos/comissoes/prd.md
  - docs/dominios/financeiro/modulos/custeio-real/prd.md
  - docs/dominios/financeiro/modulos/fiscal/prd.md
  - docs/dominios/financeiro/modulos/billing-saas/prd.md
---

# PRD — Módulo Relatórios Financeiros

> Camada analítica do domínio financeiro. Consome dados de **todos** os módulos do domínio (contas a receber, contas a pagar, despesas, comissões, custeio real, fiscal, billing-SaaS, caixa do técnico) e entrega visões consolidadas: DRE, fluxo de caixa, aging, centro de custo, resultados por dimensão.

---

## 1. O que este módulo é

Hub analítico do financeiro. Não cria lançamentos novos — apenas **lê, consolida e apresenta**. Entrega DRE (gerencial), fluxo de caixa (realizado + projetado), aging de recebíveis e pagáveis, gasto por centro de custo, conciliação bancária e resultados por dimensão (cliente, técnico, vendedor, serviço, OS, viagem).

É o módulo que o gestor/dono abre para responder "estou ganhando dinheiro? com quem? com o quê? quando o caixa vai apertar?".

## 2. Por que este módulo existe

Dor mapeada em `docs/discovery/dores-mapeadas.md` (DOR-FIN-RFN): hoje o gestor exporta CSV de cada módulo, joga em planilha, perde a noite cruzando, e na semana seguinte os números já estão velhos. Sem visão de fluxo projetado, sem visão de resultado por dimensão, sem aging confiável.

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` + `docs/comum/personas.md`.

## 4. Escopo (o que ESTÁ neste módulo)

- DRE gerencial (não contábil oficial — esse vive em `fiscal/` quando contador for cliente).
- Fluxo de caixa realizado (período fechado).
- Fluxo de caixa projetado (recebíveis + pagáveis futuros + recorrência de `billing-saas/`).
- Aging de recebíveis (`contas-receber/`).
- Aging de pagáveis (`contas-pagar/`).
- Receitas por período (consolidado de `contas-receber/` + `billing-saas/`).
- Despesas por período (consolidado de `contas-pagar/` + `despesas/`).
- Resultado por dimensão: cliente, técnico, vendedor, serviço, OS, centro de custo.
- Conciliação bancária (extrato vs. lançamentos).
- Drill-down de cada número até o lançamento de origem.
- Export PDF / XLSX / CSV.

## 5. Non-goals (o que NÃO está neste módulo)

- Criar/editar lançamento financeiro (vive em cada módulo de origem).
- DRE contábil oficial / SPED / livros fiscais (vivem em `fiscal/`).
- Forecast estatístico (machine learning / sazonalidade) — fase posterior.
- Dashboards para clientes finais (esse módulo é interno).
- Substituir BI externo (Power BI, Metabase) — oferece export, não compete.
- Cálculo de comissão (vive em `comissoes/`); aqui só visualiza resultado.
- Conciliação automática por IA — fase posterior; MVP é matching por regra.

## 6. User Stories

### US-RFN-001: Ver DRE gerencial do período

**Como** gestor/dono, **quero** ver receitas, custos diretos, despesas, resultado bruto e líquido do período, **para** saber se estou ganhando dinheiro.

**Critérios de aceite:**
- **AC-RFN-001-1**: GIVEN período selecionado, WHEN abre DRE, THEN linhas são: receita bruta, deduções, receita líquida, custo direto (custeio-real), lucro bruto, despesas operacionais, lucro operacional, resultado financeiro, lucro líquido.
- **AC-RFN-001-2**: GIVEN clique em uma linha, WHEN expande, THEN mostra composição por categoria.
- **AC-RFN-001-3**: GIVEN clique em valor de categoria, WHEN drill-down, THEN abre lista de lançamentos de origem.

**Non-goals:** versão contábil oficial.

**Invariantes:** `INV-MULTI-TENANT-001`, `INV-RFN-001` (números sempre rastreáveis a lançamentos).

**Dependências:** Bloqueado por: `contas-receber/`, `contas-pagar/`, `despesas/`, `custeio-real/`.

---

### US-RFN-002: Ver fluxo de caixa realizado

**Como** financeiro, **quero** ver entradas e saídas efetivas do período por dia/semana/mês, **para** entender o que aconteceu no caixa.

**Critérios de aceite:**
- **AC-RFN-002-1**: GIVEN período, WHEN abre fluxo realizado, THEN linhas são as entradas e saídas liquidadas com saldo acumulado.
- **AC-RFN-002-2**: GIVEN granularidade trocada, WHEN escolhe dia/semana/mês, THEN agrupamento se ajusta.

**Dependências:** Bloqueado por: `contas-receber/`, `contas-pagar/`, `despesas/`.

---

### US-RFN-003: Ver fluxo de caixa projetado

**Como** gestor, **quero** ver projeção de caixa nos próximos 30/60/90 dias, **para** antecipar aperto e tomada de crédito.

**Critérios de aceite:**
- **AC-RFN-003-1**: GIVEN janela escolhida, WHEN abre projetado, THEN soma recebíveis em aberto + pagáveis em aberto + recorrências de `billing-saas/` + folha + assinaturas previstas.
- **AC-RFN-003-2**: GIVEN data sem fundos, WHEN renderiza, THEN sinaliza dia em vermelho com motivo.

**Non-goals:** previsão estatística.

**Dependências:** `contas-receber/`, `contas-pagar/`, `billing-saas/`.

---

### US-RFN-004: Ver aging de recebíveis e pagáveis

**Como** financeiro, **quero** ver títulos a receber e a pagar agrupados por faixa de atraso (0-30, 31-60, 61-90, 90+), **para** priorizar cobrança e renegociação.

**Critérios de aceite:**
- **AC-RFN-004-1**: GIVEN data-base = hoje, WHEN abre aging, THEN títulos em aberto aparecem agrupados por faixa.
- **AC-RFN-004-2**: GIVEN clique em faixa, WHEN expande, THEN lista clientes/fornecedores com valor.

---

### US-RFN-005: Ver gasto por centro de custo

**Como** gestor, **quero** ver despesas e custos agrupados por centro de custo, **para** entender onde a empresa gasta.

**Critérios de aceite:**
- **AC-RFN-005-1**: GIVEN período, WHEN abre centro de custo, THEN tabela mostra cada centro com total, % do total e variação vs. período anterior.

---

### US-RFN-006: Conciliar extrato bancário

**Como** financeiro, **quero** importar extrato bancário (OFX/CSV) e comparar com lançamentos do sistema, **para** identificar diferenças.

**Critérios de aceite:**
- **AC-RFN-006-1**: GIVEN arquivo OFX/CSV importado, WHEN sistema processa, THEN cada linha é classificada como conciliada / divergente / não-encontrada.
- **AC-RFN-006-2**: GIVEN linha divergente, WHEN financeiro confirma manualmente, THEN matching é gravado para histórico.

**Non-goals:** matching por IA na primeira versão.

---

### US-RFN-007: Receitas e despesas por período

**Como** gestor, **quero** comparar receitas e despesas em períodos diferentes (mês, trimestre, ano, custom), **para** ver tendência.

**Critérios de aceite:**
- **AC-RFN-007-1**: GIVEN dois períodos, WHEN compara, THEN sistema mostra delta absoluto e percentual por categoria.

---

### US-RFN-008: Resultado por cliente / técnico / vendedor / serviço

**Como** gestor, **quero** ver lucratividade por cliente, técnico, vendedor ou tipo de serviço, **para** decidir manter, treinar ou cortar.

**Critérios de aceite:**
- **AC-RFN-008-1**: GIVEN dimensão escolhida, WHEN renderiza, THEN linhas mostram receita, custo direto (de `custeio-real/`), margem absoluta e %.
- **AC-RFN-008-2**: GIVEN drill-down, WHEN clica em linha, THEN abre OS / contratos / lançamentos associados.

---

### US-RFN-009: Exportar qualquer relatório

**Como** gestor/financeiro, **quero** exportar qualquer visão em PDF, XLSX ou CSV, **para** enviar ao contador, sócio ou banco.

**Critérios de aceite:**
- **AC-RFN-009-1**: GIVEN qualquer relatório, WHEN clica "Exportar", THEN opção de PDF, XLSX, CSV mantendo filtros aplicados.
- **AC-RFN-009-2**: GIVEN export contém dado pessoal de cliente, WHEN gerado, THEN respeita LGPD: anonimiza ou não conforme RBAC do solicitante.

## 7. Métricas

Ver `metricas.md`. Resumo:
- Tempo de carga DRE período mensal ≤ 2 s p95.
- % números com drill-down funcional = 100%.
- Adoção: % gestores que abrem o módulo ≥ 1×/semana.

## 8. NFR

- **Performance:** consultas pré-agregadas em materialized view; DRE mensal < 2 s p95; aging < 1 s; fluxo projetado 90 dias < 3 s.
- **Disponibilidade:** SLO do domínio financeiro.
- **Segurança:** somente leitura; RBAC restrito por papel; `SEC-LGPD-005` (export anonimizado conforme papel); `INV-MULTI-TENANT-001` em toda query.
- **Acessibilidade:** WCAG AA; tabelas com cabeçalho; gráficos com tabela equivalente.

## 9. Glossário

Ver `glossario.md`.

## 10. Como este PRD evolui

- US nova → próximo ID livre `US-RFN-NNN`.
- US deprecada → `@deprecated` + ADR.
- Mudança em AC implementado → ADR + novo teste.
