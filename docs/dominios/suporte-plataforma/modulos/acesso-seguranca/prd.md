---
owner: roldao
revisado-em: 2026-05-27
proximo-review: 2026-08-27
status: stable
modulo: acesso-seguranca
dominio: suporte-plataforma
diataxis: explanation
audiencia: agente
relacionados:
  - docs/arquitetura/cross-cutting/auth-rbac.md
  - docs/conformidade/comum/seguranca-dados.md
  - docs/conformidade/comum/lgpd-rat.md
  - docs/conformidade/comum/retencao-matriz.md
  - docs/comum/isolamento-multi-tenant.md
  - docs/adr/0007-camada-dominio-gerador-spec.md
  - docs/adr/0012-autorizacao-unificada.md
  - docs/adr/0023-os-com-atividades.md
  - docs/adr/0030-vigencia-temporal-canonica.md
  - docs/adr/0031-soft-delete-tres-padroes.md
  - docs/adr/0032-fk-cross-modulo-anonimizacao.md
  - docs/adr/0033-bus-idempotencia-consumer.md
  - docs/adr/0034-saga-compensacao-cross-modulo.md
  - docs/adr/0038-familia-inv-auth.md
  - docs/adr/0051-propagacao-adr0023-modulos-wave-a.md
  - docs/adr/0067-perfil-regulatorio-tenant-entidade-temporal.md
  - docs/conformidade/comum/matriz-feature-perfil.md
  - REGRAS-INEGOCIAVEIS.md
historico:
  - 2026-05-27 — saneamento Onda 3 Batch B4 pré-Wave A: filial-ativa lida do server-side via ContextVar `filial_atual_context` (fecha CRÍTICO L6 — payload `filial_id` ignorado); ADR-0038 família INV-AUTH (lockout / política de senha / sessão idle / retenção 365d); US-ACS-014 RBAC condicional por perfil regulatório (ADR-0067); persona inline; AC binários GIVEN-WHEN-THEN com ID `AC-ACS-NNN-N`; deps ADR completas; vocabulário Wave A; métricas inline; matriz feature × perfil; biometria FaceID/TouchID confirmada non-goal Wave A (porta aberta Wave B com DPIA); status `draft` → `stable`.
---

# PRD — Módulo Acesso, Segurança e Controle de Usuários (ACS)

> Visão de PRODUTO (telas, fluxos, perfis). Detalhes técnicos de auth/RBAC em `docs/arquitetura/cross-cutting/auth-rbac.md`; criptografia/LGPD em `docs/conformidade/comum/seguranca-dados.md` e `lgpd-rat.md`; isolamento por tenant/filial em `docs/comum/isolamento-multi-tenant.md`; invariantes canônicas de autenticação em ADR-0038 (INV-AUTH-001..005).

---

## 1. O que este módulo é

Porta de entrada do Aferê. Consolida o que o usuário final vê e faz para entrar no sistema, ser autenticado, ter seu acesso restrito por perfil/empresa/filial, e exercer direitos LGPD. Toda a malha técnica (sessão, RBAC, criptografia, RLS) é referenciada — aqui descrevemos o **produto**: telas, fluxos, mensagens, expectativas. Inclui RBAC **condicional pelo perfil regulatório do tenant** (ADR-0067) — perfil A tem perfis funcionais que perfil D simplesmente não enxerga.

Atende todos os perfis funcionais do ERP (atendente, técnico de campo, metrologista, financeiro, gestor, admin de tenant, admin global) e o titular de dados pessoais.

## 2. Por que este módulo existe

- Sem login/MFA confiável, o Aferê não pode tratar dado fiscal nem de calibração regulada.
- Sem perfis por função, o atendente vê o financeiro e o técnico vê o cadastro de clientes — vazamento interno.
- Sem **isolamento server-side por filial**, payload manipulado vaza dados cross-filial (CRÍTICO L6 saneamento 2026-05-27 — corrigido em AC-ACS-006-2).
- Sem trilha de auditoria, não há defesa em incidente (LGPD Art. 46) nem evidência em fiscalização RBC.
- Sem fluxo LGPD (exportar/anonimizar/excluir), Aferê é ilegal de operar.
- Sem **lockout anti-bruteforce + política de senha NIST + sessão idle limitada** (INV-AUTH-001..005 — ADR-0038), perfis sensíveis (financeiro, signatário, metrologista) viram NC ANPD/CGCRE.

## 3. Personas (inline)

- **P-ACS-01 Admin de tenant** — cria usuário, atribui perfil funcional, restringe filiais, gerencia sessões; opera majoritariamente em desktop.
- **P-ACS-02 Usuário operacional** (atendente, técnico, metrologista) — autentica-se com email + senha + TOTP, escolhe filial ativa, navega no contexto restrito.
- **P-ACS-03 Titular de dados (cliente final cadastrado)** — usa "Meus dados (LGPD)" pra exportar/anonimizar/excluir; tela acessível em smartphone.
- **P-ACS-04 Auditor RBC / Fiscal** — consulta trilha WORM filtrada por período + usuário; exporta CSV/PDF pra processo (perfil A do tenant frequentemente exige).
- **P-ACS-05 Admin global Aferê** — não atravessa tenant (INV-TENANT-004); opera só metadados tenant (provisionamento, suporte).

Detalhe operacional em `personas.md` deste módulo.

## 4. Escopo (Wave A — o que ESTÁ neste módulo)

- Tela de login (usuário/senha + MFA TOTP — ADR-0038 INV-AUTH-001..002).
- Tela de recuperação de senha por email.
- Tela de configuração de MFA (TOTP — Google Authenticator, Authy, 1Password).
- Tela "Meu perfil" (trocar senha, regenerar MFA, ver sessões ativas).
- Tela de gestão de usuários (admin do tenant cria/edita/desativa usuário).
- Tela de perfis e permissões (admin atribui perfil = conjunto de permissões).
- Tela de matriz de permissão por tela/módulo/ação (visualização).
- Tela de empresas/filiais (vínculo usuário ↔ filiais que pode operar).
- **Seletor de filial ativa** (UI) com decisão **server-side** via `Session.filial_atual_id` (AC-ACS-006-2 — fecha CRÍTICO L6).
- Tela de trilha de auditoria (filtros por usuário, data, ação, registro).
- Tela de histórico de alterações de um registro crítico (cliente, certificado, OS, lançamento financeiro).
- Tela de sessões ativas (admin força logout).
- Tela LGPD do titular: exportar meus dados, solicitar anonimização, solicitar exclusão.
- Tela de registro de consentimentos do titular.
- Tela de logins recentes (usuário vê histórico — IP, localização aproximada, dispositivo).

## 5. Non-goals (Wave A — o que NÃO está)

> LLM não infere por omissão.

- **NÃO** implementa SSO corporativo (SAML/OIDC) no Wave A — fica como gancho de extensão (ADR-0012 prevê adapter); decisão Wave B via ADR.
- **NÃO** implementa biometria FaceID/TouchID **no Wave A** — porta aberta para Wave B com **DPIA dedicada** (dado biométrico = dado sensível LGPD art. 5º II), e somente onde existe necessidade operacional documentada (cl. INV-OS-ACEITE-BIO-001 é caso à parte e fica em `operacao/os`).
- **NÃO** implementa SMS como segundo fator (apenas TOTP — SMS é vulnerável a SIM-swap).
- **NÃO** implementa chave física FIDO2/WebAuthn no Wave A (V2 backlog).
- **NÃO** define a engine criptográfica (responsabilidade de `seguranca-dados.md` + AWS KMS MRK).
- **NÃO** define o middleware de tenant (responsabilidade de `isolamento-multi-tenant.md` + ADR-0002 RLS).
- **NÃO** trata assinatura digital A3 do certificado RBC (módulo de calibração + ADR-0009).
- **NÃO** trata política de retenção de log (responsabilidade de `retencao-matriz.md` + ADR-0038 INV-AUTH-005).
- **NÃO** substitui o RAT LGPD (formal em `lgpd-rat.md`).

## 6. Perfil regulatório (ADR-0067)

Este módulo é transversal (todos os perfis A/B/C/D usam autenticação), mas a **lista de perfis funcionais (papéis) habilitados depende do perfil regulatório do tenant** — RBAC condicional via ADR-0067:

| Papel funcional disponível | A | B | C | D |
|---|---|---|---|---|
| `admin_tenant` | ✅ | ✅ | ✅ | ✅ |
| `tecnico_comercial` / `atendente` | ✅ | ✅ | ✅ | ✅ |
| `cliente_externo_leitura` | ✅ | ✅ | ✅ | ✅ |
| `financeiro` | ✅ | ✅ | ✅ | ✅ |
| `tecnico_campo` | ✅ | ✅ | ✅ | ✅ |
| `metrologista_bancada` | ✅ | ✅ | ✅ | ⚪ opcional |
| `rt_signatario` (RT acreditado) | ✅ | 🟡 RT rastreável | 🟡 em treinamento | ❌ DESABILITADO |
| `conferente_2a` (2ª conferência cl. 6.2.5) | ✅ OBRIGATÓRIO (se ADR-0026 ligada) | ⚪ opcional | ⚪ opcional | ❌ DESABILITADO |
| `gestor_qualidade` (cl. 8.5 — controle docs SGQ) | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ✅ OBRIGATÓRIO | ❌ DESABILITADO |
| `signatario_a3_iso17025` (selo CGCRE) | ✅ OBRIGATÓRIO | ❌ DESABILITADO | ❌ DESABILITADO | ❌ DESABILITADO |
| `dpo` (LGPD art. 41) | ✅ | ✅ | ✅ | ✅ |

Predicate canônico de gating: `papel_disponivel_para_perfil(papel, tenant.perfil_regulatorio)`. Fail-closed: se perfil indeterminado, todos os papéis sensíveis (signatário, conferente, gestor_qualidade) são bloqueados.

Detalhe completo em `docs/conformidade/comum/matriz-feature-perfil.md`.

## 7. User Stories

### US-ACS-001 — Login com usuário e senha

**Como** usuário ativo, **quero** entrar com email + senha, **para** acessar o Aferê.

- **AC-ACS-001-1**: GIVEN usuário ativo com senha válida + sem MFA pendente, WHEN envia email+senha corretos, THEN entra no dashboard padrão do seu papel funcional.
- **AC-ACS-001-2**: GIVEN credencial inválida (email não existe, senha errada, ou conta bloqueada), WHEN envia, THEN sistema responde com **mensagem genérica única** "email ou senha incorretos" — INV-AUTH-001 §"Não vaza informação".
- **AC-ACS-001-3**: GIVEN 5 tentativas falhadas em 15min para o mesmo `email` OU o mesmo `ip_hash`, WHEN tenta novamente, THEN conta entra em estado `bloqueado` por 30min + emite `AcessoSeguranca.LoginBloqueado` (ADR-0038 INV-AUTH-001).
- **AC-ACS-001-4**: GIVEN usuário desativado (`Usuario.deletado_em IS NOT NULL` — padrão C ADR-0031), WHEN tenta entrar, THEN mensagem genérica + evento `acs.login.usuario_desativado` audit.
- **INV:** INV-001 (WORM), INV-AUTH-001..002 (ADR-0038), SEC-LOG-001.

### US-ACS-002 — Autenticação em dois fatores (MFA TOTP)

**Como** usuário, **quero** segundo fator TOTP, **para** proteger conta mesmo se senha vazar.

- **AC-ACS-002-1**: GIVEN papel funcional na lista canônica de papéis sensíveis (`admin_tenant`, `financeiro`, `metrologista_bancada`, `rt_signatario`, `signatario_a3_iso17025`, `gestor_qualidade`, `dpo`), WHEN usuário faz primeiro login, THEN sistema força enrollment TOTP antes de qualquer acesso (SEC-MFA-001).
- **AC-ACS-002-2**: GIVEN usuário com MFA cadastrado, WHEN credencial OK, THEN sistema exige código TOTP 6 dígitos antes de criar sessão.
- **AC-ACS-002-3**: GIVEN 3 códigos TOTP inválidos seguidos, WHEN tenta, THEN sessão invalidada + volta pra login + evento `AcessoSeguranca.LoginFalha` `motivo=mfa_invalido`.
- **AC-ACS-002-4**: GIVEN usuário perdeu acesso ao TOTP, WHEN clica "perdi meu autenticador", THEN gera ticket pra `admin_tenant` regenerar segredo presencialmente (não há reset auto-serviço por email — anti-takeover).

### US-ACS-003 — Recuperação de senha por email

**Como** usuário que esqueceu senha, **quero** redefinir por link de email, **para** voltar a acessar.

- **AC-ACS-003-1**: GIVEN email informado em "esqueci senha", WHEN submete, THEN sistema responde com **mensagem genérica única** "se este email está cadastrado, enviamos link" (anti-enumeração) e dispara link único válido por 30min apenas se email existir.
- **AC-ACS-003-2**: GIVEN link válido, WHEN abre, THEN tela permite definir nova senha respeitando **INV-AUTH-002** (12+ chars, 3 de 4 categorias, sem reuso das últimas 5).
- **AC-ACS-003-3**: GIVEN link expirado ou já usado, WHEN abre, THEN vê "link inválido — solicite novo".
- **AC-ACS-003-4**: GIVEN usuário com MFA, WHEN redefine senha, THEN MFA continua exigido (recuperação NÃO derruba MFA).

### US-ACS-004 — Perfis funcionais (papéis) por função

**Como** admin do tenant, **quero** criar perfis funcionais (Atendente, Técnico, Metrologista, Financeiro, Gestor), **para** atribuir conjuntos de permissões sem configurar usuário por usuário.

- **AC-ACS-004-1**: GIVEN admin, WHEN cria papel "Atendente", THEN escolhe módulos/telas/ações que o papel acessa.
- **AC-ACS-004-2**: GIVEN papel existente vinculado a N usuários, WHEN admin altera permissões, THEN mudança propaga na próxima ação sensível (cache Redis TTL ≤ 5min — ADR-0012).
- **AC-ACS-004-3**: GIVEN tenant novo, WHEN provisionado (`provisionar_tenant`), THEN sistema cria papéis-semente **conforme matriz §6** — papéis indisponíveis para o perfil regulatório não são criados (perfil D não tem `rt_signatario`).

### US-ACS-005 — Permissões por tela/módulo/ação

**Como** admin do tenant, **quero** matriz fina (módulo × tela × ação CRUD), **para** customizar papel sem dev.

- **AC-ACS-005-1**: GIVEN matriz aberta, WHEN admin marca/desmarca célula, THEN salva e reflete na próxima ação do usuário.
- **AC-ACS-005-2**: GIVEN usuário sem permissão tenta ação X, WHEN clica botão, THEN UI esconde botão + endpoint responde 403 + evento `acs.acesso.negado` (registrado via `AuthorizationProvider.can()` — ADR-0012).
- **AC-ACS-005-3**: GIVEN ações sensíveis (excluir registro fiscal, alterar lançamento conciliado, emitir certificado RBC), WHEN admin configura papel, THEN matriz **exige permissão dedicada** — não basta marcar "editar" no módulo (SEC-LEAST-PRIV-001).

### US-ACS-006 — Controle de acesso por empresa/filial server-side (CRÍTICO L6 — saneamento 2026-05-27)

**Como** admin de tenant com várias filiais, **quero** restringir usuário a filiais específicas com decisão **server-side** (nunca ler `filial_id` do payload), **para** atendente da filial A não conseguir ver dados da filial B nem manipulando JSON.

- **AC-ACS-006-1**: GIVEN usuário vinculado a filial A apenas, WHEN abre lista de clientes, THEN sistema lê `Session.filial_atual_id` e filtra `WHERE filial_id = session.filial_atual_id` — vê só clientes da filial A.
- **AC-ACS-006-2**: GIVEN payload da request contém `filial_id` (qualquer valor), WHEN backend recebe, THEN **ignora completamente o `filial_id` do payload** e usa `filial_atual_context` (ContextVar populada pelo middleware a partir de `Session.filial_atual_id`). Hook `payload-filial-id-obsoleto-check` (análogo a `payload-tipo-acreditacao-obsoleto-check`) bloqueia commit que adicione handler lendo `request.data["filial_id"]` ou `request.query_params["filial_id"]`. Fecha CRÍTICO L6 saneamento.
- **AC-ACS-006-3**: GIVEN usuário com acesso a filiais A e B, WHEN entra, THEN UI mostra seletor de filial; clique no seletor faz POST `/sessao/trocar-filial` (idempotente, ADR-0033) que atualiza `Session.filial_atual_id` server-side + emite `AcessoSeguranca.FilialAtualTrocada` audit.
- **AC-ACS-006-4**: GIVEN admin global do tenant, WHEN entra, THEN `Session.filial_atual_id = NULL` significa "consolidado tenant" (matriz de permissão decide se papel pode operar consolidado).
- **AC-ACS-006-5**: GIVEN tentativa de URL direta a registro de outra filial (`/clientes/<id>` onde `cliente.filial_id != session.filial_atual_id`), WHEN backend resolve, THEN responde 404 (não 403 — não revelar existência). Aplica também a registros de outro tenant (INV-TENANT-003).
- **INV:** INV-TENANT-001..004, INV-ACS-FILIAL-SERVER-001 (NOVA — `filial_id` jamais lido de payload).

### US-ACS-007 — Registro de login, IP e localização aproximada

**Como** usuário ou admin, **quero** ver onde/quando minhas sessões aconteceram, **para** detectar acesso indevido.

- **AC-ACS-007-1**: GIVEN login OK, WHEN sessão inicia, THEN sistema registra `timestamp`, `ip_hash`, `user_agent_canonico`, `localizacao_aproximada` (país/cidade via IP — sem GPS) em `auth_login_tentativa` (ADR-0038 INV-AUTH-005).
- **AC-ACS-007-2**: GIVEN usuário abre "logins recentes", THEN vê últimos 90 dias + botão "esse não fui eu" (dispara alerta ao `admin_tenant` + força logout global do usuário).
- **AC-ACS-007-3**: Localização aproximada NÃO usa geolocalização do navegador (não pede permissão) — só IP.
- **AC-ACS-007-4 (LGPD):** Tratamento atende base **Legítimo interesse (art. 7º IX)** segurança + **Obrigação regulatória (art. 7º II)** audit (RAT-08).
- **AC-ACS-007-5 (Retenção):** `auth_login_tentativa` retém **365 dias** detalhado (INV-AUTH-005). Após 365d: agregação diária por (`tenant_id`, `dia`, `sucesso`, `motivo_falha`) em `auth_login_tentativa_agregado` — perde PII, mantém contagem.

### US-ACS-008 — Auditoria de ações dos usuários

**Como** admin do tenant ou auditor RBC, **quero** ver tudo que cada usuário fez, **para** investigar incidente ou atender fiscalização.

- **AC-ACS-008-1**: GIVEN qualquer ação de escrita (criar, editar, excluir, emitir, anular, aprovar), WHEN endpoint roda, THEN registra evento com `usuario_id`, `timestamp`, `ip_hash`, `acao`, `recurso_resumo`, `diff_antes_depois`, `perfil_no_evento` (snapshot ADR-0067 §3).
- **AC-ACS-008-2**: GIVEN admin filtra trilha por usuário + período, WHEN consulta, THEN vê linha do tempo com diffs expansíveis.
- **AC-ACS-008-3**: Trilha é WORM — nenhum papel (incluindo admin global Aferê) pode editar/apagar evento de auditoria (INV-001, trigger PG anti-UPDATE/DELETE).
- **AC-ACS-008-4**: GIVEN auditor RBC exporta trilha, WHEN solicita CSV/PDF, THEN sistema gera com `perfil_no_evento` visível por linha (defesa CGCRE retroativa).

### US-ACS-009 — Histórico de alterações em registros críticos

**Como** gestor, **quero** ver versão a versão de um cliente/certificado/lançamento, **para** entender quem mudou o quê e quando.

- **AC-ACS-009-1**: GIVEN registro crítico (cliente, certificado, OS, lançamento financeiro conciliado), WHEN abre aba "histórico", THEN vê lista cronológica de versões com diff campo-a-campo (`JanelaVigencia` ADR-0030 aplica em entidades temporais — RT, certificado).
- **AC-ACS-009-2**: GIVEN restaurar versão antiga, WHEN admin executa, THEN gera evento `acs.registro.restaurado` mantendo histórico — não apaga versões intermediárias.

### US-ACS-010 — Controle de sessões (ADR-0038 INV-AUTH-003)

**Como** usuário ou admin, **quero** gerenciar sessões ativas, **para** derrubar acesso suspeito.

- **AC-ACS-010-1**: Usuário vê próprias sessões ativas (dispositivo, IP_hash, última atividade) e pode encerrar individual ou todas-exceto-atual.
- **AC-ACS-010-2**: Admin tenant vê/encerra sessões de qualquer usuário do tenant.
- **AC-ACS-010-3**: GIVEN inatividade, WHEN passa **30min** (15min se papel sensível), THEN sessão expira + emite `AcessoSeguranca.SessaoEncerrada` `motivo=idle_timeout` (INV-AUTH-003).
- **AC-ACS-010-4**: GIVEN sessão atinge **8h** absolutas (4h se papel sensível), WHEN time-up, THEN re-login obrigatório.
- **AC-ACS-010-5**: GIVEN troca de senha, WHEN nova senha gravada, THEN sistema encerra todas as sessões do usuário exceto a atual.

### US-ACS-011 — Criptografia de dados sensíveis (visão produto)

**Como** Roldão/admin, **quero** garantia de que CPF, telefone, senha, anexo PDF estão cifrados, **para** dormir tranquilo com LGPD.

- **AC-ACS-011-1**: GIVEN tela "Status de segurança do tenant", WHEN admin abre, THEN vê: dados em trânsito cifrados (sim/não), dados em repouso (sim/não), backup (sim/não), última rotação de chave KMS (data).
- **AC-ACS-011-2**: Detalhes técnicos (algoritmos, KMS, rotação) NÃO ficam aqui — link para `docs/conformidade/comum/seguranca-dados.md`.

### US-ACS-012 — Exportação, anonimização e exclusão LGPD

**Como** titular de dados pessoais ou admin atendendo solicitação, **quero** três ações LGPD, **para** cumprir direito do titular.

- **AC-ACS-012-1**: GIVEN titular logado, WHEN abre "Meus dados (LGPD)", THEN vê 3 botões: "Exportar meus dados", "Solicitar anonimização", "Solicitar exclusão".
- **AC-ACS-012-2**: GIVEN solicitação de exportação, WHEN admin confirma, THEN sistema gera ZIP (JSON + PDFs) em até 15 dias (LGPD art. 19) e disponibiliza por 30 dias.
- **AC-ACS-012-3**: GIVEN anonimização (`ReferenciaPIIAnonimizavel` — ADR-0032), WHEN consumer roda, THEN substitui PII por hash irreversível mantendo integridade contábil/fiscal.
- **AC-ACS-012-4**: GIVEN exclusão solicitada para tenant `perfil ∈ {A, B, C}` com certificado emitido, WHEN sistema avalia, THEN **recusa fundamentada** (ISO 17025 cl. 8.4 obriga retenção ~25 anos — ADR-0067 §retenção). Para perfil D, executa em 5 anos (Receita).
- **AC-ACS-012-5**: GIVEN solicitação LGPD qualquer, WHEN registrada, THEN gera ticket auditável + comprovante PDF.

### US-ACS-013 — Registro de consentimento do titular

**Como** sistema, **quero** registrar consentimento explícito por finalidade, **para** evidenciar base legal LGPD.

- **AC-ACS-013-1**: GIVEN cadastro de cliente com dado pessoal, WHEN salva, THEN apresenta tela de consentimento por finalidade (atendimento, marketing, compartilhamento parceiro X) com toggle individual.
- **AC-ACS-013-2**: Cada consentimento registra: `titular_id`, `finalidade`, `base_legal`, `versao_termo`, `timestamp`, `ip_hash`, `politica_vigente_id`.
- **AC-ACS-013-3**: Titular pode revogar consentimento na tela "Meus dados (LGPD)" — gera evento e ajusta processamentos futuros (ADR-0033 idempotência).
- **AC-ACS-013-4**: Histórico de consentimentos é WORM (padrão B ADR-0031 — `revogado_em` + `motivo_revogacao`).

### US-ACS-014 — RBAC condicional por perfil regulatório do tenant (NOVA — saneamento ADR-0067 2026-05-27)

**Como** admin do tenant, **quero** que o catálogo de papéis funcionais disponíveis seja função do perfil regulatório (A/B/C/D), **para** não conseguir criar `signatario_a3_iso17025` em tenant comercial puro (D) — que viraria fraude documental.

- **AC-ACS-014-1**: GIVEN tenant `perfil_regulatorio="D"`, WHEN admin abre "Criar papel funcional", THEN UI esconde + backend rejeita os papéis bloqueados pela matriz §6 (`rt_signatario`, `conferente_2a`, `gestor_qualidade`, `signatario_a3_iso17025`).
- **AC-ACS-014-2**: GIVEN tentativa via API direta de atribuir papel bloqueado, WHEN endpoint roda, THEN predicate `papel_disponivel_para_perfil(papel, tenant.perfil_regulatorio)` retorna `False` e backend responde 422 com `codigo=PAPEL_INDISPONIVEL_NO_PERFIL`.
- **AC-ACS-014-3**: GIVEN promoção monotônica do tenant (D→C, C→B, B→A — ADR-0067 §matriz operações), WHEN `aplicar_evento_cgcre` consolida, THEN sistema **não cria automaticamente** os papéis novos disponíveis — admin do tenant precisa criar deliberadamente (auditoria CGCRE exige nome do RT no formulário).
- **AC-ACS-014-4**: GIVEN rebaixamento (A→B, B→D, etc.), WHEN `rebaixar_perfil_tenant_voluntario_cliente` ou `aplicar_evento_cgcre(SUSPENSAO)` consolida, THEN sistema desativa os papéis que viraram indisponíveis com `revogado_em=now()` + `motivo_revogacao="rebaixamento_perfil_<X>_para_<Y>"` (padrão B ADR-0031) — usuários atribuídos perdem o papel na próxima ação sensível.
- **INV:** ADR-0067 (matriz feature × perfil), INV-ACS-RBAC-PERFIL-001.

---

## 8. Métricas (inline)

**Primárias:**
- **Adesão MFA em papéis sensíveis: 100%** (mensal) — abaixo de 100% bloqueia login dos faltantes (INV-AUTH-002).
- **Tempo médio de resposta a solicitação LGPD: < 15 dias** (mediana) — limite legal art. 19.
- **Zero incidentes de vazamento cross-tenant ou cross-filial** (acumulado) — métrica binária; um incidente = SEV-1 obrigatório.

**Secundárias:**
- Tentativas de login bloqueadas / total < 5%.
- Tempo médio de login (incluindo MFA) p95 < 2s.

Detalhe em `metricas.md`.

## 9. NFR

- **Performance:** login completo (com MFA) p95 < 2s.
- **Disponibilidade:** SLO 99,9% (login é caminho crítico).
- **Segurança:** SEC-001, SEC-002, SEC-TENANT-001, INV-AUTH-001..005, INV-ACS-FILIAL-SERVER-001.
- **Acessibilidade:** WCAG 2.1 AA na tela de login (Lei Brasileira de Inclusão).

## 10. Glossário

- **Papel funcional** — conjunto de permissões CRUD por módulo/tela/ação. Sinônimo de "perfil de acesso". Distinguir do **perfil regulatório do tenant** (A/B/C/D — ADR-0067), que é propriedade do tenant inteiro.
- **`filial_atual_context`** — ContextVar Python populada pelo middleware a partir de `Session.filial_atual_id`. Único caminho server-side autorizado para resolver filial corrente (INV-ACS-FILIAL-SERVER-001).
- **Lockout** — bloqueio temporário de conta após N tentativas falhadas (INV-AUTH-001).
- **Papel sensível** — papel funcional que exige MFA obrigatório + senha rotacionada 90d + sessão idle 15min: `admin_tenant`, `financeiro`, `metrologista_bancada`, `rt_signatario`, `signatario_a3_iso17025`, `gestor_qualidade`, `dpo` (lista canônica em INV-AUTH-002).

Demais termos em `glossario.md`.

## 11. Matriz feature × perfil

Ver `docs/conformidade/comum/matriz-feature-perfil.md` — linhas de papéis funcionais (gating ADR-0067) acima §6 + linhas de "A3 ICP-Brasil obrigatório", "Snapshot RT competência por grandeza".

## 12. Como este PRD evolui

- US nova → próximo `US-ACS-NNN` livre.
- Mudança em AC já implementado → ADR + novo teste.
- Decisão sobre SSO/biometria/WebAuthn → ADR dedicada (Wave B).
- Mudança na matriz papéis × perfil → editar `matriz-feature-perfil.md` + hook `feature-perfil-matriz-validator.sh` revalida.
