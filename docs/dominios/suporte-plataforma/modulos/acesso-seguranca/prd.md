---
owner: roldao
revisado_em: 2026-05-17
proximo_review: 2026-08-17
status: draft
diataxis: explanation
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md#RAT-08
  - docs/conformidade/comum/retencao-matriz.md
  - docs/comum/isolamento-multi-tenant.md
  - REGRAS-INEGOCIAVEIS.md
---

# PRD — Módulo Acesso, Segurança e Controle de Usuários (ACS)

> Visão de PRODUTO (telas, fluxos, perfis). Detalhes técnicos de auth/RBAC estão em `docs/arquitetura/cross-cutting/auth-rbac.md`; detalhes de criptografia/LGPD em `docs/conformidade/comum/seguranca-dados.md` e `docs/conformidade/comum/lgpd-rat.md`. Isolamento por tenant/filial em `docs/comum/isolamento-multi-tenant.md`.

---

## 1. O que este módulo é

Porta de entrada do Aferê. Consolida o que o usuário final vê e faz para entrar no sistema, ser autenticado, ter seu acesso restrito por perfil/empresa/filial, e exercer direitos LGPD. Toda a malha técnica (sessão, RBAC, criptografia, RLS) é referenciada — aqui descrevemos o **produto**: telas, fluxos, mensagens, expectativas.

Atende todos os perfis do ERP (atendente, técnico de campo, metrologista, financeiro, gestor, admin de tenant, admin global) e o titular de dados pessoais (cliente final cadastrado).

## 2. Por que este módulo existe

- Sem login/MFA confiável, o Aferê não pode tratar dado fiscal nem de calibração regulada.
- Sem perfis por função, o atendente vê o financeiro e o técnico vê o cadastro de clientes — vazamento interno.
- Sem isolamento por empresa/filial, dois tenants (ou duas filiais do mesmo tenant) se veem — violação fatal de multi-tenancy (`INV-TENANT-001..004`).
- Sem trilha de auditoria, não há defesa em incidente (LGPD Art. 46) nem evidência em fiscalização RBC.
- Sem fluxo LGPD (exportar/anonimizar/excluir), Aferê é ilegal de operar.

## 3. Personas

Ver `personas.md` deste módulo + `../../personas.md` (domínio) + `docs/comum/personas.md` (transversais).

## 4. Escopo (o que ESTÁ neste módulo)

- Tela de login (usuário/senha + MFA).
- Tela de recuperação de senha por email.
- Tela de configuração de MFA (TOTP — Google Authenticator, Authy, 1Password).
- Tela "Meu perfil" (trocar senha, regenerar MFA, ver sessões ativas).
- Tela de gestão de usuários (admin do tenant cria/edita/desativa usuário).
- Tela de perfis e permissões (admin atribui perfil = conjunto de permissões).
- Tela de matriz de permissão por tela/módulo/ação (visualização).
- Tela de empresas/filiais (vínculo usuário ↔ filiais que pode operar).
- Tela de trilha de auditoria (filtros por usuário, data, ação, registro).
- Tela de histórico de alterações de um registro crítico (cliente, certificado, ordem de serviço, lançamento financeiro).
- Tela de sessões ativas (admin força logout).
- Tela LGPD do titular: exportar meus dados, solicitar anonimização, solicitar exclusão.
- Tela de registro de consentimentos do titular.
- Tela de logins recentes (usuário vê próprio histórico — IP, localização aproximada, dispositivo).

## 5. Non-goals (o que NÃO está neste módulo)

> LLM não infere por omissão.

- **NÃO** implementa SSO corporativo (SAML/OIDC) no MVP-1 — fica como gancho de extensão, decisão futura via ADR.
- **NÃO** implementa biometria (FaceID/TouchID) no MVP-1.
- **NÃO** implementa SMS como segundo fator (apenas TOTP — SMS é vulnerável a SIM-swap).
- **NÃO** implementa chave física FIDO2/WebAuthn no MVP-1.
- **NÃO** define a engine criptográfica (responsabilidade de `seguranca-dados.md` + AWS KMS MRK).
- **NÃO** define o middleware de tenant (responsabilidade de `isolamento-multi-tenant.md` + ADR-0002 RLS).
- **NÃO** trata assinatura digital A3 do certificado RBC (módulo de calibração + ADR-0009).
- **NÃO** trata política de retenção de log (responsabilidade de `retencao-matriz.md`).
- **NÃO** substitui o RAT LGPD (formal em `lgpd-rat.md`).

## 6. User Stories

### US-ACS-001: Login com usuário e senha

**Como** qualquer usuário ativo, **quero** entrar com email + senha, **para** acessar o Aferê.

**AC:**
- **AC-ACS-001-1**: GIVEN usuário ativo com senha válida, WHEN envia email+senha corretos, THEN entra no dashboard padrão do seu perfil.
- **AC-ACS-001-2**: GIVEN credencial inválida, WHEN envia, THEN vê mensagem genérica "email ou senha incorretos" (NÃO revelar se email existe — anti-enumeração).
- **AC-ACS-001-3**: GIVEN 5 tentativas falhadas em 15min do mesmo IP, WHEN tenta novamente, THEN é bloqueado por 30min e registrado evento `acs.login.bloqueado`.
- **AC-ACS-001-4**: GIVEN usuário desativado, WHEN tenta entrar, THEN vê mensagem genérica + evento `acs.login.usuario_desativado`.

**Invariantes:** `INV-001` (trilha WORM), `SEC-LOG-001` (mensagens genéricas — não revela existência de email), `SEC-001` (anti-enumeração), `SEC-002` (rate-limit anti-bruteforce).

### US-ACS-002: Autenticação em dois fatores (MFA TOTP)

**Como** usuário, **quero** segundo fator TOTP, **para** proteger conta mesmo se senha vazar.

**AC:**
- **AC-ACS-002-1**: GIVEN usuário sem MFA, WHEN admin tenant marca perfil como "MFA obrigatório", THEN no próximo login usuário é forçado a cadastrar TOTP antes de acessar qualquer tela.
- **AC-ACS-002-2**: GIVEN usuário com MFA cadastrado, WHEN faz login OK, THEN vê tela de código TOTP de 6 dígitos.
- **AC-ACS-002-3**: GIVEN código TOTP inválido 3x seguidas, WHEN tenta, THEN sessão é invalidada e usuário volta para tela de login.
- **AC-ACS-002-4**: GIVEN usuário perdeu acesso ao TOTP, WHEN clica "perdi meu autenticador", THEN admin tenant recebe ticket pra regenerar segredo presencialmente (não auto-serviço por email).

**Invariantes:** `SEC-MFA-001` (MFA TOTP obrigatório para perfis sensíveis: admin tenant, financeiro, metrologista, RT), `INV-009` (MFA pra acesso a CDE quando PCI aplicar), `SEC-001`.

### US-ACS-003: Recuperação de senha por email

**Como** usuário que esqueceu senha, **quero** redefinir por link de email, **para** voltar a acessar.

**AC:**
- **AC-ACS-003-1**: GIVEN email cadastrado, WHEN clica "esqueci senha" e informa email, THEN sistema envia link de uso único válido por 30min (mensagem genérica mesmo se email não existir).
- **AC-ACS-003-2**: GIVEN link válido, WHEN abre, THEN tela permite definir nova senha respeitando política (12 chars min, mistura).
- **AC-ACS-003-3**: GIVEN link expirado ou já usado, WHEN abre, THEN vê mensagem "link inválido — solicite novo".
- **AC-ACS-003-4**: GIVEN usuário com MFA, WHEN redefine senha, THEN MFA continua exigido (recuperação de senha NÃO derruba MFA).

**Invariantes:** `SEC-LOG-001` (mensagem genérica mesmo se email não existir), `SEC-001` (anti-enumeração na resposta), `SEC-002`.

### US-ACS-004: Perfis de acesso por função

**Como** admin do tenant, **quero** criar perfis (Atendente, Técnico, Metrologista, Financeiro, Gestor), **para** atribuir conjuntos de permissões sem configurar usuário por usuário.

**AC:**
- **AC-ACS-004-1**: GIVEN admin, WHEN cria perfil "Atendente", THEN escolhe quais módulos/telas/ações o perfil acessa.
- **AC-ACS-004-2**: GIVEN perfil existente vinculado a N usuários, WHEN admin altera permissões do perfil, THEN mudança propaga a todos os usuários na próxima ação (não em sessão ativa — sessão revalida a cada operação sensível).
- **AC-ACS-004-3**: Perfis "semente" pré-configurados no tenant novo: Admin Tenant, Atendente, Técnico Campo, Metrologista, Financeiro, Gestor, Somente-Leitura.

**Invariantes:** `INV-001` (trilha WORM em mudanças de perfil), `SEC-LEAST-PRIV-001` (princípio do menor privilégio).

### US-ACS-005: Permissões por tela/módulo/ação

**Como** admin do tenant, **quero** matriz fina (módulo × tela × ação CRUD), **para** customizar perfil sem precisar pedir dev.

**AC:**
- **AC-ACS-005-1**: GIVEN matriz visível, WHEN admin marca/desmarca célula, THEN salva e refletido na próxima ação do usuário.
- **AC-ACS-005-2**: GIVEN usuário sem permissão tenta ação X, WHEN clica botão, THEN vê mensagem "você não tem permissão para esta ação" + evento `acs.acesso.negado` registrado.
- **AC-ACS-005-3**: Ações sensíveis (excluir registro fiscal, alterar lançamento conciliado, emitir certificado RBC) exigem permissão dedicada — não basta "editar".

**Invariantes:** `SEC-LEAST-PRIV-001` (matriz RBAC fina + permissão dedicada pra ações sensíveis), `SEC-002`.

### US-ACS-006: Controle de acesso por empresa/unidade (tenant + filial)

**Como** admin de tenant com várias filiais, **quero** restringir usuário a filiais específicas, **para** atendente da filial A não ver dados da filial B.

**AC:**
- **AC-ACS-006-1**: GIVEN usuário vinculado a filial A, WHEN abre lista de clientes, THEN vê só clientes da filial A.
- **AC-ACS-006-2**: GIVEN usuário com acesso a filiais A e B, WHEN entra, THEN tela inicial mostra seletor de filial (escolhe contexto operacional).
- **AC-ACS-006-3**: GIVEN admin global de tenant, WHEN entra, THEN enxerga consolidado de todas as filiais.
- **AC-ACS-006-4**: Tentativa de URL direta a registro de outra filial → 404 (não 403 — não revelar existência).

**Invariantes:** `INV-TENANT-001` (toda query carrega tenant_id), `INV-TENANT-002` (filtro filial em cima do tenant_id), `INV-TENANT-003` (impossível escapar do tenant via URL), `INV-TENANT-004` (admin global de tenant NÃO atravessa tenants), `SEC-TENANT-001`.

### US-ACS-007: Registro de login, IP e localização aproximada

**Como** usuário ou admin, **quero** ver onde/quando minhas sessões aconteceram, **para** detectar acesso indevido.

**AC:**
- **AC-ACS-007-1**: GIVEN login OK, WHEN sessão inicia, THEN sistema registra timestamp, IP, user-agent, localização aproximada (país/cidade via IP — sem GPS).
- **AC-ACS-007-2**: GIVEN usuário abre "logins recentes", THEN vê tabela com últimos 90 dias + botão "esse não fui eu" (que dispara alerta ao admin tenant + força logout global).
- **AC-ACS-007-3**: Localização aproximada NÃO usa geolocalização do navegador (não pede permissão) — só IP.
- **AC-ACS-007-4 (LGPD):** Tratamento atende base **Legítimo interesse (art. 7º IX)** para segurança da conta + **Obrigação regulatória (art. 7º II)** para audit (RAT-08). Sem consentimento adicional (não-PII além de identificação ligada à conta).
- **AC-ACS-007-5 (Retenção):** Registros conforme `retencao-matriz.md` linha "Audit trail" (2 anos default) e linha "Audit trail (ações em paths sensíveis)" (5-10 anos para `auth/`, `kms/`, `financeiro/`, `migrations/`); após prazo: crypto-shredding.

**Invariantes:** `INV-001` (trilha WORM dos logins), `SEC-001`.

### US-ACS-008: Auditoria de ações dos usuários

**Como** admin do tenant ou auditor RBC, **quero** ver tudo que cada usuário fez, **para** investigar incidente ou atender fiscalização.

**AC:**
- **AC-ACS-008-1**: Toda ação de escrita (criar, editar, excluir, emitir, anular, aprovar) registra evento com usuário, timestamp, IP, ação, registro afetado, valores antes/depois (diff).
- **AC-ACS-008-2**: GIVEN admin filtra trilha, WHEN escolhe usuário + período, THEN vê linha do tempo com diffs expansíveis.
- **AC-ACS-008-3**: Trilha é WORM — nenhum perfil (nem admin global) pode editar/apagar evento de auditoria (`INV-001`).
- **AC-ACS-008-4**: Exportação da trilha em CSV/PDF para fiscalização (ver `contratos/exports.md`).

**Invariantes:** `INV-001` (audit WORM imutável), `SEC-LOG-001`, `SEC-001`, `SEC-002`.

### US-ACS-009: Histórico de alterações em registros críticos

**Como** gestor, **quero** ver versão a versão de um cliente/certificado/lançamento, **para** entender quem mudou o quê e quando.

**AC:**
- **AC-ACS-009-1**: GIVEN registro crítico (cliente, certificado RBC, ordem de serviço, lançamento financeiro conciliado), WHEN abre aba "histórico", THEN vê lista cronológica de versões com diff campo-a-campo.
- **AC-ACS-009-2**: Restaurar versão antiga gera evento `acs.registro.restaurado` (mantém histórico — não apaga versões intermediárias).

**Invariantes:** `INV-001` (WORM em histórico de alterações), `SEC-LOG-001`.

### US-ACS-010: Controle de sessões

**Como** usuário ou admin, **quero** gerenciar sessões ativas, **para** derrubar acesso suspeito.

**AC:**
- **AC-ACS-010-1**: Usuário vê próprias sessões ativas (dispositivo, IP, última atividade) e pode encerrar individualmente ou todas-exceto-atual.
- **AC-ACS-010-2**: Admin tenant vê e pode encerrar sessões de qualquer usuário do tenant.
- **AC-ACS-010-3**: Sessão expira por inatividade (30min default — configurável por perfil até máximo 8h).
- **AC-ACS-010-4**: Troca de senha encerra todas as sessões do usuário (exceto a atual).

**Invariantes:** `SEC-LEAST-PRIV-001` (admin tenant gerencia sessões do tenant), `SEC-002`.

### US-ACS-011: Criptografia de dados sensíveis (visão produto)

**Como** Roldão/admin, **quero** garantia de que CPF, telefone, senha, anexo PDF estão cifrados, **para** dormir tranquilo com LGPD.

**AC:**
- **AC-ACS-011-1**: Tela "Status de segurança do tenant" mostra: dados em trânsito cifrados (sim/não), dados em repouso cifrados (sim/não), backup cifrado (sim/não), última rotação de chave (data).
- **AC-ACS-011-2**: Detalhes técnicos (algoritmos, KMS, rotação) NÃO ficam aqui — link para `docs/conformidade/comum/seguranca-dados.md`.

**Invariantes:** ver `seguranca-dados.md`. Aqui referência apenas.

### US-ACS-012: Exportação, anonimização e exclusão LGPD

**Como** titular de dados pessoais (cliente final cadastrado) ou admin atendendo solicitação, **quero** três ações LGPD, **para** cumprir direito do titular.

**AC:**
- **AC-ACS-012-1**: Tela "Meus dados (LGPD)" disponível para titular logado com 3 botões: "Exportar meus dados", "Solicitar anonimização", "Solicitar exclusão".
- **AC-ACS-012-2**: Exportação gera ZIP com JSON + PDFs em até 15 dias (prazo LGPD Art. 19) e disponibiliza para download por 30 dias.
- **AC-ACS-012-3**: Anonimização substitui dados pessoais por hash irreversível mantendo integridade contábil/fiscal (CPF vira `***.***.***-**` + hash interno; nome vira "Titular Anonimizado #N").
- **AC-ACS-012-4**: Exclusão respeita retenção legal — pedido entra em fila e só executa após vencimento de retenção mínima (Receita 5 anos, ISO 17025 ~25 anos para certificado). Titular é informado do prazo.
- **AC-ACS-012-5**: Toda solicitação LGPD gera ticket auditável + comprovante PDF para o titular.

**Invariantes:** ver `lgpd-rat.md` + `retencao-matriz.md`. Aqui só fluxo de produto.

### US-ACS-013: Registro de consentimento do titular

**Como** sistema, **quero** registrar consentimento explícito do titular para cada finalidade, **para** evidenciar base legal LGPD.

**AC:**
- **AC-ACS-013-1**: GIVEN cadastro de cliente com dado pessoal, WHEN salva, THEN sistema apresenta tela de consentimento por finalidade (atendimento, marketing, compartilhamento parceiro X) com toggle individual.
- **AC-ACS-013-2**: Cada consentimento registra: titular, finalidade, base legal, versão do termo aceito, timestamp, IP, identificador da política vigente.
- **AC-ACS-013-3**: Titular pode revogar consentimento a qualquer tempo na tela "Meus dados (LGPD)" — revogação gera evento e ajusta processamentos futuros.
- **AC-ACS-013-4**: Histórico de consentimentos (versões) é WORM — não pode ser editado.

**Invariantes:** `INV-001`, ver `lgpd-rat.md`.

---

## 7. Métricas de sucesso

Ver `metricas.md`. Resumo:
- Taxa de adesão MFA em perfis sensíveis = 100%
- Tempo médio de resposta a solicitação LGPD < 15 dias
- Zero incidentes de vazamento cross-tenant
- Tentativas de login bloqueadas / total < 5%

## 8. NFR

- **Performance:** login completo (incluindo MFA) < 2s p95.
- **Disponibilidade:** SLO 99.9% (login é caminho crítico — sem login, nada funciona).
- **Segurança:** `SEC-001`, `SEC-002`, `SEC-TENANT-001` aplicáveis em todas as US.
- **Acessibilidade:** WCAG 2.1 AA na tela de login (obrigatório por lei brasileira para serviços digitais).

## 9. Glossário

Ver `glossario.md` deste módulo.

## 10. Como este PRD evolui

- US nova → próximo `US-ACS-NNN` livre.
- Mudança em AC já implementado → ADR + novo teste.
- Decisão sobre SSO/biometria/WebAuthn → ADR dedicada (hoje non-goal).
