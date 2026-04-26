# Finding — E-mail globalmente único em AppUser impede identidade multitenant

## Status

Aberto.

## Contexto

`AppUser.email` tem índice `@unique`. Em SaaS multitenant, isso impede que o mesmo e-mail pertença a usuários de organizações diferentes. Se a intenção é identidade global, o modelo não explicita isso (não há `Identity` separada nem `Membership` com `organizationId + email`).

## Impacto

- Impossibilidade de um usuário pertencer a múltiplos tenants (ex: consultor externo, auditor compartilhado).
- Conflito de cadastro se organizações diferentes tentarem convidar o mesmo e-mail.
- Dificuldade para migrar para modelo de identidade federada no futuro.

## Correção recomendada

1. Se identidade for global: criar tabela `Identity` (email único) e `Membership` (`identityId + organizationId`, unique composite).
2. Se identidade for por tenant: mudar índice para `@@unique([organizationId, email])` e remover `@unique` de `email`.
3. Atualizar login para resolver identidade corretamente no modelo escolhido.

## Rastreamento

- Área: `packages/db/prisma/schema.prisma`
- Requisito PRD: §13.11 (auth)
