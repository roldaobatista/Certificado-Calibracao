---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: agenda
dominio: operacao
---

# Glossário do módulo Agenda

> Termos específicos. Transversais em `docs/comum/glossario.md`.

| Termo | Definição (1 linha) | Sinônimos proibidos | Se vir na tela/log, significa | Origem |
|---|---|---|---|---|
| Slot | Bloco de tempo na agenda de 1 técnico (intervalo início-fim) | "horário" (ambíguo) | unidade básica que carrega OS ou evento | OP13 |
| Evento de agenda | Item alocado num slot (OS, bloqueio, descanso, deslocamento, almoço, manutenção interna) | "compromisso" (genérico demais) | objeto plotado no calendário | OP13 |
| Bloqueio | Slot indisponível por razão não-OS (férias, treinamento, atestado) | "off" | técnico não pode receber OS naquele slot | OP13 |
| Conflito | Dois eventos disputando o mesmo slot do mesmo técnico | "choque" | agendamento rejeitado; humano resolve | JTBD-010 |
| Capacidade do técnico | Horas úteis disponíveis por dia/semana após bloqueios + jornada legal | "carga máxima" | número usado pra balanceamento | OP13 |
| Jornada legal UMC | 11h ininterruptas entre jornadas + 30min descanso a cada 5h30 (Lei 13.103) | "lei do motorista" | INV-020 — hook valida no agendamento | INV-020 |
| Deslocamento | Tempo entre fim de uma OS e início da próxima (estimado por endereço) | "viagem" | bloco no calendário entre 2 OS | JTBD-009 |
| Multi-técnico | Visão calendário com várias colunas (uma por técnico) | "grade" | tela principal do gerente | OP13 |
| Feriado | Data não-útil (nacional/estadual/municipal/tenant) | "folga" | bloqueia agendamento default; gerente pode forçar | OP13 |
| Recorrência | Evento que repete (manutenção semanal, calibração mensal) | "agendamento periódico" | gera slots futuros automaticamente | OP13 |
| Reagendamento | Mover evento de slot mantendo a OS/evento intacto | "remarcar" | grava transição na auditoria + notifica cliente | JTBD-010 |
| Agenda externa | Calendário do cliente exposto via link (ICS) ou portal pra ver janela do técnico | "calendário compartilhado" | só leitura | JTBD-009 |

## Como evolui

Termo novo → verificar conflito com glossário comum.
