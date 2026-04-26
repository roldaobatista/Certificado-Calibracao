# Finding — Ausência de model `Certificate` e `CertificateStatus`

## Status

Aberto.

## Contexto

O domínio de certificado é tratado indiretamente via `ServiceOrder` + `CertificatePublication`. Não há entidade `Certificate` com seu próprio ciclo de vida, status jurídico/técnico e metadados.

## Impacto

- Dificuldade para modelar revisão, reemissão, substituição e expiração como estados do certificado.
- Acoplamento entre ordem de serviço (operacional) e certificado (regulatório/jurídico).

## Correção recomendada

1. Criar model `Certificate` vinculado a `ServiceOrder`.
2. Definir `enum CertificateStatus` (draft, emitted, reissued, superseded, revoked).
3. Migrar `CertificatePublication` para referenciar `Certificate` em vez de `ServiceOrder` diretamente.
4. Manter rastreabilidade: `Certificate.serviceOrderId` + `Certificate.publicationId`.

## Rastreamento

- Área: `packages/db/prisma/schema.prisma`
