---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/AGENTS.md
  - docs/comum/personas.md
---

# Personas do domínio Dados

> Personas que interagem **transversalmente** com BI/Indicadores. Personas específicas de módulo ficam em `modulos/<modulo>/personas.md`.

---

## Persona 1: Dono / sócio (P1 reutilizada de `docs/comum/personas.md`)

**Identidade:** 35-55 anos, decisor final. Não usa BI técnico do dia-a-dia; consome **resumo executivo** semanal ou diário.

**Goals neste domínio:**
- Ver em 1 tela: faturamento do mês, contas a receber, inadimplência, OS em andamento.
- Receber resumo agendado (e-mail / WhatsApp) sem precisar abrir o sistema.
- Comparar mês atual vs anterior sem ter que pedir pro contador.

**Frustrations:**
- "Dashboard bonito mas não sei o que olhar."
- Indicador que muda de definição entre módulos (ex: "faturamento" no comercial != no financeiro).
- BI lento que trava o sistema.

**Jornada típica:**
1. Abre o app → vê dashboard executivo na home.
2. Clica em "Inadimplência" → vê lista de clientes em atraso.
3. Recebe e-mail toda segunda 8h com DRE simplificado.

**Devices:** mobile (consulta) + web desktop (análise).
**Frequência:** diário (resumo) + semanal (análise profunda).

---

## Persona 2: Gerente operacional (P2 reutilizada)

**Identidade:** Braço-direito do dono. Acompanha produtividade da equipe, SLA, fila de OS.

**Goals neste domínio:**
- Dashboard operacional ao vivo (OS atrasadas, fila por técnico).
- Comparar produtividade entre técnicos / vendedores.
- Identificar gargalo (qual processo está atrasando).

**Frustrations:**
- Indicador que demora 1 dia pra atualizar (precisa de near-real-time).
- Não consegue filtrar por filial / equipe sem TI.

**Devices:** web desktop (principal).
**Frequência:** diário.

---

## Persona 3: Analista / responsável por relatórios

**Fonte canônica:** `docs/comum/personas.md` P-BI-01 (promovida em 2026-05-17 — aparece em `dados/bi` e futuramente em `financeiro/relatorios-financeiros`, `operacao/capacity-planning-operacional`). Antes era marcada como "específica deste domínio"; com a chegada de relatórios financeiros e capacity planning passou a transversal.

---

## Persona 4: Cliente externo (consumidor de dashboard público — Wave B opcional)

**Identidade:** Cliente do tenant que recebeu link público de dashboard (ex: empresa grande monitorando SLA dos serviços contratados).

**Goals:**
- Ver indicadores do seu próprio relacionamento (sem ver dado de outros clientes).

**Frustrations:**
- Login chato — quer acesso por link.
- Indicador desatualizado.

**Notas de risco:**
- Link público é **superfície LGPD**. Toda informação exposta passa por agregação OU pertence exclusivamente ao próprio cliente.
- `INV-TENANT-*` valida que dashboard externo nunca vaza dado de outro tenant.

---

## Como esta lista evolui

- Persona nova → adicionar entrada + atualizar `docs/comum/personas.md` se for transversal a múltiplos domínios.
- Persona descontinuada → marcar `@deprecated` + manter histórico.
- Revisão obrigatória a cada release de feature que afeta UX.
