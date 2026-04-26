# Finding — Audit events sem sequência monotônica e âncora de cadeia

## Status

Aberto.

## Contexto

`EmissionAuditEvent` tem `prevHash` e `hash`, mas não há campo de sequência (`sequenceNumber`, `eventIndex` ou similar) por ordem/certificado. A ordenação depende de `createdAt` (timestamp), que pode ser frágil sob:

- Concorrência de emissão simultânea
- Clock skew
- Eventos no mesmo instante
- Replay de eventos

## Impacto

- Dificuldade para detectar deleção ou inserção de evento fora de ordem.
- Verificação de hash-chain depende de ordenação implícita, não explícita.
- Possível inconsistência na reconstrução da cadeia em auditoria externa.

## Correção recomendada

1. Adicionar `sequence Int` (ou `BigInt`) em `EmissionAuditEvent`, incrementado por `organizationId` + `serviceOrderId` (ou escopo equivalente).
2. Usar sequence como parte da canonicalização do payload de hash (`prevHash + sequence + ...`).
3. Criar âncora de cadeia (primeiro evento com `prevHash = null` e `sequence = 1`).
4. Testar integridade da cadeia sob concorrência simulada.

## Rastreamento

- Área: `packages/db/prisma/schema.prisma`, `packages/audit-log/`
- Requisito PRD: §13.06 (trilha crítica de auditoria)
