# Finding — Hash do certificado calculado sobre campos lógicos, não sobre artefato canônico

## Status

Aberto.

## Contexto

Na emissão (`signature-queue.ts` e domínio relacionado), o `documentHash` é derivado de `workOrderNumber`, cliente, equipamento, número de certificado, resultado e incerteza. Isso cria uma hash de *payload selecionado*, não do *documento final*.

Para certificado regulado, o hash deveria ser computado sobre o artefato canônico final (PDF/A ou envelope DCC), incluindo seus bytes, metadados e assinatura. Caso contrário, não há prova criptográfica de que o documento publicado é exatamente aquele que foi aprovado.

## Impacto

- Não repúdio fraco: um PDF adulterado pode manter a mesma "hash lógica" se os campos de input não mudarem.
- Dificuldade em auditorias formais que exigem integridade do artefato.
- Incompatibilidade futura com DCC (Digital Calibration Certificate), onde o envelope assinado é a prova.

## Correção recomendada

1. Gerar o documento canônico (PDF/A) antes da assinatura.
2. Persistir o artefato em storage com content-address (hash SHA-256 dos bytes).
3. Registrar no `CertificatePublication` o `contentHash`, `storageKey`, `sizeBytes` e `mimeType`.
4. A hash-chain de auditoria deve referenciar o `contentHash`, não uma hash derivada de campos.
5. Validar PDF/A externamente antes de publicação.
6. Assinar o hash do artefato com KMS real.

## Rastreamento

- Área crítica: `apps/api/src/domain/emission/`, `packages/db/prisma/schema.prisma` (CertificatePublication)
- Requisito PRD: §13.05 (QR público/autenticidade), §13.16 (reemissão controlada)
- Gate 7: snapshots de certificado determinístico
