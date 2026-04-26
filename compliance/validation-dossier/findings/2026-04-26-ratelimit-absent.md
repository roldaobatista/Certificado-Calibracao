# Finding — Rate-limit e proteção anti-bruteforce ausentes

## Status

Aberto.

## Contexto

O `package.json` da API não lista plugin de rate-limit. Login público, verificação pública de certificado e endpoints de onboarding estão expostos sem throttle por IP, tenant, conta ou token.

## Impacto

- Brute-force de senhas.
- Enumeração de e-mails/tokens/certificados.
- DoS por exaustão de recursos em endpoints pesados.

## Correção recomendada

1. Adicionar `@fastify/rate-limit` (ou equivalente) com store Redis.
2. Configurar limites diferenciados: login (5/min por IP, 3/min por conta), verificação pública (20/min por IP), onboarding (3/min por IP).
3. Integrar com observabilidade para alertar de padrões de ataque.

## Rastreamento

- Área: `apps/api/src/app.ts`, `apps/api/package.json`
