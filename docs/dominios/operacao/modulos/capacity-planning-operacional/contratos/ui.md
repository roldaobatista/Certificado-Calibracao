---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: capacity-planning-operacional
dominio: operacao
---

# Contratos UI — Capacity Planning Operacional

## Telas

### Tela 1: Painel Consolidado
**Propósito:** visão única da capacidade × demanda por recurso.
**Persona:** P-CPO-01 (gerente).
**US:** US-CPO-003, US-CPO-005, US-CPO-009, US-CPO-011.
**Acessível por:** menu "Planejamento de Capacidade" → "Painel".

**Elementos:**
- Filtros: tipo recurso, equipe, laboratório, tipo serviço, janela (4/8/12 semanas)
- Heatmap recurso × semana com cor por taxa de ocupação (verde ≤70%, amarelo 70-85%, laranja 85-100%, vermelho >100%)
- Lista lateral de gargalos abertos
- KPIs no topo: capacidade total, ocupação média, gargalos abertos, sobrecargas

**Estados:**
- Vazio: "Cadastre recursos e capacidade base para começar."
- Carregando: skeleton heatmap.
- Erro: "Falha ao recalcular. Mostrando dados de [timestamp]."

**A11y:** WCAG AA, heatmap com etiquetas textuais (não só cor).
**Mobile:** painel simplificado em lista.

---

### Tela 2: Cadastro de Recurso e Capacidade
**Propósito:** registrar técnico/equipe/laboratório e suas horas.
**Persona:** P-CPO-01, P-CPO-03.
**US:** US-CPO-001, US-CPO-002.

**Elementos:**
- Form: tipo (técnico|equipe|laboratório), referência, ativo
- Form aninhado capacidade base: horas/semana, dias úteis (checkbox)
- Lista de ausências/manutenções programadas
- Para laboratório: bancadas (quantidade), equipamentos-padrão, turnos

---

### Tela 3: Widget de Disponibilidade (em Chamado/Orçamento/OS)
**Propósito:** atendente vê semáforo antes de prometer prazo.
**Persona:** P-CPO-02.
**US:** US-CPO-004.

**Elementos:**
- Componente embutido no fluxo: input "data prometida"
- Semáforo: verde (folga), amarelo (apertado), vermelho (não cabe)
- Sugestão "próxima data verde" quando vermelho/amarelo

---

### Tela 4: Simulação de Cenário
**Propósito:** rodar "e se" sem afetar real.
**Persona:** P-CPO-01.
**US:** US-CPO-006.

**Elementos:**
- Nome da simulação, descrição
- Editor: adicionar/remover OS hipotéticas, mudar técnico, alterar capacidade temporariamente
- Painel resultado: comparação lado-a-lado real × simulado
- Botões: salvar | aplicar (transforma em real) | descartar

---

### Tela 5: Sugestão de Distribuição (dentro de OS)
**Propósito:** sistema sugere técnico/equipe para a OS.
**Persona:** P-OP-04 / P-CPO-01.
**US:** US-CPO-007.

**Elementos:**
- Lista de recursos elegíveis ordenados por score (capacidade + skill + custo + proximidade geográfica)
- Cada item: nome, ocupação atual, horas necessárias, semáforo
- Botão "atribuir" por item + opção "outro recurso" (override manual)

---

### Tela 6: Tempo Médio por Tipo de OS
**Propósito:** ver previsto vs realizado por tipo.
**Persona:** P-CPO-01.
**US:** US-CPO-008.

**Elementos:**
- Tabela: tipo serviço, tempo médio histórico, override manual, erro mediano %, última atualização
- Botão "definir override" e "voltar pro automático"

---

### Tela 7: Indicação de Contratação
**Propósito:** painel de necessidade de contratação.
**Persona:** P-CPO-01.
**US:** US-CPO-010.

**Elementos:**
- Lista de indicações abertas: tipo serviço, FTE sugerido, horizonte, justificativa
- Botões: encaminhar pra RH | rejeitar | marcar atendida

---

## Componentes reutilizáveis

Heatmap e semáforo de capacidade são candidatos a `../../../comum/contratos/ui.md` (também usados em Agenda).
