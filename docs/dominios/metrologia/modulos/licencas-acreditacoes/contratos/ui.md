---
owner: roldao
revisado_em: 2026-05-17
status: draft
diataxis: reference
audiencia: agente
---

# Contratos de UI — Licenças e Acreditações

> Telas do módulo. Wireframe descritivo enquanto stack não está cravada (ADR-0001 candidata).

---

## Telas

### Tela 1: Dashboard de Licenças

**Propósito:** visão imediata do status de todos os documentos regulatórios do tenant.
**Persona principal:** Responsável administrativo de conformidade.
**US relacionadas:** `US-LIC-001`, `US-LIC-002`.
**Acessível por:** menu lateral "Conformidade > Licenças".

**Elementos:**
- Cards-resumo: total vigente, vence em 30 dias, vencidos, bloqueantes ativos.
- Tabela paginada: tipo, número, órgão, validade, status colorido, próximo alerta, bloqueante (sim/não), ações.
- Filtros: tipo, status, bloqueante, responsável.
- Botão "Cadastrar novo documento".
- Botão "Gerar relatório auditoria".

**Estados:**
- Vazio: card "Nenhum documento cadastrado — comece aqui".
- Carregando: skeleton com linhas placeholder.
- Erro: "Não foi possível carregar — tente novamente em 1 minuto" + botão recarregar.
- Sucesso: tabela populada.

**Acessibilidade:** WCAG AA, teclado completo, alt nos ícones de status.
**Mobile:** responsivo prioritário (alertas no mobile são chave).

---

### Tela 2: Cadastro/Edição de Documento

**Propósito:** criar novo documento ou editar metadados não-imutáveis.
**Persona principal:** Responsável administrativo.
**US relacionadas:** `US-LIC-001`, `US-LIC-005`, `US-LIC-006`.

**Elementos:**
- Formulário em seções: identificação (tipo, número, órgão, escopo se acreditação), vigência (datas), responsabilidade (responsável, bloqueante), anexo (upload PDF/imagem), observação.
- Validação inline: data_validade > data_emissao; anexo obrigatório; escopo obrigatório se tipo=ACREDITACAO_CGCRE.
- Pré-visualização do anexo antes de salvar.

**Estados:**
- Erro de validação: campo destacado + mensagem PT clara ("a data de validade precisa ser depois da emissão").
- Salvando: botão desabilitado com spinner.
- Sucesso: redireciona pra detalhe + toast "documento cadastrado".

**Acessibilidade:** WCAG AA; labels associados a inputs.
**Mobile:** responsivo, upload via câmera permitido.

---

### Tela 3: Detalhe do Documento

**Propósito:** ver dados completos + histórico de revisões + alertas + botão renovar.
**Persona principal:** Responsável administrativo + RT (quando ART/RRT própria).

**Elementos:**
- Cabeçalho com status grande e colorido.
- Abas: Dados | Histórico de revisões | Alertas | Bloqueios.
- Aba Histórico: linha do tempo com cada revisão (data emissão, validade, anexo, quem criou).
- Aba Alertas: lista enviados + agendados.
- Aba Bloqueios: bloqueios ativos + histórico + eventos emergenciais.
- Ações: Renovar | Editar metadados | Marcar bloqueante | Excluir (só admin master, com confirmação dupla — gera evento WORM).

**Estados:** padrão.
**Acessibilidade:** WCAG AA.
**Mobile:** responsivo.

---

### Tela 4: Renovação

**Propósito:** registrar nova revisão (versão) do documento.
**Persona principal:** Responsável administrativo.
**US relacionadas:** `US-LIC-004`.

**Elementos:**
- Resumo do documento atual.
- Formulário curto: nova data emissão, nova validade, novo anexo, motivo (enum), observação.
- Alerta visual: "ao salvar, esta revisão fica imutável".

**Estados:** padrão; sucesso reagenda alertas e fecha bloqueio se ativo.

---

### Tela 5: Modo Emergencial

**Propósito:** liberar operação com documento bloqueante vencido.
**Persona principal:** Admin tenant (com privilégio).
**US relacionadas:** `US-LIC-003`.

**Elementos:**
- Texto grande de aviso: "Você está liberando operação com documento vencido. Isso será auditado."
- Documento bloqueante exibido.
- Campo obrigatório: justificativa (mínimo 50 caracteres).
- Janela de validade do bypass: 24h / 72h / 7 dias.
- Botão "Confirmar com assinatura A3" → dispara fluxo Web PKI Lacuna (ADR-0009).

**Estados:**
- Sem A3 conectado: bloqueia + instrução "conecte o token A3".
- Sucesso: registra EventoEmergencial + libera operação + notifica auditor.

---

### Tela 6: Relatório de Auditoria

**Propósito:** gerar PDF consolidado pra auditoria externa.
**Persona principal:** Auditor externo ou admin.
**US relacionadas:** `US-LIC-007`.

**Elementos:**
- Filtros: data corte, tipos a incluir, incluir histórico (sim/não — janela em meses).
- Pré-visualização sumária.
- Botão "Gerar PDF" → download + envia hash por e-mail.

---

## Componentes reutilizáveis

- Badge de status (vigente/vencendo/vencido) — compartilhado com Calibração e Certificados.
- Upload com pré-visualização PDF — compartilhado com vários módulos. Ver `../../../comum/contratos/ui.md`.

## Como esta lista evolui

- Tela nova → adicionar + ligar a US.
- Mudança UX → bump CHANGELOG.
- Tela deprecada → `@deprecated` + janela.
