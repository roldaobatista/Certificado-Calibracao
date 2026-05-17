---
owner: Roldão
revisado-em: 2026-05-17
status: draft
modulo: crm
dominio: comercial
diataxis: reference
---

# Personas — Módulo CRM

## P-CRM-01 — Vendedor (operacional, persona dominante)

Referência: P-COM-02. Dominante no CRM.

**Goals específicos:**
- Abrir CRM, ver lista do dia (JTBD-083) — não decidir no improviso.
- Mover oportunidade no kanban + atualizar etapa.
- Receber notificação quando cliente abre orçamento, responde NPS detrator, calibração vence em 30d.
- Não esquecer follow-up (tarefas automáticas).

**Frustrations:**
- "Planilha que ninguém olha" (status quo).
- "Cliente sumiu e eu nem notei."
- "Eu lembro de ligar pro João, mas esqueço o resto."

**Jornada típica:**
1. Login → tela inicial mostra "Lista do dia" (JTBD-083)
2. Top do dia: cliente cuja calibração vence em 25d, último contato há 60d
3. Clica → abre 360° do cliente + sugere próxima ação ("ligar / mandar lembrete WhatsApp / oferecer recalibração")
4. Após ligar, registra resultado em 1 clique (atendeu/não atendeu/agendado retorno)

**Devices:** desktop principal, mobile follow-up campo.
**Frequência:** dezenas de vezes/dia.

---

## P-CRM-02 — Atendente (caixa de entrada)

Referência: P-COM-01.

**Goals específicos:**
- Receber lead WhatsApp na caixa de entrada (JTBD-086).
- Converter lead → cliente em 1 clique.
- Atribuir oportunidade ao vendedor certo.

**Frustrations:**
- "Cliente novo manda WhatsApp e a mensagem vira número solto na linha."

**Frequência:** dezenas de vezes/dia.

---

## P-CRM-03 — Dono (configurador de automações)

Referência: P-COM-05.

**Goals específicos:**
- Configurar régua de automação (NPS detrator → tarefa, certificado vencendo → lembrete WhatsApp).
- **Testar em sandbox antes de ativar** (mitigação R-novo CRM-1 — JTBD-087).
- Ver MAPA-DO-DONO com KPIs CRM: pipeline aberto, taxa conversão, NPS médio, motivos de churn.
- Configurar funil kanban customizado.

**Frequência:** semanal (configuração) + diária (consulta de KPI).

---

## P-CRM-04 — Gerente / RT (escalada)

Referência transversal: Sandra (gerente) — `personas-detalhadas.md`.

**Goals:**
- Receber alerta de NPS detrator antes do vendedor escalar (JTBD-085).
- Acompanhar produtividade do time (tarefas atrasadas, taxa fechamento).

**Frequência:** diária (resumo).

---

## P-CRM-05 — Cliente final (receptor de NPS)

Referência: P-COM-03.

**Goals:**
- Responder NPS em < 30 segundos via link WhatsApp/e-mail.
- Comentar livremente se quiser.

**Frequência:** após cada OS concluída.

---

## Anti-personas

- **Vendedor que usa CRM externo (Pipedrive, HubSpot):** módulo NÃO faz sync bidirecional (V2 considera).
- **Marketing massivo (campanha 10k e-mails):** fora do escopo — RAT-06 só permite transacional.

## Convenções

P-CRM-04 (Gerente) é candidata a promover pra `../../personas.md` se aparecer também em módulo Contratos.
