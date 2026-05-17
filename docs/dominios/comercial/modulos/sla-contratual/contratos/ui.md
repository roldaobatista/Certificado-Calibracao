---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo SLA Contratual

> Telas e comportamento. Wireframe textual enquanto stack final não está cravada.

---

## Telas

### Tela 1: Lista de Perfis de SLA

**Propósito:** ver, criar, versionar perfis reutilizáveis.
**Persona principal:** Gerente Comercial.
**US relacionadas:** `US-SLA-001`.
**Acessível por:** menu Comercial → SLA → Perfis.

**Elementos:**
- Botão "Novo perfil".
- Tabela com colunas: nome, versão, TR, TS, calendário, vinculados (qtde de contratos), status.
- Filtros: status (ativo/rascunho/descontinuado), criticidade, tipo serviço.
- Ação por linha: ver detalhe, nova versão, descontinuar.

**Estados:** vazio → CTA "Crie seu primeiro perfil"; carregando skeleton; erro mensagem PT.

**Acessibilidade:** WCAG AA, teclado, screen reader.
**Mobile:** apenas leitura (gestão é desktop).

---

### Tela 2: Detalhe / Edição de Perfil de SLA

**Propósito:** criar/editar perfil em rascunho; perfis ativos só permitem nova versão.
**US:** `US-SLA-001`.

**Elementos:**
- Cabeçalho com nome + versão + status.
- Campos: TR (input min/h), TS (input min/h), seletor calendário, criticidade-alvo, tipo-serviço-alvo.
- Bloco "Penalidade": tipo (% / valor fixo / por hora), teto, piso.
- Bloco "Bonificação": idem.
- Lista de motivos de pausa permitidos (multi-select de catálogo + adicionar).
- Botões: salvar rascunho, ativar (valida campos obrigatórios), nova versão (se ativo).

**Estados:** rascunho editável, ativo somente leitura com banner "para alterar crie nova versão".

---

### Tela 3: Cronômetro de SLA (componente embarcado em Chamado/OS)

**Propósito:** mostrar tempo restante em tempo real.
**Persona:** Atendente, Técnico.
**US:** `US-SLA-002`, `US-SLA-003`.
**Acessível por:** dentro da tela do chamado/OS.

**Elementos:**
- Cronômetros TR e TS lado a lado.
- Cor: verde > 50%, amarelo 50–20%, vermelho < 20%.
- Indicador "PAUSADO" quando aplicável.
- Botão "Pausar" → modal com motivo (select obrigatório de lista permitida) + descrição + anexo.
- Botão "Despausar" (somente se pausado).
- Histórico de pausas em accordion.

**Estados:**
- Cronometrando: cor + tempo decrescente.
- Pausado: badge amarelo "PAUSADO desde HH:MM por [motivo]".
- Estourado: badge vermelho "ESTOUROU em X min".
- Cumprido: badge verde "CUMPRIDO".

---

### Tela 4: Dashboard de Cumprimento

**Propósito:** ver SLA agregado por cliente, equipe, período.
**Persona:** Gerente de Operações, Gerente Comercial.
**Acessível por:** menu Comercial → SLA → Dashboard.

**Elementos:**
- Filtros: período, cliente, equipe, tipo serviço.
- KPI cards: % cumprimento, qtd estouros, qtd em risco agora.
- Gráfico de tendência mensal.
- Tabela de SLAs em risco agora (drill-down para chamado/OS).

---

### Tela 5: Lista e Geração de Relatórios SLA

**Propósito:** gerar relatório mensal por cliente e enviar.
**Persona:** Gerente Comercial.
**US:** `US-SLA-007`.

**Elementos:**
- Seletor cliente + período.
- Botão "Gerar relatório".
- Pré-visualização do PDF.
- Botão "Emitir" (gera hash imutável + publica evento).
- Botão "Enviar ao cliente" (após emitir) → escolhe canal (Comunicação Omnichannel).
- Lista de relatórios já emitidos (com hash, data, status entrega).

**Estados:** gerando → spinner; emitido → bloqueado pra alteração; enviado → status entrega.

---

### Tela 6: Configuração de Escalonamento

**Propósito:** definir cadeia de escalonamento por perfil.
**Persona:** Gerente Comercial.
**US:** `US-SLA-005`.

**Elementos:**
- Por nível: tempo sem ação (min) + destinatários (papel ou usuário) + canais (e-mail/push/WhatsApp via Omnichannel).
- Pré-visualização da cadeia.

---

### Tela 7: Calendário de Atendimento

**Propósito:** criar/editar calendários (8x5, 24/7, customizado, feriados).
**Persona:** Gerente de Operações.
**US:** `US-SLA-002` (AC-002-2, AC-002-3).

**Elementos:**
- Tipo (8x5 / 24x7 / custom).
- Grade semanal editável.
- Lista de feriados (importação por município).
- Fusos horários permitidos.

---

## Componentes reutilizáveis

- Componente Cronômetro SLA — também usado em telas de Chamado/OS (sincroniza via evento `SLA.Cronometrando`).
- Componente Badge Status SLA — usado em listagens cross-módulo.

Componentes verdadeiramente compartilhados ficam em `../../../comum/contratos/ui.md`.

---

## Como esta lista evolui

- Tela nova → adicionar + ligar a US-NNN.
- Mudança em UX → bump CHANGELOG seção "Modificado".
- Tela descontinuada → `@deprecated` + janela.
