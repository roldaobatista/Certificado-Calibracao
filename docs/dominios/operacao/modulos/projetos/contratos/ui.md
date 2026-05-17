---
owner: Roldão
revisado-em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
modulo: projetos
dominio: operacao
---

# Contratos de UI — Módulo Gestão de Projetos

> Telas + comportamento. Wireframe textual enquanto stack candidata.

---

## Telas

### Tela 1: Lista de Projetos (Portfolio)

**Propósito:** visão consolidada do portfolio.
**Persona:** P-PRJ-03 Dono, P-PRJ-01 Gerente.
**US:** `US-PRJ-001`, `US-PRJ-005`.
**Acessível por:** menu Operação → Projetos.

**Elementos:**
- Tabela: código, nome, cliente, responsável, status (badge colorida), data_fim_prevista, % concluído, semáforo prazo (verde/amarelo/vermelho), semáforo budget
- Filtros: status, cliente, responsável, faixa de data, semáforo
- Botão "Novo projeto"
- KPIs no topo: total ativos, em risco, concluídos no mês

**Estados:** vazio → CTA "Criar primeiro projeto"; carregando → skeleton; erro → mensagem PT.
**A11y:** WCAG AA (`INV-016`).
**Mobile:** lista compacta read-only.

---

### Tela 2: Cadastro / Detalhe do Projeto

**Propósito:** criar projeto e ver visão única.
**Persona:** P-PRJ-01 Gerente.
**US:** `US-PRJ-001`.
**Acessível por:** botão "Novo projeto" ou click na lista.

**Elementos (cadastro):**
- Campos: código (auto-sugestão), nome, cliente (autocomplete CRM), responsável, datas previstas, orçamento, receita prevista, descrição
- Validação: cliente bloqueado financeiramente → bloqueia salvar com mensagem

**Elementos (detalhe — tabs):**
- "Visão geral" — semáforos, KPIs, próximo marco
- "Cronograma" → Tela 3
- "Etapas" → Tela 4
- "Orçamento" → Tela 5
- "Riscos" → Tela 6
- "Diário" → Tela 7
- "Documentos" → Tela 8
- "Aditivos" → Tela 9
- "OSs vinculadas" — lista com link ao módulo OS
- "Reuniões" — atas

---

### Tela 3: Gantt do Projeto

**Propósito:** visualizar cronograma e atrasos.
**Persona:** P-PRJ-01 Gerente, P-PRJ-02 Responsável.
**US:** `US-PRJ-004`.
**Acessível por:** aba "Cronograma" no detalhe.

**Elementos:**
- Barras por etapa (previsto + realizado em sobreposição)
- Marcos como losangos
- Hoje destacado por linha vertical
- Zoom (dia/semana/mês)
- Drag-and-drop pra ajustar (gera evento de auditoria)

**Estados:** atraso → barra realizada vermelha; antecipado → verde claro.
**Mobile:** read-only.

---

### Tela 4: Etapas + Aceite

**Propósito:** detalhar etapa, marcar conclusão, registrar aceite.
**Persona:** P-PRJ-01, P-PRJ-02, P-PRJ-04 (portal).
**US:** `US-PRJ-002`, `US-PRJ-007`.

**Elementos:**
- Lista ordenada de etapas (drag pra reordenar enquanto não iniciada)
- Detalhe da etapa: tarefas, entregáveis, marco_de_faturamento, valor_faturamento
- Botão "Marcar concluída" → exige entregáveis ENTREGUE
- Bloco "Aceite do cliente": nome+CPF do representante, observação, opção "assinatura digital" → integração Lacuna (`INV-017` quando aplicável)
- Após aceite → marca habilitado para faturamento + dispara `Marco.Atingido`

---

### Tela 5: Orçamento Previsto vs Realizado

**Propósito:** comparar e ver margem.
**Persona:** P-PRJ-01, P-PRJ-03.
**US:** `US-PRJ-005`.

**Elementos:**
- Tabela: categoria, descrição, valor_previsto, valor_realizado, % consumido
- Gráfico de barras lado a lado
- KPI "margem atual" com cor (verde > 15%, amarelo 5–15%, vermelho < 5%)
- Botão "Exportar XLSX" → Export 2 (ver `exports.md`)

---

### Tela 6: Riscos

**Persona:** P-PRJ-01, P-PRJ-02.
**US:** `US-PRJ-006`.

**Elementos:**
- Matriz 5x5 (probabilidade × impacto) com riscos plotados
- Lista com plano de mitigação, responsável, prazo
- Botão "Novo risco"

---

### Tela 7: Diário de Execução

**Persona:** P-PRJ-02 (campo + bancada).
**US:** `US-PRJ-006`.

**Elementos:**
- Timeline reversa (mais recente no topo)
- Entrada: data, autor, texto, anexos (fotos do campo)
- Botão "Nova entrada" — mobile permite offline (sync depois)
- Sem editar/excluir (imutável `INV-001`)

---

### Tela 8: Documentos

**Elementos:**
- Lista por tipo (contrato/planta/ata/relatório)
- Upload com versão automática
- Visualizador inline (PDF/imagem)
- Histórico de versões

---

### Tela 9: Aditivos

**Persona:** P-PRJ-01, P-PRJ-03.
**US:** `US-PRJ-008`.

**Elementos:**
- Lista de aditivos por versão
- Formulário: motivo, alteração de escopo, dias a adicionar, valor adicional
- Workflow PROPOSTO → APROVADO/REJEITADO (gerente/dono aprova)
- Visualização "contrato consolidado" mostrando original + N aditivos somados

---

### Tela 10: Portal do Cliente

**Persona:** P-PRJ-04.
**US:** `US-PRJ-004`, `US-PRJ-007`.

**Elementos:**
- Visão simplificada: Gantt read-only, etapas, documentos liberados, aceites pendentes
- Botão "Assinar aceite" → fluxo digital (`INV-017` quando aplicável)
- WCAG AA estrito (`INV-016` — portal exposto a usuário externo)

---

## Componentes reutilizáveis

Gantt, semáforos, autocomplete-cliente vão pra `../../../comum/contratos/ui.md` quando 2+ módulos usarem.

## Como evolui

Tela nova → adicionar + linkar US. Mudança UX → CHANGELOG.
