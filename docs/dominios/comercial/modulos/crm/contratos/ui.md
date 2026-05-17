---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
---

# Contratos UI — Módulo CRM

## Telas

### 1. Lista do dia — `/crm` (home do vendedor)
**Propósito:** JTBD-083 — vendedor abre e vê quem priorizar.
**Persona:** P-CRM-01 Vendedor.
**Elementos:** lista ranqueada (30 clientes), cada card mostra nome + sinais ativos (ícones com tooltip "calibração vence em 25d" / "NPS detrator há 2h" / "sem contato 60d") + lead scoring (0-100) + ação rápida (ligar/WhatsApp/abrir 360°).
**Estados:** vazio ("nenhum cliente em destaque — adicionar primeiro?"), atualizando.

### 2. Caixa de entrada — `/crm/inbox`
**Propósito:** atendente vê leads novos (WhatsApp + import + manual) antes de virarem cliente.
**Persona:** P-CRM-02 Atendente.
**Elementos:** lista de leads, filtros (origem, idade, atribuído/não), botão "**converter em cliente**" em cada card (US-CRM-001).

### 3. Conversão de lead — modal sobre `/crm/inbox` (US-CRM-001)
**Propósito:** 1 clique cria cliente + oportunidade.
**Elementos:** toggle PF/PJ, campos pré-preenchidos com dados capturados (nome, telefone, mensagem), confirmação, atribuição de vendedor responsável.

### 4. Kanban funil — `/crm/funil` (Wave B)
**Propósito:** US-CRM-005 — funil visual com drag-and-drop.
**Persona:** P-CRM-01 Vendedor.
**Elementos:** colunas configuráveis (etapas), cards com nome cliente + valor + selo de "tempo na etapa" + foto vendedor, filtros (vendedor, valor, etapa).
**Ação especial:** mover pra "perdido" abre modal pedindo motivo obrigatório.
**Mobile:** modo lista alternativo (kanban horizontal trava em mobile).

### 5. Detalhes oportunidade — `/crm/oportunidades/{id}`
**Propósito:** ver/editar oportunidade.
**Elementos:** dados (valor, prazo, probabilidade), abas (Atividades, Tarefas, Orçamentos vinculados, Histórico de mudanças de etapa).

### 6. Tarefas do vendedor — `/crm/tarefas`
**Propósito:** lista priorizada de tarefas abertas.
**Elementos:** agrupamento (hoje / atrasadas / próximos 7 dias / mais tarde), check-off em 1 clique, criação rápida.

### 7. Configuração de funil — `/configuracoes/crm/funis`
**Persona:** P-CRM-03 Dono.
**Elementos:** lista de funis + editor (adicionar/remover/reordenar etapas, tipo da etapa).

### 8. Configuração de automação — `/configuracoes/crm/automacoes` (Wave B)
**Persona:** P-CRM-03 Dono.
**Elementos:** lista de automações + editor visual gatilho→condição→ação + botão "**testar em sandbox**" (US-CRM-004).
**Sandbox:** modal mostrando "Se ativada hoje, dispararia em N clientes" + lista dos N + revisão obrigatória antes de ativar.

### 9. NPS dashboard — `/crm/nps`
**Propósito:** ver respostas + segmentação detrator/neutro/promotor + comentários.
**Persona:** P-CRM-03 Dono + P-CRM-04 Gerente.
**Elementos:** gráfico tempo, lista comentários abertos, ação "marcar tratado".

### 10. Tela pública NPS — `/nps/{token}` (sem login)
**Propósito:** cliente final responde NPS em < 30s.
**Persona:** P-CRM-05 Cliente final.
**Elementos:** pergunta única + 11 botões grandes (0-10) + campo comentário opcional + agradecimento.
**Mobile-first.**

### 11. Análise de motivos de perda — `/crm/perdas`
**Propósito:** P-CRM-03 Dono entende por que oportunidades estão sendo perdidas.
**Elementos:** gráfico de barras Top motivos + drill-down por período/vendedor/segmento.

## Componentes reutilizáveis

- `<SinalBadge>` (ícone + tooltip explicativo) — pode promover pra comum.
- `<KanbanColuna>` (Wave B).
- `<NPSBotoes>` (0-10).

## Acessibilidade

- WCAG AA + AAA no link público NPS (botões grandes, contraste alto).
- Drag-and-drop kanban tem fallback teclado (mover via menu de contexto).

## Mobile

- Lista do dia + tarefas: responsivos (uso campo).
- Kanban: modo lista alternativo em telas < 768px.
- NPS link público: 100% mobile-first.

## Como evolui

Tela nova → US-CRM-NNN.
