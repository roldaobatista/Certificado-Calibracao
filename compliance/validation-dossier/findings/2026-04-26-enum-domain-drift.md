# Finding — Estados e papéis armazenados como String livre no banco

## Status

Aberto.

## Contexto

O schema Prisma usa `String` e `String[]` para campos que deveriam ser enums ou tabelas de domínio:

- `AppUser.roles` → `String[]`
- `AppUser.status` → `String`
- `ServiceOrder.workflowStatus` → `String`
- `ServiceOrder.reviewDecision` → `String`

Embora os contracts valide valores na borda, o banco permite drift se alguém escrever via migration, script de importação ou acesso direto.

## Impacto

- Inconsistência de dados que passa despercebida até causar falha em runtime.
- Dificuldade para manter integridade referencial e evolução de domínio.
- Queries por índice menos eficientes sem enums/tipos nativos.

## Correção recomendada

1. Usar `enum` do Prisma/Postgres para campos com cardinalidade fechada (status, workflowStatus, reviewDecision).
2. Usar tabela de domínio `Role` ou `UserRole` para papéis, especialmente se houver necessidade de metadata por papel.
3. Manter contracts como validação de borda, mas adicionar constraints de banco como segunda linha de defesa.

## Rastreamento

- Área: `packages/db/prisma/schema.prisma`
- Requisito PRD: §13.11 (RBAC)
