---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Contratos de UI — Módulo Agenda

> Telas principais. Foco em drag & drop validado.

---

## Tela 1: Calendário multi-técnico (gerente)

**Propósito:** ver semana inteira de todos técnicos lado a lado.
**Persona:** P-OP-04.
**US:** US-AG-001, US-AG-002, US-AG-003.
**Acessível:** menu Operação → "Agenda".

**Elementos:**
- Seletor de modo: Dia | Semana (default) | Mês (resumo).
- Eixo X: técnicos (colunas — até 20 visíveis; rolagem se mais).
- Eixo Y: horas (06h-22h default — configurável por tenant).
- Cards de evento coloridos por tipo (OS=azul, bloqueio=cinza, descanso=verde, feriado=amarelo, deslocamento=cinza claro).
- Drag & drop:
  - Arrastar evento dentro da mesma coluna = mudar horário.
  - Arrastar pra outra coluna = mudar técnico.
  - Durante drag: validação live mostra "ok" (verde) ou "violação INV-020" / "conflito" (vermelho com motivo).
  - Drop em estado inválido = cancela com toast explicando.
- Indicadores na coluna: % ocupação do dia, ícone de alerta se passou 95%.
- Banner de feriado quando coluna do dia é feriado.

**Estados:**
- Vazio: "Nenhum evento na semana." + botão "Criar evento".
- Carregando: skeleton de grade.
- Erro: "Não conseguimos carregar a agenda."

**Acessibilidade:** WCAG AA. Drag por teclado (foco no card + Alt+setas pra mover entre slots). Leitor de tela anuncia validação durante move.

---

## Tela 2: Criar/editar evento (modal)

**Propósito:** form rápido pra criar bloqueio, OS, descanso.
**US:** US-AG-004, US-AG-005.

**Elementos:**
- Tipo (segmented: OS | Bloqueio | Descanso | Deslocamento | Manutenção interna).
- Técnico (autocomplete).
- Data + hora início + duração (default 1h).
- Se tipo=OS: campo OS (autocomplete RASCUNHO/AGENDADA).
- Se tipo=Bloqueio: motivo (dropdown).
- Recorrência (toggle "Repetir") → seletor de regra (semanal por dia, mensal por dia do mês).
- Botão "Salvar" valida antes; se inválido, mostra motivo.

---

## Tela 3: Minha agenda (mobile técnico)

**Propósito:** técnico vê próximo turno.
**Persona:** P-OP-01.
**US:** US-AG-007.

**Elementos:**
- Lista vertical do dia: hora, OS/evento, cliente, endereço, tempo de deslocamento estimado entre eventos.
- Tap em OS → vai pra tela de execução (módulo OS).
- Indicador "intervalo legal obrigatório aqui" quando descanso INV-020 está marcado.

**Mobile:** read-only. Sync automático com servidor (offline ok pra consulta).

---

## Tela 4: Sugestão de slot ao converter chamado em OS

**Propósito:** atendente recebe sugestões prontas ao converter (US-AG-006).
**US:** US-AG-006.

**Elementos:**
- Lista de 3 sugestões: próximos slots livres do técnico competente, com data/hora + janela proposta + deslocamento estimado.
- Botão "Aceitar" em cada.
- Link "Ver agenda completa" abre Tela 1 já filtrada.

---

## Tela 5: Portal cliente — Aprovar janela

**Persona:** P-OP-05.
**US:** US-AG-008.

**Elementos:** janela proposta (ex: "amanhã 8h-12h") + botão "Aprovar" + botão "Propor outra". Lembrete automático D-1.

---

## Componentes reutilizáveis

Calendário base, card de evento, modal de evento → `../../../comum/contratos/ui.md`.

## Como evolui

Tela nova → ligar a US-AG-NNN.
