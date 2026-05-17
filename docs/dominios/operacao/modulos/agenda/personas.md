---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Personas do módulo Agenda

> Detalhe transversal em `../personas.md`. Aqui o papel específico em Agenda.

---

## P-OP-04 (Gerente operacional) — PRIMÁRIA

**Goals em Agenda:**
- Ver semana multi-técnico em 1 tela (JTBD-013)
- Arrastar OS entre técnicos e horários — sistema valida em tempo real (INV-020)
- Detectar técnico sobrecarregado (capacidade > 100%) vs. ocioso
- Reagendar com 2 cliques quando técnico falta (JTBD-010)
- Bloquear horários (treinamento, férias) sem programar manualmente

**Frustrations:**
- "Planilha do Excel não diz que motorista X passou de 11h" (Dor real ligada a INV-020)
- "Reagendei a OS mas esqueci de avisar o cliente" (JTBD-010)
- "Não vejo deslocamento — agendei 3 OS em locais opostos no mesmo turno"

**Jornada típica:**
1. Manhã: abro semana → vejo todos técnicos lado a lado
2. Cliente liga pra remarcar → arrasto OS pro novo slot
3. Sistema valida → se ok, salva + notifica cliente automático
4. Tarde: técnico avisa que vai faltar amanhã → arrasto OS pra outro técnico → INV-020 valida

**Devices:** web desktop (uso intenso) + mobile (consulta).

---

## P-OP-01 (Técnico de campo)

**Goals em Agenda:**
- Ver minha agenda do dia no mobile (já em OS, mas Agenda alimenta)
- Tempo de deslocamento estimado entre OS
- Não receber agendamento que viola minha jornada legal (INV-020 me protege)

**Devices:** mobile (read-only).

---

## P-OP-03 (Atendente)

**Goals em Agenda:**
- Ao converter chamado em OS, ver slots livres do técnico competente
- Aceitar sugestão de slot em 1 clique
- Não precisar abrir outra tela pra checar disponibilidade

**Devices:** web desktop.

---

## P-OP-05 (Cliente final)

**Goals em Agenda:**
- Ver janela proposta pelo gerente (ex: "amanhã 8h-12h")
- Aprovar ou contraproposta pelo portal/WhatsApp
- Receber lembrete na véspera

**Devices:** mobile (WhatsApp/portal).

---

## Convenções

Papel em ≥2 módulos com mesma responsabilidade → promover.
