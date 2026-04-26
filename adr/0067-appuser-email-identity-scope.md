# ADR 0067: AppUser.email — Global Unique vs Tenant-Scoped

## Status
Proposed → **Accepted**

## Context
O modelo `AppUser` atual define `email @unique` global no Prisma schema. Isso significa que o mesmo endereço de e-mail não pode ser usado em duas organizações diferentes. A auditoria estática levantou a questão: essa restrição global é desejável ou deveria ser relaxada para `@@unique([organizationId, email])`?

## Decisão
**Opção A — Manter `email @unique` global** e evoluir para um modelo de `Identity` global + `OrganizationMembership` se multi-organização por usuário for necessária no futuro.

## Consequências

### Positivas
- **Simplicidade imediata**: não exige remodelagem de autenticação, sessão, reset de senha e onboarding.
- **Prevenção de conflito de identidade**: um endereço de e-mail representa uma pessoa física/jurídica única no domínio metrológico; risco baixo de colisão legítima entre tenants.
- **Compatibilidade com LGPD**: um e-mail vinculado a múltiplos tenants aumenta a superfície de dados pessoais compartilhados; isolamento por e-mail facilita a gestão de consentimento e exclusão.
- **Facilita single sign-on futuro**: se o usuário precisar acessar múltiplos laboratórios, o modelo de `Identity` + `Membership` é mais adequado do que duplicar o mesmo e-mail em tenants diferentes.

### Negativas
- **Restrição de multi-tenant por usuário**: um metrologista que trabalhe em dois laboratórios precisará de dois e-mails distintos (ou aguardar a evolução para `Identity` + `Membership`).
- **Risco de enumeração**: um atacante pode testar e-mails e inferir existência de conta (mitigado por rate limiting e timing-safe responses).

## Alternativa Rejeitada
**Opção B — `@@unique([organizationId, email])`**
- Permite o mesmo e-mail em múltiplos tenants imediatamente.
- Porém, quebra a semântica de "uma pessoa, uma identidade" e complica futura consolidação de contas.
- Aumenta a complexidade de autenticação (login precisaria de `organizationId` ou slug implícito).

## Próximos Passos
1. Se o requisito de multi-organização por usuário emergir, criar tabela `identities` (global) e migrar `AppUser` para `OrganizationMembership`.
2. Manter monitoramento de conflitos de e-mail no onboarding via `hasAnyOrganization` e mensagens de erro apropriadas.

## Referências
- `packages/db/prisma/schema.prisma` — modelo `AppUser`
- `harness/05-guardrails.md` — regras de multitenancy
