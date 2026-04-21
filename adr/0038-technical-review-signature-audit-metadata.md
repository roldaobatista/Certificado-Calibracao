# ADR 0038 — Metadados canônicos para revisão técnica e assinatura

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0035-prd-13-04-technical-review-signature-audit.md`, `PRD.md` §13.4 e §7.10

## Contexto

O requisito do PRD não pede apenas que revisão técnica e assinatura existam na trilha, mas que carreguem identidade, timestamp e dispositivo de forma auditável. Após a entrada da cobertura mínima de eventos críticos no `@afere/audit-log`, falta uma verificação semântica específica para os eventos de revisão e assinatura.

## Decisão

1. `@afere/audit-log` passa a exportar `verifyTechnicalReviewSignatureAudit()`.
2. A função exige a presença dos eventos `technical_review.completed` e `certificate.signed`.
3. Cada ocorrência desses eventos deve conter:
   - `actorId` como string não vazia;
   - `deviceId` como string não vazia;
   - `timestampUtc` como string UTC ISO-8601 com sufixo `Z`.
4. A decisão é fail-closed: hash-chain inválida, evento ausente ou metadado ausente/inválido torna a verificação inválida.

## Consequências

- O PRD §13.4 passa a ter evidência executável específica sobre autoria e rastreabilidade mínima de revisão/assinatura.
- `apps/api` ganha um contrato futuro objetivo para validar metadados antes de emitir evidência ou liberar assinatura.
- O shape mínimo (`actorId`, `timestampUtc`, `deviceId`) fica estável e reutilizável em outras validações regulatórias.

## Limitações honestas

- A ADR não prova autenticidade criptográfica nem conformidade jurídica da assinatura eletrônica.
- A validação ainda opera sobre entradas já materializadas da hash-chain, não sobre persistência real do backend.
- Competência do signatário, MFA e dupla aprovação continuam cobertos por requisitos separados.
