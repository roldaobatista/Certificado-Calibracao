---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos UI — Módulo Suporte SaaS

---

## Telas

### Tela 1: Portal de Suporte (entrada)

**Propósito:** Hub onde usuário busca artigo OU abre ticket.
**Persona principal:** Usuário Tenant.
**US:** `US-SUP-001`, `US-SUP-004`.
**Acessível por:** ícone permanente "?" no header do produto.

**Elementos:**
- Barra de busca grande "O que precisa?".
- Sugestões em tempo real (artigos da BC).
- Botão "Abrir ticket".
- Lista de "Meus tickets" (acessos rápidos).
- Indicador status do sistema (verde/amarelo/vermelho com link pra page status).

**Estados:**
- Vazio: cards de tópicos populares.
- Sistema degradado: banner amarelo.
- Manutenção: banner vermelho com janela.

**Acessibilidade:** WCAG AA, teclado.
**Mobile:** responsivo.

---

### Tela 2: Abertura de Ticket

**Propósito:** Usuário descreve problema + anexa evidência.
**US:** `US-SUP-001`, `US-SUP-002`, `US-SUP-008`.

**Elementos:**
- Categoria (select com tooltip explicando cada).
- Título + descrição (markdown leve).
- Auto-sugestão de artigo enquanto digita.
- Upload de anexo (screenshot/vídeo/log).
- Botão "Capturar logs do navegador automaticamente" (com consentimento).
- Prioridade (usuário sugere, suporte confirma).

**Estados:**
- Sucesso: tela de protocolo + ETA SLA + "Acompanhar".
- Erro: mensagem em PT clara.

---

### Tela 3: Detalhe do Ticket

**Propósito:** Conversa thread + ações.
**US:** `US-SUP-005`, `US-SUP-006`.

**Elementos:**
- Header: protocolo, status, categoria, SLA deadline.
- Thread de mensagens (usuário ↔ atendente ↔ IA).
- Campo de resposta + anexo.
- Botão "Marcar resolvido" (usuário).
- CSAT (após resolução).
- Sidebar: histórico de tickets do usuário/tenant.

---

### Tela 4: Chat de Suporte

**Propósito:** Conversa síncrona com IA → handoff humano.
**US:** `US-SUP-005`.

**Elementos:**
- Janela flutuante ou tela cheia.
- Indicador "IA respondendo" / "Aguardando humano".
- Botão "Falar com humano".
- Histórico persistido.

---

### Tela 5: Base de Conhecimento

**Propósito:** Buscar artigos por tópico.
**US:** `US-SUP-004`.

**Elementos:**
- Busca + filtros por categoria.
- Lista de artigos populares.
- Visualização do artigo com markdown + vídeo embed.
- Avaliação "Resolveu?" (sim/não + comentário).

---

### Tela 6: Solicitação/Autorização de Acesso Remoto

**Propósito:** Tenant admin autoriza acesso do suporte.
**US:** `US-SUP-007`.
**Persona:** Tenant Admin.

**Elementos:**
- Notificação destacada (toast + e-mail).
- Detalhes: quem solicita, motivo, TTL proposto.
- Botões "Autorizar" / "Negar" / "Negociar TTL".
- Banner persistente durante sessão ativa ("Suporte está conectado — encerrar").
- Histórico de sessões anteriores.

---

### Tela 7: Roadmap Público

**Propósito:** Mostrar planejamento.
**US:** `US-SUP-010`.

**Elementos:**
- Colunas: Planejado / Em construção / Concluído.
- Cards com título + descrição curta + votos.
- Filtro por módulo / trimestre.

---

### Tela 8: Sugestão de Melhoria

**Propósito:** Usuário propõe + vota.
**US:** `US-SUP-009`.

**Elementos:**
- Formulário simples (título + descrição).
- Listagem com busca + voto rápido.
- Indicador "Sua sugestão foi aprovada/recusada" com motivo.

---

### Tela 9: Painel de Status do Sistema

**Propósito:** Comunicação pública de saúde + manutenções.
**US:** `US-SUP-011`.

**Elementos:**
- Status por componente (API, banco, jobs, A3, fiscal).
- Calendário de manutenções planejadas.
- Histórico de incidentes + pos-mortems.

---

### Tela 10: Atendente — Fila de Tickets

**Propósito:** Atendente vê fila por prioridade.
**Persona:** Atendente Suporte.

**Elementos:**
- Filtros: categoria, prioridade, status, atribuído a mim.
- Indicador de SLA próximo de vencer.
- Ação rápida: pegar ticket, escalar, responder.

---

## Componentes reutilizáveis

Compartilhados em `../../../comum/contratos/ui.md`: banner de manutenção, badge de status, picker de prioridade.

## Como evolui

Tela nova → ligar US. Mudança UX → CHANGELOG.
