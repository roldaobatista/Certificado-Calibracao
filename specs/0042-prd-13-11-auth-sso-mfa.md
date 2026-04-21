# 0042 — Auto-cadastro com provedores obrigatórios e MFA por papel

## Contexto

O PRD §13.11 exige auto-cadastro com e-mail/senha e SSO Google, Microsoft e Apple, além de MFA obrigatório para signatários e administradores. O repositório ainda não possui um contrato executável que bloqueie onboarding/autocadastro quando algum provedor obrigatório estiver ausente ou quando um papel privilegiado não tiver MFA.

## Escopo

- Adicionar em `apps/api/src/domain/auth` uma política executável para auto-cadastro.
- Exigir os quatro métodos de entrada: `email_password`, `google`, `microsoft` e `apple`.
- Exigir pelo menos um fator MFA para papéis `admin` e `signatory`.
- Materializar em `apps/web/src/auth` um view model que mostre métodos disponíveis, métodos faltantes e a etapa de MFA quando aplicável.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-11-auth-sso-mfa.test.ts`.
- Promover `REQ-PRD-13-11-AUTH-SSO-MFA` para `validated` se a evidência ficar verde.

## Fora de escopo

- Integração real com Google, Microsoft ou Apple.
- Provisionamento real de TOTP, WebAuthn, SMS ou recovery codes.
- RBAC completo e sessão JWT do backend.

## Critérios de aceite

- A política aceita auto-cadastro quando os quatro provedores estão habilitados.
- A política falha fechado quando faltar qualquer provedor obrigatório.
- A política falha fechado quando `admin` ou `signatory` não possuem MFA.
- O view model do back-office deixa explícito quando o fluxo está pronto e quando faltam provedores obrigatórios.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/auth/self-signup-policy.test.ts`
- `pnpm exec tsx --test apps/web/src/auth/self-signup-checklist.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-11-auth-sso-mfa.test.ts`
- `pnpm check:all`
