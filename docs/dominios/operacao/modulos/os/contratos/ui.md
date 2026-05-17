---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: os
dominio: operacao
---

# Contratos de UI — Módulo OS

> Telas principais. Wireframe textual enquanto stack não fechada (ADR-0001).

---

## Tela 1: Fila de OS (gerente)

**Propósito:** ver e redistribuir todas as OS ativas em uma tela.
**Persona principal:** P-OP-04 (gerente operacional).
**US:** US-OS-002, US-OS-008.
**Acessível por:** menu Operação → "Fila de OS".

**Elementos:**
- Filtro: estado, técnico, tipo, cliente, prazo.
- Kanban por estado (RASCUNHO | AGENDADA | EM_EXECUCAO | CONCLUIDA | FATURADA) com drag & drop entre estados **válidos** (hook valida INV-027 — drop em estado inválido cancela).
- Card de OS mostra: cliente, equipamento, técnico, prazo, badge NC.
- Ação "redistribuir": muda `tecnico_atribuido_id` + valida INV-020 (UMC).

**Estados:**
- Vazio: "Nenhuma OS ativa. Crie a partir de um orçamento aprovado."
- Carregando: skeleton de cards.
- Erro: "Não conseguimos carregar a fila. Tente novamente."

**Acessibilidade:** WCAG AA, navegação por teclado obrigatória no drag & drop (alt + setas).
**Mobile:** responsivo simplificado (lista vertical com botão "mover").

---

## Tela 2: Detalhe da OS (todos)

**Propósito:** ver tudo da OS + histórico de eventos.
**US:** US-OS-001, US-OS-005, US-OS-006, US-OS-007.

**Elementos:**
- Cabeçalho: número da OS, tipo, estado (badge colorido), cliente, equipamento.
- Abas: Resumo | Checklist | Itens (peças/serviços) | Histórico | Anexos (fotos/assinatura).
- Botões de ação variam por estado e papel:
  - RASCUNHO + gerente: "Atribuir técnico", "Cancelar".
  - EM_EXECUCAO + técnico atribuído: "Concluir" (bloqueia se checklist incompleto).
  - CONCLUIDA + gerente: "Reabrir" (cria nova OS-filha — confirma com diálogo).
- Badge "NC" vermelha se `nao_conformidade=true`.
- Aba Histórico mostra timeline de `EventoDeOS` (transições, atribuições, marcação NC).

---

## Tela 3: Execução da OS (mobile técnico)

**Propósito:** técnico em campo executa OS com poucos toques.
**Persona principal:** P-OP-01.
**US:** US-OS-003, US-OS-004.

**Elementos:**
- Lista do dia (OS AGENDADA do técnico).
- Card grande: cliente + endereço + botão "Iniciar".
- "Iniciar OS" → captura geo (se campo) → estado EM_EXECUCAO.
- Checklist: tipo-dependente (foto + assinatura + padrão + peça).
- Botão "Concluir": valida checklist; se incompleto, mostra os itens que faltam.
- Indicador de sync: "salvo no aparelho" / "enviado pro servidor" (ADR-0004).

**Mobile:** funciona 100% offline. Sync em background quando rede volta.

---

## Tela 4: Portal cliente — Acompanhamento da OS

**Propósito:** cliente vê status da OS sem login complexo (link WhatsApp).
**Persona:** P-OP-05.

**Elementos:** linha do tempo simples (Aberta → Agendada → Em execução → Concluída), data prevista, técnico atribuído (nome + foto opt-in), botão "Aprovar reagendamento" se proposto.

---

## Componentes reutilizáveis

Badge de estado, card de OS, kanban genérico → `../../../comum/contratos/ui.md`.

## Como evolui

Tela nova → ligar a US-OS-NNN. UX → CHANGELOG.
