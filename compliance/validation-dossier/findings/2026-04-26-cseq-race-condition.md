# Finding — Numeração sequencial de certificado vulnerável a corrida

## Status

Aberto, parcialmente mitigado por `reserveSequentialCertificateNumber()`.

## Contexto

O fluxo de assinatura carrega `records`, calcula o próximo número e emite. O Prisma `reserveSequentialCertificateNumber()` usa transação, mas a inspeção estática não confirma uso de `SELECT ... FOR UPDATE`, advisory lock ou sequence nativa do Postgres por organização. Duas emissões concorrentes podem competir pelo mesmo número.

## Impacto

- Colisão de número de certificado, violando unicidade regulatória.
- Retry em cascata ou falha de transação visível ao usuário.

## Correção recomendada

1. Usar `pg_advisory_lock` por `organizationId` ou sequence nativa `CREATE SEQUENCE org_<id>_cert_seq`.
2. Ou `SELECT ... FOR UPDATE` em tabela de controle de numeração dentro da transação de emissão.
3. Retry controlado com backoff e evento auditável de reserva/falha.

## Rastreamento

- Área: `packages/db/src/`, `apps/api/src/domain/emission/signature-queue.ts`
- Requisito PRD: §13.14 (numeração sequencial)
- AC: `prd-13-14-sequential-numbering.test.ts`
