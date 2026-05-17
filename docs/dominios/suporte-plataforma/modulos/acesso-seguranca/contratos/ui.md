---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: reference
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/comum/isolamento-multi-tenant.md
---

# Contratos de UI — Módulo ACS

> Telas + comportamento. Wireframe textual basta enquanto stack final (HTMX/Flutter) não fechou. Stack candidata em ADR-0001.

---

## Convenções gerais

- Acessibilidade: WCAG 2.1 AA mínimo em todas as telas (lei brasileira para serviços digitais).
- Navegação por teclado obrigatória em fluxos críticos (login, MFA, LGPD).
- Mensagens de erro em PT-BR, genéricas em fluxos sensíveis (`SEC-001`).
- Toda ação destrutiva exige confirmação dupla (modal + digitar palavra-chave).
- Toda tela respeita perfil ativo: botões/abas que usuário não pode usam estado disabled com tooltip "você não tem permissão (perfil X)".

---

## Telas

### Tela 1: Login

**Propósito:** entrada principal do sistema (usuários autenticados).
**Persona principal:** todos os usuários.
**US:** `US-ACS-001`, `US-ACS-002`.
**Acessível por:** URL raiz do tenant (ex: `<tenant>.afere.app/login`) ou subdomain configurado.

**Elementos:**
- Campo `email` (validação formato).
- Campo `senha` (mascarado, toggle "mostrar senha").
- Botão "Entrar".
- Link "Esqueci minha senha" → tela 3.
- (sem link "criar conta" — usuários só são criados por admin tenant).

**Estados:**
- Vazio: foco em `email`.
- Carregando: botão disabled + spinner.
- Erro (`SEC-001`): "Email ou senha incorretos" (sem dizer qual).
- Erro bloqueio (`SEC-002`): "Muitas tentativas. Tente novamente em X minutos."
- Sucesso parcial (MFA): redireciona pra Tela 2.
- Sucesso total: redireciona pra dashboard do perfil.

**Acessibilidade:** labels associados, foco visível, autocomplete `username`/`current-password`.
**Mobile:** responsivo (PWA + app Flutter — ver ADR-0003).

---

### Tela 2: Validação MFA (TOTP)

**Propósito:** segundo fator após senha válida.
**US:** `US-ACS-002`.
**Acessível por:** redirect automático após Tela 1.

**Elementos:**
- Campo `código` (6 dígitos, numeric, autocomplete `one-time-code`).
- Botão "Validar".
- Link "Perdi meu autenticador" → abre ticket para admin tenant (NÃO auto-serviço).

**Estados:**
- Carregando.
- Erro: "Código inválido. Tentativa X/3."
- Após 3 falhas: sessão invalidada, redirect pra Tela 1 com mensagem.
- Sucesso: redirect pra dashboard.

**Acessibilidade:** input numérico, auto-submit ao completar 6 dígitos.

---

### Tela 3: Recuperação de senha (solicitar)

**Propósito:** solicitar link de redefinição.
**US:** `US-ACS-003`.

**Elementos:**
- Campo `email`.
- Botão "Enviar link".
- Texto explicativo: "Se o email estiver cadastrado, você receberá um link em alguns minutos."

**Estados:**
- Sempre mostra mensagem genérica (`SEC-001`): "Se o email existir, enviaremos um link."
- Rate-limit (`SEC-002`): bloqueio silencioso (mostra mesma mensagem mas não envia).

---

### Tela 4: Recuperação de senha (redefinir via link)

**Propósito:** definir nova senha com link válido.
**US:** `US-ACS-003`.
**Acessível por:** link do email.

**Elementos:**
- Campo `nova senha` (12 chars min, indicador de força).
- Campo `confirmar senha`.
- Botão "Redefinir".

**Estados:**
- Link expirado/usado: "Link inválido. Solicite novo."
- Senha fraca: indicador vermelho + lista de critérios faltando.
- Sucesso: redirect Tela 1 com toast "Senha redefinida. Faça login."

---

### Tela 5: Setup MFA (primeiro uso ou regenerar)

**Propósito:** vincular app autenticador à conta.
**US:** `US-ACS-002`.

**Elementos:**
- QR code do segredo TOTP.
- Texto do segredo (caso QR não funcione).
- Lista de apps recomendados (Google Authenticator, Authy, 1Password — `SEC-001` proíbe SMS).
- Campo `código de teste` (valida que app está sincronizado antes de salvar).
- Botão "Ativar MFA".

**Estados:**
- Código de teste inválido: "Código incorreto. Verifique horário do dispositivo."
- Sucesso: mostra 8 códigos de backup (one-shot, baixar PDF) + toast "MFA ativado".

---

### Tela 6: Meu Perfil

**Propósito:** auto-serviço do usuário.
**US:** `US-ACS-010`, `US-ACS-002`, `US-ACS-007`.

**Elementos:**
- Dados pessoais (nome, foto, email — email não editável por auto-serviço).
- Botão "Trocar senha" → modal.
- Botão "Regenerar MFA" → confirma + Tela 5.
- Aba "Sessões ativas" — lista (dispositivo, IP, localização aprox, última atividade), botão "Encerrar" por linha, botão "Encerrar todas-exceto-esta".
- Aba "Logins recentes" — últimos 90 dias, botão "Esse não fui eu" (dispara `acs.sessao.repudiada`).

---

### Tela 7: Gestão de Usuários (admin tenant)

**Propósito:** CRUD de usuários do tenant.
**Persona:** Admin do Tenant.
**US:** `US-ACS-001`, `US-ACS-004`, `US-ACS-006`.

**Elementos:**
- Lista de usuários (filtros: status, perfil, filial).
- Botão "Novo usuário" → modal (nome, email, CPF opcional, perfil, filiais, MFA obrigatório).
- Por linha: ver, editar, desativar (NÃO excluir — só LGPD), forçar logout.

**Estados:**
- Vazio: ilustração + botão "Criar primeiro usuário".

**Acessibilidade:** tabela com cabeçalhos `<th>`, ordenação por teclado.

---

### Tela 8: Perfis e Permissões (admin tenant)

**Propósito:** criar perfis e configurar matriz módulo × tela × ação.
**US:** `US-ACS-004`, `US-ACS-005`.

**Elementos:**
- Lista de perfis (sementes marcadas com badge "Padrão", não editáveis em estrutura).
- Botão "Novo perfil".
- Detalhe do perfil: nome, descrição, MFA obrigatório (toggle), timeout sessão, matriz de permissões.
- Matriz: árvore expansível módulo → tela → ações (criar/ler/editar/excluir + sensíveis). Checkbox por nó.
- Botão "Salvar" + preview "X usuários serão afetados".

**Estados:**
- Edição de perfil-semente: alguns campos disabled com tooltip.
- Salvamento: invalida cache de autorização + toast "Permissões atualizadas para N usuários".

---

### Tela 9: Filiais e Vínculos (admin tenant)

**Propósito:** vincular usuário ↔ filial.
**US:** `US-ACS-006`.

**Elementos:**
- Tabela usuário × filial (checkbox), botão "Salvar".
- Seletor de filial padrão por usuário.

---

### Tela 10: Trilha de Auditoria

**Propósito:** ver tudo que aconteceu (admin / auditor).
**Persona:** Admin Tenant, Auditor RBC, Admin Global.
**US:** `US-ACS-008`.

**Elementos:**
- Filtros: período (date range), usuário, tipo de evento, entidade afetada, IP, texto livre.
- Tabela: timestamp, usuário, ação, entidade, IP, expand para ver diff JSON.
- Botão "Exportar" → ver `exports.md` (CSV/PDF assinado).
- Paginação cursor-based (não offset — performance em milhões de eventos).

**Estados:**
- Vazio (filtros sem match): "Nenhum evento no período."
- Carregando: skeleton.

**Importante:** sem botões editar/excluir — `INV-001` WORM.

---

### Tela 11: Histórico de Registro Crítico

**Propósito:** versão a versão de 1 registro (cliente, certificado, OS, lançamento).
**US:** `US-ACS-009`.
**Acessível por:** aba "Histórico" dentro do detalhe do registro.

**Elementos:**
- Linha do tempo vertical, cada nó = versão (data, usuário, resumo).
- Click no nó: diff campo-a-campo (antes/depois lado a lado).
- Botão "Restaurar esta versão" (só perfis com permissão dedicada — gera evento `acs.registro.restaurado`).

---

### Tela 12: Sessões Globais (admin tenant)

**Propósito:** ver e encerrar sessões de qualquer usuário do tenant.
**US:** `US-ACS-010`.

**Elementos:**
- Tabela: usuário, dispositivo, IP, localização, iniciada, última atividade.
- Filtros: usuário, IP, ativo nos últimos N min.
- Botão "Encerrar" por linha, "Encerrar todas do usuário X".

---

### Tela 13: Portal LGPD do Titular

**Propósito:** auto-serviço do titular para direitos LGPD.
**Persona:** Titular de Dados Pessoais (sem ser usuário do sistema).
**US:** `US-ACS-012`, `US-ACS-013`.
**Acessível por:** URL pública do tenant `<tenant>.afere.app/lgpd`.

**Fluxo de autenticação:**
- Campo CPF + email.
- Token de 6 dígitos enviado por email (ou SMS — decisão pendente).
- Token expira em 60min, use-once.

**Tela principal (após autenticar):**
- 3 botões grandes: "Exportar meus dados", "Solicitar anonimização", "Solicitar exclusão".
- Lista de consentimentos ativos, cada um com toggle "Revogar".
- Lista de solicitações anteriores e status.
- Texto explicativo em linguagem leiga: "Exclusão pode levar até X anos por causa da lei (Receita 5 anos, ISO 17025 ~25 anos pra certificados)."

**Estados:**
- Solicitação aberta: confirmação com prazo + número de protocolo.
- Solicitação concluída: link de download (válido 30 dias) + comprovante PDF assinado.

---

### Tela 14: Termo de Consentimento (apresentação)

**Propósito:** mostrar termo na hora de coletar consentimento.
**US:** `US-ACS-013`.
**Contexto:** disparada por outros módulos (cadastro de cliente, captura web, etc.) — não vive isolada.

**Elementos:**
- Texto do termo (versionado).
- Lista de finalidades com toggle individual.
- Botão "Aceitar selecionados".
- Hash + versão visíveis (para auditoria).

---

### Tela 15: Status de Segurança do Tenant (resumo visual)

**Propósito:** painel "tudo está cifrado/seguro?" para o admin tenant dormir tranquilo.
**US:** `US-ACS-011`.
**Persona:** Admin do Tenant, Roldão.

**Elementos:**
- Cards verde/amarelo/vermelho:
  - Dados em trânsito (TLS): verde.
  - Dados em repouso (KMS): verde + data última rotação.
  - Backup cifrado: verde + última verificação.
  - Cobertura MFA perfis sensíveis: verde 100% / amarelo se < 100%.
  - Solicitações LGPD no prazo: verde se 100%.
- Link "ver detalhes técnicos" → `docs/conformidade/comum/seguranca-dados.md`.

---

## Componentes reutilizáveis

Componentes compartilhados (botão, modal, toast, badge de status, indicador de força de senha) ficam em `../../../comum/contratos/ui.md` quando esse doc existir.

## Como esta lista evolui

- Tela nova → adicionar + linkar US.
- Mudança de UX → bump CHANGELOG.
- Tela descontinuada → marcar `@deprecated` + janela de migração.
