---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
---

# Personas — Módulo Suporte SaaS

> Personas específicas. Transversais em `../../personas.md` e `docs/comum/personas.md`.

---

## Persona 1: Usuário Tenant (qualquer papel)

**Identidade:** Qualquer pessoa logada num tenant Aferê. Sem perfil técnico assumido.

**Goals deste módulo:**
- Resolver dúvida operacional rápido.
- Reportar bug que está atrapalhando trabalho.
- Sugerir melhoria que perceberia diferença pra rotina.

**Frustrations específicas:**
- Não saber pra onde escalar erro do sistema.
- Abrir ticket e nunca receber resposta.
- Procurar resposta em base de conhecimento desatualizada.

**Jornada típica:**
1. Encontra problema no produto.
2. Clica "Falar com suporte" (atalho permanente).
3. Sistema sugere artigos antes de abrir ticket.
4. Se não resolve → abre ticket + anexa evidência.
5. Recebe atualização por e-mail + dentro do produto.

**Devices:** web (principal) + mobile (Aferê mobile).
**Frequência:** eventual (semanal a mensal).

---

## Persona 2: Atendente do Suporte Aferê

**Identidade:** Equipe interna do Aferê (humanos + agentes IA). Conhece o produto a fundo.

**Goals deste módulo:**
- Resolver tickets dentro do SLA.
- Identificar bugs reincidentes para escalar pra dev.
- Atualizar base de conhecimento com novas FAQ.

**Frustrations específicas:**
- Ticket sem evidência ("não funciona") sem detalhes.
- Mesmo bug reportado 20 vezes sem ser corrigido.

**Jornada típica:**
1. Ticket cai na fila por categoria + prioridade.
2. Lê histórico do tenant + usuário.
3. Responde / pede acesso remoto / escala pra dev.
4. Atualiza status até resolver.

**Devices:** web desktop.
**Frequência:** diário, tempo integral.

---

## Persona 3: Gerente de Produto do Aferê

**Identidade:** Roldão + futuros PMs. Decide o que vai pro roadmap.

**Goals deste módulo:**
- Ver tendências (categorias mais reportadas, módulos mais problemáticos).
- Decidir prioridades de roadmap baseado em votação + dados.
- Comunicar releases + manutenções.

**Frustrations específicas:**
- Roadmap desconectado da dor real.

**Devices:** web desktop.
**Frequência:** diário a semanal.

---

## Persona 4: Tenant Admin (consentimento de acesso remoto)

**Identidade:** Dono ou TI do tenant.

**Goals deste módulo:**
- Autorizar (ou negar) acesso remoto do suporte.
- Auditar quando suporte acessou e o que fez.

**Frustrations específicas:**
- Não saber quando suporte entra no sistema.

**Devices:** web desktop.
**Frequência:** eventual.

---

## Convenções

Persona específica = responsabilidade única deste módulo. Se aparecer em ≥2 módulos, promover.
