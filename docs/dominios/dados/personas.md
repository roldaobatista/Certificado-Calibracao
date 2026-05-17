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

## Persona 3: Analista / responsável por relatórios (NOVA — específica deste domínio)

**Identidade:** Pode ser o próprio dono em empresas pequenas, ou um perfil dedicado em empresas maiores. Familiaridade média com planilhas (Excel). Não programa SQL.

**Goals:**
- Criar relatório customizado sem chamar suporte.
- Agendar envio automático para diretoria / cliente externo.
- Exportar para Excel / CSV para análise externa.

**Frustrations:**
- Ferramentas de BI exigem treinamento longo.
- Custo de licença por usuário em ferramentas tipo Power BI / Tableau.
- Engessamento — "só posso ver o que vem pronto".

**Jornada típica:**
1. Abre construtor de relatório → escolhe métrica + filtros + agrupamento.
2. Visualiza prévia → ajusta.
3. Salva como dashboard pessoal OU agenda envio semanal.

**Devices:** web desktop.
**Frequência:** semanal.

**Permissões:** RBAC `analista` — leitura ampla + criação de relatório próprio, sem ver dado financeiro sensível salvo permissão extra.

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
