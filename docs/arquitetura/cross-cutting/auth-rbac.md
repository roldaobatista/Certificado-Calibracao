---
owner: Roldão
revisado-em: 2026-05-17
status: draft
---

# Cross-cutting — autenticação + RBAC

> **Pra quê:** quem é quem, e quem pode o quê. Sem isso, multi-tenant vira "todo mundo enxerga tudo".

---

## Stack (ADR-0001)

- **django-allauth** — login social opcional + e-mail/senha
- **django-otp** — MFA (TOTP via Authenticator app)
- **SimpleJWT** — token pra mobile
- **django.contrib.auth** — usuário base

---

## Papéis padrão (RBAC)

Definidos por tenant (cada tenant escolhe quem é o quê):

| Papel | Permissões |
|-------|-----------|
| **Dono do tenant** | Tudo dentro do tenant + admin RBAC interno + ver fatura Aferê |
| **Gerente** | Tudo, exceto financeiro sensível (cobrança, ajuste manual) e admin RBAC |
| **Atendente** | CRM + criar OS + agenda + ver cliente |
| **Técnico de campo** | Suas OS atribuídas + emitir certificado (se for signatário) |
| **Financeiro** | NFS-e + cobrança + comissões + relatórios financeiros |
| **Signatário técnico** | Assinar certificado dentro do escopo declarado |
| **Auditor (read-only)** | Tudo + audit trail (sem editar) |
| **Suporte Aferê** | Acesso temporário via ticket aberto pelo tenant; auditoria reforçada (role `support_user`) |

---

## ABAC parcial

Algumas permissões dependem de atributo:
- Técnico só vê OS atribuídas a ele
- Signatário só assina certificado dentro de competência declarada (`signatario.escopo ⊇ certificado.tipo`)
- Financeiro de Filial 1 só vê dados de Filial 1 (se tenant tiver multi-filial — V2)

---

## MFA obrigatório

Pra papéis sensíveis:
- Dono do tenant
- Gerente
- Financeiro
- Signatário técnico
- Suporte Aferê (sempre)

TOTP via Authenticator (Google/Microsoft/Aegis/Authy). SMS NÃO aceito (SIM swap).

---

## Sessão

| Tipo | Duração |
|------|---------|
| Sessão web | 24h máx; renova com atividade |
| JWT mobile | 7 dias; refresh disponível |
| MFA grace | 12h após auth bem-sucedido |
| Support role | 4h por ticket; auto-revoke |

---

## Auth & API

Endpoints REST:
- `POST /auth/login` — e-mail + senha; retorna JWT
- `POST /auth/mfa/verify` — TOTP; promove sessão pra "authenticated"
- `POST /auth/refresh` — refresh JWT
- `POST /auth/logout` — invalida JWT
- Header `Authorization: Bearer <jwt>` em todas as outras

---

## Multi-tenant injection

Middleware Django:
1. Decodifica JWT → user_id
2. Identifica tenant do user (1 tenant por user no MVP-1; multi-tenant por user em V2)
3. Seta `SET LOCAL app.tenant_id` na transação do request
4. RLS no PG filtra automaticamente

---

## Audit log obrigatório

Eventos em audit trail (`audit_event` + WORM):
- `auth.login.success`
- `auth.login.failed`
- `auth.mfa.success`
- `auth.mfa.failed`
- `auth.logout`
- `rbac.role_changed` (quem mudou, antes/depois)
- `rbac.user_added`
- `rbac.user_removed`
- `support.access_granted` (com ticket ID)
- `support.access_revoked`

---

## Política de senha

- Mínimo 12 caracteres
- Nenhum padrão trivial (não validar contra lista top-1000)
- Lista de senhas vazadas (haveibeenpwned API ou self-hosted) — bloqueia se vazada
- Hash com Argon2id (`django-argon2-py`)

---

## Hooks / verificação

Auditor Segurança em pre-commit:
- Endpoint sem `@login_required` ou `@permission_required` → CONCERN
- Endpoint em `financeiro/`, `auth/`, `tenant/`, `kms/` sem `@mfa_required` → FAIL
- Senha em texto plano em qualquer lugar → FAIL

---

## Referências

- ADR-0001 (stack auth)
- `seguranca-dados.md` §3 (RBAC)
- `lgpd-rat.md` RAT-02
- `isolamento-multi-tenant.md`
