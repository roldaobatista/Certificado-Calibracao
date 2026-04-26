# Finding — Gaps de segurança em sessão, redirect e rate-limit

## Status

Mitigado em 2026-04-26. Cookie Secure/Strict, redirect allowlist e rate-limit implementados; testes verdes.

## Contexto

Inspeção estática de `apps/api/src/domain/auth/session-auth.ts` e rotas HTTP de auth/onboarding revela múltiplos gaps de segurança:

1. **Cookie `afere_session` sem flag `Secure`**: a serialização visível define `HttpOnly` e `SameSite=Lax`, mas não adiciona `Secure`. Em produção HTTPS, isso expõe o cookie a interceptação em rede não segura.

2. **Open redirect em `auth/login`, `auth/logout`, `onboarding/bootstrap` e rotas de review/signature**: os endpoints aceitam `redirectTo` e chamam `reply.redirect(redirectTo)` sem allowlist visível de domínios ou rotas internas.

3. **Ausência de rate-limit / anti-bruteforce**: não há plugin de rate-limit visível no Fastify para login público, verificação pública de certificado ou endpoints sensíveis. O `package.json` da API não lista `@fastify/rate-limit` ou equivalente.

## Impacto

- Hijack de sessão por cookie não-Secure em rede comprometida.
- Phishing / open redirect explorável para domínios externos.
- Brute-force de credenciais e enumeração de contas/tokens sem throttle.

## Correção recomendada

1. `Secure` obrigatório quando `NODE_ENV=production`; `SameSite=Strict` para endpoints sensíveis.
2. Rotação de sessão em login; expiração curta com renovação controlada; invalidação por device.
3. Allowlist rigorosa para `redirectTo` (rotas internas prefixadas ou domínios explicitamente configurados).
4. Rate-limit por IP, tenant e conta em login, verificação pública e APIs sensíveis.
5. CSRF para POSTs autenticados com cookie.
6. Logs de auth estruturados sem vazar PII indevida.

## Rastreamento

- Área crítica: `apps/api/src/domain/auth/session-auth.ts`, `apps/api/src/interfaces/http/auth-session.ts`, `apps/api/src/interfaces/http/onboarding.ts`, `apps/api/src/interfaces/http/emission-workspace.ts`, `apps/api/src/app.ts`
- Requisito PRD: §13.11 (auth SSO/MFA), §13.04 (assinatura técnica auditável)
