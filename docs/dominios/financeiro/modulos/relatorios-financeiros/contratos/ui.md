---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Relatórios Financeiros

> Telas analíticas. Toda tela precisa permitir drill-down e export (invariante).

---

## Tela 1: DRE gerencial

**Propósito:** mostrar receitas → custos → despesas → lucro do período.
**Persona:** Dono/gestor.
**US:** `US-RFN-001`.
**Acessível por:** menu Financeiro → Relatórios → DRE.

**Elementos:**
- Seletor de período (mês corrente default; trimestre; ano; custom).
- Comparativo opcional com período anterior.
- Tabela com linhas: Receita bruta → Deduções → Receita líquida → Custo direto → Lucro bruto → Despesas operacionais → Lucro operacional → Resultado financeiro → Lucro líquido.
- Cada célula com valor é clicável (drill-down).
- Botão "Exportar" (PDF/XLSX/CSV).
- Botão "Salvar visão" + "Agendar envio".

**Estados:**
- Vazio: "Sem lançamentos no período."
- Carregando: skeleton.
- Erro: mensagem PT + botão "Tentar de novo".

**Acessibilidade:** WCAG AA. Tabela com header semântico. Drill-down acessível por teclado.

**Mobile:** versão simplificada (cards).

---

## Tela 2: Fluxo de caixa realizado

**Propósito:** ver entradas/saídas efetivas dia a dia.
**US:** `US-RFN-002`.

**Elementos:**
- Seletor granularidade (dia/semana/mês).
- Tabela: data, descrição agregada, entradas, saídas, saldo acumulado.
- Gráfico de linha do saldo acumulado.
- Drill-down em qualquer linha abre lançamentos do dia.

---

## Tela 3: Fluxo de caixa projetado

**Propósito:** mostrar entradas/saídas previstas em janela 30/60/90 dias.
**US:** `US-RFN-003`.

**Elementos:**
- Seletor janela (30/60/90/custom).
- Tabela com dia, entradas previstas, saídas previstas, saldo projetado.
- Dia com saldo negativo destacado em vermelho.
- Toggle "Considerar recorrências de assinatura SaaS".
- Drill-down em valor abre títulos que compõem.

---

## Tela 4: Aging

**Propósito:** títulos em aberto por faixa.
**US:** `US-RFN-004`.

**Elementos:**
- Seletor "A receber" / "A pagar" / "Ambos".
- Tabela: faixa (0-30, 31-60, 61-90, 90+), quantidade, valor total, % do total.
- Drill: clica faixa → lista por cliente/fornecedor.

---

## Tela 5: Centro de custo

**Propósito:** ver gasto por centro.
**US:** `US-RFN-005`.

**Elementos:**
- Tabela: centro, total, % do total, variação vs. período anterior.
- Gráfico de barras horizontal.
- Drill: clica centro → lista lançamentos.

---

## Tela 6: Conciliação bancária

**Propósito:** importar extrato, conferir matches, resolver divergências.
**US:** `US-RFN-006`.

**Elementos:**
- Upload OFX/CSV.
- Lista de linhas com status (conciliada / divergente / não-encontrada).
- Para cada divergência: sugestão de matching + botão "Confirmar" / "Criar lançamento avulso".
- Resumo: total conciliado, total pendente, valor divergente.

---

## Tela 7: Receitas / Despesas por período

**Propósito:** comparar dois períodos.
**US:** `US-RFN-007`.

**Elementos:**
- Dois seletores de período.
- Tabela: categoria, período A, período B, delta absoluto, delta %.
- Gráfico de barras comparativo.

---

## Tela 8: Resultado por dimensão

**Propósito:** lucratividade por cliente/técnico/vendedor/serviço.
**US:** `US-RFN-008`.

**Elementos:**
- Seletor dimensão.
- Tabela: nome, receita, custo direto, margem absoluta, margem %.
- Ordenação por margem (default: pior pra melhor — chama atenção).
- Drill: clica linha → OS/contratos associados.

---

## Componentes reutilizáveis

- Seletor de período → comum.
- Tabela com drill-down → comum.
- Exportador (PDF/XLSX/CSV) → comum.

Ver `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → linkar US.
- Mudança UX → bump CHANGELOG.
- Tela `@deprecated` → janela de migração.
