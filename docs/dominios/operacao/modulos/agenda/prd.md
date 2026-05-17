---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# PRD — Módulo Agenda

## 1. O que este módulo é

Calendário gerencial multi-técnico que distribui OS, bloqueios e eventos pelos slots dos técnicos com **validação automática da jornada UMC (INV-020)**, detecção de conflitos, deslocamento estimado, feriados e recorrência. **OP13 — Wave A** (NOVA, destacada de OP3 e OP10).

## 2. Por que este módulo existe

JTBD-009 (gerente não sabe onde técnico está hoje) + JTBD-010 (reagendar vira bagunça em planilha). Antes da auditoria 17/05, agenda estava embutida em OP3.1 e OP10 sem visão multi-técnico. Sem agenda formalizada, OS roda sem programação consistente — bloqueio estrutural do MVP-1.

## 3. Personas

`../personas.md` — P-OP-04 (gerente operacional, primária), P-OP-01 (técnico — visualiza própria agenda), P-OP-03 (atendente — agenda chamado convertido em OS), P-OP-05 (cliente — vê janela proposta).

## 4. Escopo MVP-1 Wave A

- Calendário multi-técnico (visão dia/semana, colunas por técnico)
- Slots de tempo com eventos (OS, bloqueio, descanso, deslocamento, almoço, manutenção interna)
- **Validação INV-020** (Lei 13.103): hook bloqueia agendamento que viola jornada UMC
- Detecção de conflito ao arrastar/criar (não permite 2 eventos no mesmo slot do mesmo técnico)
- Tempo de deslocamento estimado entre OS (geo/distância — fallback manual)
- Bloqueios (férias, treinamento, atestado)
- Feriados (nacional default + estadual/municipal + custom por tenant)
- Recorrência simples (semanal, mensal — manutenção preventiva)
- Reagendamento com auditoria + notificação cliente
- Capacidade do técnico (horas úteis / dia)
- Drag & drop com validação live
- Integração com Chamados (slot proposto ao converter em OS) e OS (atribuição liga slot)

## 5. Non-goals MVP-1

- Roteirização inteligente (TSP) — MVP-2 (OP3.3)
- Sugestão automática de melhor técnico por skill/proximidade — MVP-2
- Integração 2-way com Google/Outlook Calendar — MVP-2
- Reserva de UMC (veículo) como recurso — MVP-2 (Wave B)
- Sincronização da agenda com app pessoal do técnico (push iOS/Android) — MVP-2
- Bot que negocia horário com cliente via WhatsApp — não fazer

## 6. User Stories (resumo)

- **US-AG-001:** gerente vê semana multi-técnico em 1 tela (JTBD-013)
- **US-AG-002:** arrastar OS pra outro técnico/horário valida INV-020 + conflito
- **US-AG-003:** sistema bloqueia agendamento que viola Lei 13.103 com mensagem clara
- **US-AG-004:** criar bloqueio (férias, treinamento) com motivo
- **US-AG-005:** feriados aparecem destacados; agendar em feriado exige confirmação
- **US-AG-006:** ao converter chamado em OS, sistema sugere slot livre do técnico competente
- **US-AG-007:** técnico vê própria agenda no mobile com tempo de deslocamento estimado
- **US-AG-008:** reagendamento notifica cliente com nova janela proposta (aprovação no portal)
- **US-AG-009:** manutenção recorrente (semanal/mensal) gera slots futuros automaticamente
- **US-AG-010:** capacidade do dia mostra "75% ocupado" — gerente decide se aceita mais OS

## 7. Métricas

Ver `metricas.md`. Primárias: % ocupação técnico, conflitos detectados/aceitos, reagendamentos por OS.

## 8. NFR

- Drag & drop responsivo (< 200ms feedback)
- Validação INV-020 acontece **antes** de salvar (não pode aceitar e depois rejeitar)
- WCAG AA (INV-016) — calendário acessível por teclado e leitor de tela
- Visão multi-técnico até 20 técnicos sem degradar (MVP-1)

## 9. Glossário

Ver `glossario.md`.

## 10. Como evolui

US nova → próximo `US-AG-NNN`.
