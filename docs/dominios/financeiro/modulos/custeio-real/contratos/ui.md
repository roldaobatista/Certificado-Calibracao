---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Custeio Real

> Telas + comportamento. Stack pós ADR-0001.

---

## Telas

### Tela 1: Detalhe de Custos da OS (dentro da OS)

**Propósito:** mostra apuração completa de uma OS específica.
**Persona principal:** Gestor operacional, Dono.
**US relacionadas:** `US-CUS-001`, `US-CUS-002`.
**Acessível por:** botão "Custos" dentro da tela da OS (módulo Operação).

**Elementos:**
- Cabeçalho: número OS, cliente, técnico, data encerramento.
- Cards-resumo: receita, custo total, margem R$, margem %, badge "DEFICITÁRIA" se aplicável.
- Tabela "Previsto × Realizado":
  - Colunas: categoria, previsto R$, realizado R$, variação R$, variação %.
  - Linhas: mão de obra, deslocamento, hospedagem, alimentação, pedágio, peças, retrabalho, garantia, comissão.
  - Linhas com variação > threshold em laranja/vermelho.
- Bloco "Versões de apuração" (quando OS foi reaberta): lista versões com data + diff.
- Botão "Solicitar reapuração" (papel autorizado).
- Bloco "Origem dos custos": cada linha clicável → drilldown pra entidade fonte (saída de estoque, lançamento caixa técnico, etc.).

**Estados:**
- OS ainda não apurada: mensagem "Custo real ainda não apurado. Aguarde insumos."
- Apuração em andamento: spinner + "Processando..."
- Apuração com erro (insumo faltante): aviso "Falta dado X — clique pra ver".

**Mobile:** responsivo (tabela vira cards).

---

### Tela 2: Dashboard "Minha Margem" (dono)

**Propósito:** visão consolidada da rentabilidade do tenant.
**Persona principal:** Dono.
**US relacionadas:** `US-CUS-003`.

**Elementos:**
- Filtro de período (mês atual / últimos 3 / últimos 12 / customizado).
- Cards: receita do período, custo total, margem R$, margem %, count OSs, count deficitárias.
- Gráfico de linha: margem % mensal (12 meses).
- Tabela "Top 10 OSs por margem (melhores)" e "Top 10 piores".
- Botão pra exportar XLSX/CSV.

---

### Tela 3: Ranking por Cliente

**Propósito:** ordenar clientes por margem.
**US:** `US-CUS-003`.

**Elementos:**
- Filtro período.
- Tabela: cliente, receita, custo, margem R$, margem %, count OSs, % retrabalho, flag deficitário.
- Ordenação por qualquer coluna (default: pior margem primeiro pra visibilidade).
- Click no cliente → drilldown OSs do cliente no período.

---

### Tela 4: Ranking por Técnico

**Propósito:** identificar técnicos mais/menos rentáveis e com mais retrabalho/garantia.
**US:** `US-CUS-003`.

**Elementos:**
- Filtro período.
- Tabela: técnico, count OSs, receita gerada, custo mão de obra, custo retrabalho, custo garantia, margem média, % retrabalho.
- Aviso de uso responsável: "Dados sensíveis — RBAC restrito".

---

### Tela 5: Ranking por Vendedor

**Propósito:** identificar vendedores cujas vendas geram OSs deficitárias.
**Elementos:** análogo Tela 4 com lente em vendedor.

---

### Tela 6: Ranking por Tipo de Serviço

**Propósito:** identificar serviços com margem baixa (candidatos a reprecificação).
**Elementos:** análogo Tela 4 com lente em tipo de serviço; aqui garantia ganha destaque.

---

### Tela 7: Lista de Alertas Deficitários

**Propósito:** fila de revisão pro gestor.
**Persona principal:** Gestor operacional.
**US:** `US-CUS-004`.

**Elementos:**
- Filtros: status (aberto/em revisão/tratado), período, técnico, cliente.
- Tabela: OS, cliente, técnico, margem %, criado em, status.
- Click → tela de detalhe (Tela 1) + campo "Tratamento" com nota e botão "Marcar tratado".

---

### Tela 8: Configuração de Parâmetros de Custeio (admin)

**Propósito:** dono configura hora-base, custo/km, threshold de alerta.
**Persona principal:** Dono/admin.
**US:** `US-CUS-007`.

**Elementos:**
- Lista de parâmetros agrupados (Globais, Por Técnico, Por Serviço).
- Cada linha editável; mudança cria nova versão (mostra histórico).
- Aviso: "Mudanças só afetam OSs FUTURAS. Histórico mantém valores vigentes na data."

---

## Componentes reutilizáveis

- Tabela rankings (compartilhada com `comissoes/`).
- Card "DEFICITÁRIA" — padrão visual de alerta.

## Como esta lista evolui

- Tela nova → ligar a US.
- Mudança em RBAC de telas sensíveis → ADR.
