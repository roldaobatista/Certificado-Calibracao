# Finding — Contexto tRPC sem sessão, tenant ou papéis

## Status

Aberto.

## Contexto

`apps/api/src/plugins/trpc.ts` cria contexto com `requestId` apenas. Não há extração de sessão, organização ou papéis no contexto tRPC. Se qualquer procedure sensível for adicionada, não há guarda automática no nível do router.

## Impacto

- Vetor de bypass se procedures sensíveis forem expostas via tRPC sem replicar guards HTTP.
- Duplicação de lógica de auth entre camada HTTP e camada tRPC.

## Correção recomendada

1. Enriquecer o contexto tRPC com sessão (cookie), `organizationId` e `roles`.
2. Criar middleware de procedura `authed`/`tenantAdmin`/`signatory` que bloqueia antes do handler.
3. Proibir procedures públicas em routers de domínio sensível.

## Rastreamento

- Área: `apps/api/src/plugins/trpc.ts`
