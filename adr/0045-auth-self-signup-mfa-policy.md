# ADR 0045 — Auto-cadastro exige quatro provedores e MFA por papel privilegiado

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0042-prd-13-11-auth-sso-mfa.md`, `PRD.md` §13.11

## Contexto

O requisito de auth ainda não pode ser validado por integrações reais com IdPs. A evidência executável mais segura neste estágio é uma política de domínio que valide a matriz mínima de provedores e a obrigatoriedade de MFA por papel.

## Decisão

1. `apps/api/src/domain/auth/self-signup-policy.ts` passa a exportar `evaluateSelfSignupPolicy()`.
2. A política exige os provedores `email_password`, `google`, `microsoft` e `apple`.
3. Os papéis `admin` e `signatory` exigem ao menos um fator MFA enrolado.
4. `apps/web/src/auth/self-signup-checklist.ts` materializa um view model que explicita métodos disponíveis, métodos faltantes e a etapa de MFA.
5. A decisão é fail-closed: provedor ausente ou MFA ausente para papel privilegiado bloqueiam o fluxo.

## Consequências

- O PRD §13.11 ganha evidência executável antes das integrações reais de identidade.
- O back-office passa a ter um modelo explícito para renderizar bloqueios do fluxo de cadastro.
- O backend futuro pode reutilizar a mesma política como pré-condição da criação de conta.

## Limitações honestas

- Não há integração real com OAuth/OIDC, TOTP ou WebAuthn.
- A ADR não cobre sessão, recuperação de conta, antifraude ou política de senha.
- Os papéis e fatores ainda são avaliados sobre payloads já resolvidos, não sobre estado persistido.
