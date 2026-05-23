---
adr: 0038
titulo: Família INV-AUTH-* — invariantes de autenticação (lockout, política de senha, sessão, troca forçada, retenção tentativas)
status: proposto
data: 2026-05-23
proposto-por: agente (Onda 3 saneamento F-B pré-Marco 3 OS — Auditor 2 achado F-B-A4)
revisado-por: tech-lead-saas-regulado + advogado-saas-regulado + auditor-conformidade-lgpd
revisado-em: 2026-05-23
bloqueia-fase: Wave A (Marco 3 OS + Marco 4 Calibração — perfis sensíveis financeiro/metrologista/signatário entram em produção)
depende-de: ADR-0012 (autorização unificada), ADR-0002 (multi-tenancy)
owner: tech-lead-saas-regulado
---

# ADR-0038 — Família INV-AUTH-* (autenticação canônica)

## Contexto

Foundation F-B fechou (2026-05-19) com `auth_usuario` + MFA (django-otp real) + `auth_usuario_perfil` (M:N) + middleware `app.tenant_ids`. Mas **a invariante INV-AUTHZ-* só cobre autorização** (decidir se pode). **Autenticação** (provar identidade + manter sessão segura) ficou implícita em código sem ID rastreável:

1. **Login bruteforce** — Auditor 2 (Onda 3) detectou: `LoginView` aceita N tentativas sem lockout. Atacante com lista de e-mails de tenants conhecidos pode rodar credential-stuffing infinito.
2. **Política de senha fraca** — `password_validators` Django default (8 chars). Tenants sensíveis (laboratório ISO 17025, financeiro) precisam padrão NIST SP 800-63B + reuso histórico bloqueado.
3. **Sessão eterna** — sem `SESSION_COOKIE_AGE` customizado por perfil; signatário ISO 17025 esquecer laptop aberto vira NC ANPD/CGCRE.
4. **Troca forçada de senha** — perfis sensíveis (financeiro, signatario, metrologista_bancada) não rotacionam. Auditoria 21 CFR Part 11 (cliente farma) reprova.
5. **Tentativas de login retidas indefinidamente** — `LoginFalha` evento canônico v10 (cat. integrações) cresce sem expurgo. LGPD art. 16 (eliminação fim-de-finalidade) é violado em 1 ano.

INV-AUTHZ-002 (audit síncrono de **autorização**) **não cobre** os eventos de autenticação acima — INV-AUTH-* preenche essa lacuna na camada anterior (provar identidade).

## Decisão

Criar 5 invariantes canônicas `INV-AUTH-001..005` em `REGRAS-INEGOCIAVEIS.md` (seção própria após INV-AUTHZ-*), com hooks validadores e testes E2E em Wave A.

### INV-AUTH-001 — Lockout anti-bruteforce
- Após **5 tentativas falhadas em janela de 15min** (mesmo `email` OU mesmo `ip_hash`), conta entra em estado `bloqueado` por **30min**.
- Bloqueio emite `AcessoSeguranca.LoginBloqueado` (catálogo v10) com `motivo: "tentativas_excedidas"`.
- Desbloqueio: automático após 30min OU manual por `admin_tenant` (registra `AcessoSeguranca.RegistroAlterado`).
- **Não vaza informação:** mesma mensagem de erro pra "usuário não existe" / "senha errada" / "conta bloqueada" — apenas log audit registra a distinção.

### INV-AUTH-002 — Política de senha
- **Mínimo 12 caracteres** + exigir **3 das 4 categorias** (maiúscula, minúscula, dígito, símbolo).
- **Histórico de 5 senhas** (`auth_senha_historico` — hash bcrypt, retenção atrelada a vida do usuário + 90d pós-desativação).
- **Expiração 180 dias** apenas para **perfis sensíveis** (lista canônica em `politica-senha-sessao.md`): `financeiro`, `signatario`, `metrologista_bancada`, `admin_tenant`, `gerente_operacional`. Perfis não-sensíveis sem expiração (alinhado NIST SP 800-63B rev.4 — expiração compulsória prejudica segurança).
- Vetada senha igual a `email`, `nome`, `cpf`, `cnpj_tenant` (verificação canonicalizada — case-insensitive, sem acentos).

### INV-AUTH-003 — Sessão idle + máximo
- **Idle timeout: 30min** (sem requisição autenticada) → sessão expira, emite `AcessoSeguranca.SessaoEncerrada` com `motivo: "idle_timeout"`.
- **Máximo absoluto: 8h** independentemente de atividade → re-login obrigatório.
- Perfis sensíveis: idle reduz pra **15min**, máximo **4h**.
- Refresh token (caso adotado em Wave A app-tecnico Flutter): rotação a cada uso + janela 7d.

### INV-AUTH-004 — Troca forçada de senha (perfis sensíveis)
- Perfis da lista canônica (ver INV-AUTH-002) trocam senha a cada **90 dias**.
- 7 dias antes: banner + e-mail; no D-0: bloqueia operação até trocar.
- Histórico (INV-AUTH-002 §3) impede reuso das últimas 5.

### INV-AUTH-005 — Retenção tentativas-login
- `auth_login_tentativa` (tabela detalhada por evento) retém **365 dias**.
- Após 365d: agregação diária por (`tenant_id`, `dia`, `sucesso`, `motivo_falha`) em `auth_login_tentativa_agregado` — perde `ip_hash` + `email` (PII), mantém contagem.
- WORM B2 mantém eventos canônicos (INV-AUTHZ-002 cobre).

## Mapeamento eventos canônicos v10

Esta ADR **consome** (não cria) eventos já catalogados em `docs/comum/integracoes-inter-modulos.md`:

- `AcessoSeguranca.LoginSucesso` / `LoginFalha` / `LoginBloqueado` (INV-AUTH-001)
- `AcessoSeguranca.SessaoEncerrada` (INV-AUTH-003)
- `AcessoSeguranca.RegistroAlterado` (INV-AUTH-001 desbloqueio manual + INV-AUTH-002 troca senha)
- `AcessoSeguranca.UsuarioCriado` / `UsuarioDesativado` (INV-AUTH-005 expurgo)

Declaração formal de payload + consumidores em `docs/dominios/suporte-plataforma/modulos/acesso-seguranca/eventos.md`.

## Non-goals

- **MFA enrollment forçado** — fica em INV-AUTHZ-* / ADR-0012 (ortogonal: MFA é "prova segundo fator", não política de senha).
- **Biometria** — coberta por INV-OS-ACEITE-BIO-001 (Onda 4 saneamento), não autenticação genérica.
- **WebAuthn / passkey** — diferido pós-Wave A (proposta em V2 backlog).
- **SSO (SAML/OIDC)** — porta `AuthorizationProvider` (ADR-0012) prevê adapter; INV-AUTH-* não rege sessão delegada a IdP externo.

## Consequências

- **Migration Wave A:** `auth_senha_historico` (5 últimas), `auth_login_tentativa` (eventos detalhados 365d), `auth_login_tentativa_agregado` (pós-expurgo).
- **Hook validador Wave A:** `auth-policy-check.sh` valida que `LoginView`/`PasswordChangeView` chamam `verificar_lockout()` + `validar_politica_senha()` antes de gravar.
- **3 testes E2E Wave A:** `test_inv_auth_001_lockout`, `test_inv_auth_002_politica_senha`, `test_inv_auth_003_sessao_idle`.
- **Atualização `politica-senha-sessao.md`** — single-source dos parâmetros (5/15/30 lockout, 12 chars, 180d, 30min idle, 8h máximo).

## Status

🟡 **Proposto** — aceitação depende de:
1. Roldão validar parâmetros (5 tentativas? 12 chars? 30min idle?) — Wave A kick-off.
2. `tech-lead-saas-regulado` revisar implementação django-axes (lib candidata pra INV-AUTH-001) vs build-in.
3. `advogado-saas-regulado` validar retenção 365d × LGPD finalidade.

Quando aceito: REGRAS-INEGOCIAVEIS.md ganha as 5 linhas + bloqueia Wave A perfis sensíveis.
