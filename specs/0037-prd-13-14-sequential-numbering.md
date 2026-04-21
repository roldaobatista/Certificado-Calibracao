# 0037 — Numeração sequencial isolada por organização

## Contexto

O PRD §13.14 exige que a numeração de certificados seja sequencial por organização e sem colisão entre tenants. O repositório ainda não possui um contrato executável que reserve o próximo número de certificado com isolamento de tenant e fail-closed para colisões ou inconsistências.

## Escopo

- Adicionar em `packages/db` uma API que reserve o próximo número de certificado por organização.
- Exigir sequência monotônica por organização, com prefixo estável por tenant.
- Bloquear colisões quando um número já existir para outro tenant ou quando o histórico estiver inconsistente.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-14-sequential-numbering.test.ts`.
- Promover `REQ-PRD-13-14-SEQUENTIAL-NUMBERING` para `validated` se a evidência ficar verde.

## Fora de escopo

- Persistência real em Postgres/Prisma.
- Locks distribuídos e transação do backend real.
- Regras de formatação visual de PDF ou QR.

## Critérios de aceite

- A API reserva o próximo número sequencial para a mesma organização.
- Duas organizações podem emitir a mesma sequência ordinal sem colisão porque o número público fica isolado por prefixo de tenant.
- A API falha fechado quando o histórico contém colisão ou prefixo inconsistente para a mesma organização.
- O teste de aceite falha se a API não for exportada por `packages/db/src/index.ts`.

## Evidência

- `pnpm exec tsx --test packages/db/src/certificate-numbering.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-14-sequential-numbering.test.ts`
- `pnpm check:all`
