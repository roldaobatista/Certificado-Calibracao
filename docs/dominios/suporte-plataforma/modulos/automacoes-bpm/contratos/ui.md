---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Automações & BPM

> Telas do módulo + comportamento esperado. Stack final em ADR-0001.

---

## Telas

### Tela 1: Editor Visual de Fluxos

**Propósito:** desenhar fluxo arrastando etapas e ligando transições.
**Persona principal:** Configurador de Fluxos.
**US relacionadas:** `US-BPM-001`, `US-BPM-003`.
**Acessível por:** menu "Automações > Fluxos > Novo / Editar".

**Elementos:**
- Canvas central com paleta de etapas à esquerda (Início, Decisão Humana, Ação Automática, Condicional, Fim).
- Painel de propriedades à direita (selecionar etapa abre propriedades: nome, SLA, responsável, escalonamento).
- Barra superior: nome do fluxo, versão, botão "Salvar rascunho", "Publicar (shadow)", "Publicar (ativo)", "Histórico de versões".
- Mini-mapa do fluxo no canto inferior direito.

**Estados:**
- Vazio: canvas em branco com tutorial inline (3 passos).
- Carregando: skeleton do canvas.
- Erro de validação: lista de problemas (etapas órfãs, transições sem condição, ciclos detectados).
- Sucesso ao publicar: toast "Fluxo X versão N publicado em modo shadow/ativo".

**Acessibilidade:** WCAG AA; canvas alternativa por listagem hierárquica (tab-friendly); shortcuts (a=adicionar etapa, t=adicionar transição).
**Mobile:** apenas leitura (visualização do desenho); edição é desktop.

---

### Tela 2: Editor de Regras Automáticas

**Propósito:** cadastrar regra `evento + condição + ação` em formato formulário.
**Persona principal:** Configurador de Fluxos.
**US:** `US-BPM-002`, `US-BPM-006`, `US-BPM-007`.

**Elementos:**
- Wizard de 4 passos: 1) escolher evento (busca no catálogo); 2) definir condição (form-builder ou YAML); 3) escolher ação (busca no catálogo); 4) revisar e publicar.
- Toggle "Modo shadow" no último passo.
- Preview do payload exemplo do evento selecionado.

**Estados:** vazio (passo 1); validação inline em cada passo; sucesso → redireciona pra lista de regras.

---

### Tela 3: Painel "Minhas Aprovações"

**Propósito:** aprovador vê e decide pendências.
**Persona principal:** Aprovador.
**US:** `US-BPM-005`.

**Elementos:**
- Lista paginada ordenada por SLA crescente.
- Cores: verde (>50% SLA restante), amarelo (20-50%), vermelho (<20% ou estourado).
- Cada linha: nome do fluxo, etapa atual, entidade (OS-1234, Orçamento-567), valor (se aplicável), SLA restante, botões "Aprovar", "Rejeitar", "Ver detalhes".
- Filtros: tudo / fluxo / SLA / risco.
- Botão "Aprovar/rejeitar em lote" (seleção múltipla).

**Estados:**
- Vazio: "Nenhuma pendência. Bom trabalho!"
- Decisão: modal de confirmação + campo comentário.
- Após decisão: linha some com animação fade-out.

---

### Tela 4: Catálogo de Eventos / Condições / Ações

**Propósito:** consultar o que está disponível pro editor.
**Persona principal:** Configurador de Fluxos.
**US:** `US-BPM-007`.

**Elementos:**
- 3 abas (Eventos / Condições / Ações).
- Busca + filtro por módulo de origem.
- Linha expansível: descrição PT-BR, schema payload, exemplo, status (ativo / `@deprecated`).

---

### Tela 5: Log de Execuções / Reprocessamento

**Propósito:** ver histórico de regras executadas, identificar falhas, reprocessar.
**Persona principal:** Operador de Suporte.
**US:** `US-BPM-004`.

**Elementos:**
- Filtros: regra, status (sucesso|falha), data, tenant (admin global only).
- Tabela: data, regra, evento entrada, condição (true|false), ação, resultado, link "Ver payload".
- Botão "Reprocessar" por linha (status falha) + "Reprocessar em lote".

**Estados:** falha → expande motivo de erro (mensagem + stack se admin).

---

### Tela 6: Configuração de Delegação

**Propósito:** aprovador cadastra substituto temporário.
**Persona principal:** Aprovador.
**US:** `US-BPM-003`.

**Elementos:**
- Campos: substituto (busca usuário), válido de / até, motivo.
- Lista de delegações ativas e históricas.

---

### Tela 7: Configuração de Alertas

**Propósito:** cadastrar alertas operacionais (vencimento, SLA, estoque mínimo etc.).
**Persona principal:** Configurador de Fluxos.

**Elementos:**
- Tipo de alerta (dropdown).
- Critério (evento + offset temporal OU condição).
- Canal (e-mail, WhatsApp, SMS, in-app).
- Destinatário (usuário, grupo, alçada).

---

## Componentes reutilizáveis

Componentes compartilhados (ex: `<BuscaUsuario>`, `<EditorYaml>`) ficam em `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → linkar a US.
- Mudança de UX → bump CHANGELOG.
- Tela descontinuada → `@deprecated` + janela de migração.
