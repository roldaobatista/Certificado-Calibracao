---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas do módulo Comunicação Omnichannel

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Atendente / SDR

**Identidade:** profissional de atendimento, 20–35 anos, alta rotatividade típica do setor; trabalha em frente ao computador o dia inteiro.

**Goals deste módulo:**
- Ver e responder mensagens de todos os canais em uma única caixa.
- Identificar cliente rápido (sidebar com histórico).
- Usar respostas rápidas e templates para ganhar produtividade.
- Converter conversa em chamado ou lead quando necessário.

**Frustrations específicas:**
- Trocar entre 4 apps (WhatsApp Web, Outlook, plataforma SMS, chat do site).
- Não saber se cliente já falou com colega.
- Repetir digitação de mensagens comuns.
- Esquecer de registrar opt-in/opt-out.

**Jornada típica:**
1. Login → caixa unificada com filtro "minhas".
2. Cliente novo: dispara template de consentimento.
3. Responde, usa "/preco" para enviar tabela.
4. Converte em chamado quando vira problema técnico.

**Devices:** web desktop (foco).
**Frequência:** diário, jornada toda.

---

## Persona 2: Gerente de Atendimento

**Identidade:** gerente da operação de atendimento; responde por TMA, SLA de primeira resposta, qualidade.

**Goals deste módulo:**
- Distribuir conversas entre atendentes (round-robin / carteira / skill).
- Acompanhar dashboard de volume e TMA.
- Auditar conversas críticas.
- Aprovar templates antes do uso.

**Frustrations específicas:**
- Falta de visão agregada da operação.
- Atendente cobrindo errado por celular pessoal (zero rastro).

**Jornada típica:**
1. Manhã: configura distribuição/escalas.
2. Acompanha dashboard ao longo do dia.
3. Aprova templates pendentes.
4. Mensal: revisa relatório de atendimento.

**Devices:** web desktop + mobile (alertas).
**Frequência:** diário.

---

## Persona 3: DPO / Encarregado LGPD

**Identidade:** responsável pelo programa LGPD da empresa cliente (pode ser interno ou terceirizado).

**Goals deste módulo:**
- Garantir registro de consentimento auditável.
- Garantir opt-out imediato em qualquer canal.
- Exportar trilha para auditoria/Anatel/ANPD.

**Frustrations específicas:**
- Risco de envio para cliente em opt-out (vazamento).
- Falta de evidência de base legal por mensagem.

**Jornada típica:**
1. Trimestral: auditoria amostral de consentimentos.
2. Em incidente: exporta trilha para responder à ANPD.

**Devices:** web desktop.
**Frequência:** trimestral + ad-hoc.

---

## Persona 4: Gerente Comercial / Marketing

**Identidade:** dispara campanhas de comunicação massiva (campanhas comerciais, lembretes de calibração programada).

**Goals deste módulo:**
- Disparar mensagens em massa para segmentos.
- Garantir que só vai para opt-in.
- Medir conversão (mensagem → orçamento aceito).

**Frustrations específicas:**
- Lista de envio desatualizada.
- WhatsApp bloqueando por excesso ou template não aprovado.

**Jornada típica:**
1. Define segmento (clientes com calibração vencendo em 30 dias).
2. Escolhe template aprovado.
3. Agenda envio.
4. Monitora entrega/leitura/conversão.

**Devices:** web desktop.
**Frequência:** semanal.

---

## Persona 5: Cliente final (externa, mas relevante para UX)

**Identidade:** cliente da empresa cliente; receberá as mensagens. Pode ser técnico, comprador, gestor.

**Goals deste módulo (lado cliente):**
- Receber comunicação no canal preferido.
- Pedir opt-out e ser ouvido imediatamente.
- Ter histórico das conversas no portal (opcional, se acessar).

**Frustrations específicas:**
- Mensagem em canal indesejado.
- Não ter resposta no horário comercial.

**Devices:** mobile predominante (WhatsApp/SMS).
**Frequência:** variável.

---

## Convenções

- Persona específica = papel com responsabilidade única neste módulo.
- "Cliente final" também é transversal — versão expandida em `docs/comum/personas.md`.
- Hook valida não-duplicação.
