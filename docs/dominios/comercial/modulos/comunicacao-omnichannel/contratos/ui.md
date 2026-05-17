---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Comunicação Omnichannel

> Telas e comportamento. Wireframe textual até stack final.

---

## Telas

### Tela 1: Caixa de Entrada Unificada

**Propósito:** ver e responder mensagens de todos os canais.
**Persona principal:** Atendente.
**US relacionadas:** `US-COM-001`, `US-COM-005`, `US-COM-010`.
**Acessível por:** menu Comercial → Atendimento → Inbox.

**Elementos:**
- Coluna esquerda: lista de threads (avatar cliente, canal, prévia, badge não lida, badge status SLA quando aplicável).
- Coluna central: thread selecionada com bolhas de mensagem, indicador de status (enviado/entregue/lido).
- Coluna direita: sidebar do cliente — dados básicos, OS abertas, orçamentos, último contato, consentimentos.
- Filtros topo: canal, status (não lidas, em andamento, resolvidas), atribuição (minhas/equipe/todas), pesquisa.
- Botão "Compor" (nova conversa de saída).
- Input inferior: campo de texto + anexo + botão "/" (respostas rápidas) + botão "Templates" + botão "Enviar".

**Estados:**
- Vazio: ilustração + "Sem mensagens".
- Carregando: skeleton.
- Erro: mensagem em PT.
- Cliente sem opt-in (envio promocional): badge vermelho "SEM OPT-IN" e botão "Enviar" desabilitado.

**Acessibilidade:** WCAG AA; navegação por teclado completa (atalhos j/k pra navegar threads, etc.).
**Mobile:** versão responsiva limitada (foco é desktop).

---

### Tela 2: Thread (detalhe)

**Propósito:** ler e responder uma thread específica.
**US:** `US-COM-001`, `US-COM-005`, `US-COM-008`, `US-COM-009`, `US-COM-010`.

**Elementos:**
- Cabeçalho: cliente, canal, status, atendente atribuído (com ação "Reatribuir").
- Histórico de mensagens em ordem cronológica.
- Cada mensagem: timestamp, autor, conteúdo, status entrega, anexos.
- Ações: Marcar resolvida, Reabrir, Converter em chamado, Converter em lead, Vincular a OS/Orçamento existente.
- Indicador de sessão WhatsApp (24h) quando aplicável: "Sessão expira em HH:MM".

---

### Tela 3: Composer / Nova Mensagem

**Propósito:** iniciar conversa de saída ou enviar em thread existente.
**US:** `US-COM-001`, `US-COM-004`, `US-COM-005`.

**Elementos:**
- Seletor de canal.
- Destinatário (busca em CRM).
- Seletor de template (obrigatório fora de sessão WhatsApp).
- Editor com variáveis substituídas.
- Pré-visualização final.
- Aviso "Esta mensagem é promocional — precisa de opt-in" quando aplicável.
- Botão "Enviar".

---

### Tela 4: Lista e Editor de Templates

**Propósito:** cadastrar/gerir templates.
**Persona:** Gerente Comercial.
**US:** `US-COM-004`.

**Elementos:**
- Lista com colunas: nome, versão, canal, status (rascunho/pendente/aprovado/reprovado), última atualização.
- Filtros por canal e status.
- Editor: nome, canal, corpo com variáveis (chips visuais para `{{cliente.nome}}`), pré-visualização, botão "Submeter para aprovação" (canais regulados).
- Banner "Template aprovado: para alterar crie nova versão".

---

### Tela 5: Respostas Rápidas

**Propósito:** gerir snippets.
**Persona:** Atendente (escopo pessoal), Gerente (equipe/tenant).
**US:** `US-COM-005`.

**Elementos:**
- Lista atalho + corpo + escopo.
- Editor com pré-visualização.
- Importar/exportar (CSV).

---

### Tela 6: Regras de Automação

**Propósito:** configurar mensagens automáticas por evento.
**Persona:** Gerente Comercial.
**US:** `US-COM-006`.

**Elementos:**
- Construtor de regra: evento gatilho + condições + template + canal preferido + fallback.
- Pré-visualização do disparo.
- Toggle ativo/inativo.
- Histórico de disparos (auditoria).

---

### Tela 7: Distribuição de Conversas

**Propósito:** configurar como conversas são atribuídas.
**Persona:** Gerente.
**US:** `US-COM-007`.

**Elementos:**
- Tipo (round-robin/carteira/skill).
- Parâmetros conforme tipo.
- Pré-visualização do impacto.
- Override manual por conversa.

---

### Tela 8: Consentimentos do Cliente

**Propósito:** auditar consentimentos de um cliente.
**Persona:** Atendente, DPO.
**US:** `US-COM-002`, `US-COM-003`.

**Elementos:**
- Lista por canal: tipo (opt-in/opt-out), base legal, texto apresentado, resposta, data, referência mensagem.
- Botão "Exportar trilha" (CSV/PDF).
- Não permite editar (WORM); apenas registrar novo.

---

### Tela 9: Dashboard de Atendimento

**Propósito:** indicadores de operação.
**Persona:** Gerente.
**US:** `US-COM-011`.

**Elementos:**
- Filtros: período, canal, atendente, equipe.
- KPI cards: volume, TMR, TMA, % opt-in, conversões.
- Gráficos: por canal, por hora do dia, por atendente.
- Drill-down para conversa específica.

---

## Componentes reutilizáveis

- Componente "Status Entrega" (badge) — também usado em fichas de cliente / OS.
- Componente "Histórico de Comunicação" (timeline) — embarcado em telas de cliente, OS, orçamento, chamado.

Componentes verdadeiramente compartilhados em `../../../comum/contratos/ui.md`.

---

## Como esta lista evolui

- Tela nova → adicionar + ligar a US.
- Mudança em UX → bump CHANGELOG.
- Tela descontinuada → `@deprecated` + janela.
