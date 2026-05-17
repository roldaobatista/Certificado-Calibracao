---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Módulo Onboarding

> Telas do módulo de implantação. Stack final em ADR-0001 (Django + HTMX no web; Flutter no mobile se aplicável).

---

## Telas

### Tela 1: Wizard de cadastro inicial da empresa

**Propósito:** guiar responsável interno na criação do tenant em etapas sequenciais.
**Persona principal:** Responsável interno pela implantação.
**US relacionadas:** `US-ONB-001`.
**Acessível por:** menu "Implantações" → "Nova implantação".

**Elementos:**
- Indicador de progresso (Etapa 1 de N).
- Formulário por etapa: dados cadastrais (CNPJ, razão social, IE), filiais, CNAE, regime tributário, primeiros usuários admin.
- Botão "Salvar e continuar depois" (persiste estado).
- Botão "Avançar" (valida etapa).
- Botão "Voltar".

**Estados:**
- Vazio: primeira etapa em branco.
- Carregando: skeleton no formulário.
- Erro: mensagem em PT-BR apontando campo, sem perder dados preenchidos.
- Sucesso: avança pra próxima etapa.

**Acessibilidade:** WCAG AA; navegação por teclado; foco visível.
**Mobile:** responsivo.

---

### Tela 2: Painel de implantações

**Propósito:** visão geral de todas as implantações atribuídas ao usuário interno + agregada pro gestor.
**Persona principal:** Responsável interno, Gestor.
**US relacionadas:** `US-ONB-004`, `US-ONB-005`.

**Elementos:**
- Filtros: status, responsável, faixa de data.
- Lista de implantações com: nome do tenant, responsável, status agregado, dias desde criação, próxima etapa.
- Indicador visual de parada (>7 dias sem mudança).
- Botão "Nova implantação".

**Estados:**
- Vazio: "Nenhuma implantação. Criar nova?".
- Carregando: skeleton.

---

### Tela 3: Detalhe da implantação

**Propósito:** ver checklist, status de cada etapa, ações disponíveis.
**Persona principal:** Responsável interno, Admin do tenant cliente.
**US relacionadas:** `US-ONB-003`, `US-ONB-005`, `US-ONB-006`.

**Elementos:**
- Cabeçalho: nome tenant, responsável, status, dias decorridos.
- Lista de etapas com status individual e ações (marcar concluída, marcar pendente cliente).
- Timeline com eventos: criação, etapas concluídas, treinamentos, validações.
- Abas: "Importações", "Inconsistências", "Treinamentos", "Validações", "Termo".

---

### Tela 4: Importação de dados

**Propósito:** upload, validação e execução de imports iniciais.
**Persona principal:** Responsável interno, Admin do tenant.
**US relacionadas:** `US-ONB-002`, `US-ONB-007`.

**Elementos:**
- Seletor de tipo (clientes / produtos / serviços / equipamentos / estoque).
- Botão "Baixar template" (CSV/XLSX padrão do tipo).
- Área de upload (drag-and-drop).
- Prévia das primeiras 20 linhas após validação.
- Botão "Validar" → mostra inconsistências detectadas.
- Botão "Executar import" (habilitado só se validação passou).
- Após execução: resumo (criados / duplicados / ignorados) + link pra inconsistências.

**Estados:**
- Vazio: explica o tipo e mostra template.
- Carregando: barra de progresso por linhas.
- Erro: arquivo inválido / formato incorreto / quota excedida.
- Sucesso: resumo + link.

---

### Tela 5: Inconsistências de migração

**Propósito:** listar e resolver inconsistências detectadas.
**US relacionadas:** `US-ONB-007`.

**Elementos:**
- Filtros: severidade, status, tipo de import.
- Lista: linha do arquivo, campo, descrição, severidade, dado original, sugestão.
- Ação por linha: "Resolver" (exige justificativa) ou "Aceitar como está".

---

### Tela 6: Registro de treinamento

**Propósito:** registrar treinamento realizado.
**US relacionadas:** `US-ONB-006`.

**Elementos:**
- Data, duração, módulos cobertos (multi-select), participantes (pessoas do tenant).
- Upload de anexos (slides, link de gravação).

---

### Tela 7: Validação do ambiente

**Propósito:** rodar checks técnicos e ver resultado.
**US relacionadas:** `US-ONB-008`.

**Elementos:**
- Botão "Rodar validação".
- Lista de checks (RLS, KMS, backup, integrações, usuários) com status individual e detalhes.
- Resultado agregado (passou / falhou).
- Bloqueio: se falhou, botão "Promover sandbox" fica desabilitado com tooltip.

---

### Tela 8: Termo de aceite

**Propósito:** gerar, visualizar e assinar termo.
**US relacionadas:** `US-ONB-009`.

**Elementos:**
- Pré-visualização do PDF (escopo, checklist, treinamentos, inconsistências aceitas).
- Botão "Gerar termo" → PDF salvo em WORM.
- Área de assinatura (assinatura A3 via Lacuna — ADR-0009).
- Após assinatura: PDF imutável + status implantação = concluída.

---

### Tela 9: Sandbox e promoção

**Propósito:** ver dados/configurações no sandbox e promover.
**US relacionadas:** `US-ONB-010`.

**Elementos:**
- Indicador "Sandbox" no topo (cor distintiva, nunca confundir com produção).
- Comparação sandbox vs produção (config diff).
- Botão "Promover pra produção" (habilitado só com termo assinado + validação OK).

---

## Componentes reutilizáveis

Banner "Sandbox" e wizard de etapas podem ir pra `../../../comum/contratos/ui.md` se reusados.

## Como esta lista evolui

- Tela nova → ligar a US-NNN.
- Mudança UX → bump CHANGELOG.
