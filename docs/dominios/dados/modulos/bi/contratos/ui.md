---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/dominios/dados/modulos/bi/prd.md
---

# Contratos de UI — Módulo BI

> Telas + comportamento. Stack final em ADR-0001.

---

## Telas

### Tela 1: Dashboard Executivo (Home do Dono)

**Propósito:** mostrar em 1 tela faturamento, recebíveis, inadimplência, OS abertas.
**Persona principal:** P1 Dono (`../personas.md`).
**US relacionadas:** `US-BI-001`.
**Acessível por:** menu raiz "Início" / link direto após login do dono.

**Elementos:**
- 4 cards principais: faturamento mês, receber 30d, inadimplência (R$ + %), OS abertas.
- Cada card: valor grande, label PT-BR, timestamp última atualização, ícone drill-down.
- Mini-gráfico de tendência (últimos 6 meses) abaixo de cada card.
- Botão "Compartilhar resumo" (gera PDF + e-mail para dono).

**Estados:**
- Vazio: "Sem dados ainda — assim que o primeiro lançamento entrar, aparece aqui."
- Carregando: skeleton dos cards.
- Erro: "Não consegui carregar agora. Estou tentando de novo." + botão "Tentar novamente".
- Sucesso: cards preenchidos + timestamp.

**Acessibilidade:** WCAG AA; navegação teclado obrigatória; paleta com daltonismo (vermelho/verde acompanhado de ícone).

**Mobile:** responsivo (cards empilhados).

---

### Tela 2: Dashboards por Área

**Propósito:** ver indicadores por área (financeiro, comercial, operacional, estoque, qualidade, frota, laboratório).
**Persona:** P2 Gerente.
**US:** `US-BI-002`.
**Acessível por:** menu "Indicadores > Por Área".

**Elementos:**
- Seletor de área (tabs ou dropdown).
- Grid de widgets (configurável por papel).
- Filtro de período (hoje/7d/30d/mês corrente/customizado).

**Estados:** padrão (vazio/loading/erro/sucesso) + estado **bloqueado** (sem permissão para a área).

**Acessibilidade:** WCAG AA.

**Mobile:** responsivo (1 widget por linha em telas pequenas).

---

### Tela 3: Fluxo de Caixa Projetado

**Propósito:** ver saldo dia-a-dia próximos 30/60/90 dias.
**Persona:** P1 Dono.
**US:** `US-BI-003`.

**Elementos:**
- Gráfico de linha temporal.
- Tabela com entradas/saídas dia-a-dia.
- Alerta visual (linha vermelha) quando saldo cruza zero.
- Toggle "incluir/excluir recorrências".

---

### Tela 4: DRE Gerencial

**Propósito:** ver DRE simplificado.
**Persona:** P1 Dono.
**US:** `US-BI-004`.

**Elementos:**
- Seletor de período (mês/trimestre/ano + comparar com período anterior).
- Tabela com linhas: receita, deduções, custo direto, lucro bruto, despesas operacionais, lucro operacional, lucro líquido.
- Coluna de % vertical (cada linha como % da receita).
- Rodapé fixo: "Visão gerencial. Não substitui demonstrativo contábil oficial."

---

### Tela 5: Inadimplência

**Propósito:** lista de clientes inadimplentes + ação de cobrança.
**Persona:** P1, P2.
**US:** `US-BI-005`.

**Elementos:**
- Tabela: cliente, total em atraso, dias máximo de atraso, último contato, botão "Cobrar".
- Ordenação por valor (default), dias, alfabético.
- Filtro por faixa de dias (1-30 / 31-60 / 61-90 / 90+).

---

### Tela 6: Receita por Dimensão

**Propósito:** receita por cliente/serviço/técnico/vendedor.
**Persona:** P1.
**US:** `US-BI-006`.

**Elementos:**
- Seletor de dimensão.
- Gráfico de barras horizontal (top 10).
- Tabela completa abaixo com export.
- Alerta de concentração (cliente > 30% da receita).

---

### Tela 7: Indicadores Operacionais (Produtividade Técnica + SLA)

**Propósito:** ver OS/dia por técnico, tempo médio, taxa retrabalho, SLA cumprido.
**Persona:** P2.
**US:** `US-BI-007`, `US-BI-009`.

**Elementos:**
- Cards de SLA cumprido (% no período).
- Tabela de técnicos com colunas: OS concluídas, tempo médio por tipo, retrabalho.
- Alerta visual de OS prestes a violar SLA.

---

### Tela 8: Funil Comercial (Conversão)

**Persona:** P1, P2 comercial.
**US:** `US-BI-008`.

**Elementos:**
- Visualização em funil (largura por etapa).
- Taxa de conversão entre etapas.

---

### Tela 9: Churn e Segmentação

**Persona:** P1.
**US:** `US-BI-010`, `US-BI-011`.

**Elementos:**
- Janela de inatividade configurável.
- Lista exportável de clientes inativos.
- Segmentador visual com critérios em facetas.

---

### Tela 10: Sugestões Comerciais

**Persona:** vendedor (a definir como P5).
**US:** `US-BI-012`.

**Elementos:**
- Card embutido na ficha do cliente.
- Até 3 sugestões com justificativa simples ("clientes parecidos compraram X").

---

### Tela 11: Manutenção Preditiva

**Persona:** P2 + técnico laboratório.
**US:** `US-BI-013`.

**Elementos:**
- Lista de equipamentos com alerta "manutenção sugerida em X dias".
- Botão "Gerar orçamento preventivo" (integra Comercial).

---

### Tela 12: Construtor de Relatório Customizado

**Persona:** Analista (P3).
**US:** `US-BI-014`.

**Elementos:**
- Painel esquerdo: catálogo de métricas permitidas (RBAC).
- Painel central: filtros + agrupamentos drag-and-drop.
- Painel direito: prévia em tempo real.
- Botões: "Salvar", "Salvar e agendar", "Exportar agora" (CSV/XLSX/PDF).

**Estados:** estado especial "métrica indisponível para seu papel" — métrica fica grayed-out com tooltip.

---

### Tela 13: Agendamento de Envio

**Persona:** Analista, P1.
**US:** `US-BI-015`.

**Elementos:**
- Seletor de relatório/dashboard.
- Cron amigável ("toda segunda às 8h").
- Lista de destinatários + flag "destinatário externo? marcar risco LGPD aceito".
- Histórico das últimas 10 execuções (sucesso/falha).

---

### Tela 14: Link Público de Dashboard

**Persona:** Analista, P1.
**US:** `US-BI-016`.

**Elementos:**
- Toggle "ativar link público".
- Obrigatórios: expiração (data ou nunca-expira-com-aviso), escopo (agregado / cliente específico).
- Opcionais: senha, restrição IP.
- Mostra URL + QR Code + botão "copiar".
- Aviso vermelho: "Qualquer pessoa com este link verá esses dados. LGPD se aplica."
- Botão "Revogar agora" sempre visível.

---

### Tela 15: Visualização Pública (consumida pelo cliente externo)

**Persona:** Cliente externo (Persona 2 do módulo).
**US:** `US-BI-016`.

**Elementos:**
- Apenas o dashboard restrito + branding do tenant.
- Sem menu, sem login (a não ser senha se configurada).
- Rodapé com data da última atualização.

**Estados:**
- Link expirado → página dedicada "link expirado" sem vazar dado.
- Senha errada → tentativa logada; após 5 tentativas, link bloqueado por 1h.

---

## Componentes reutilizáveis

Compartilhados com outros módulos vão pra `../../../comum/contratos/ui.md`:
- Cards de KPI
- Seletor de período
- Tabela exportável
- Gráficos (linha, barra, funil, donut)

## Como esta lista evolui

- Tela nova → adicionar + ligar a US-BI-NNN.
- Mudança UX → bump CHANGELOG.
- Tela descontinuada → `@deprecated`.
