# 0035 — Metadados obrigatórios de revisão técnica e assinatura

## Contexto

O PRD §13.4 exige que a revisão técnica e a assinatura do certificado registrem identidade, timestamp e dispositivo. O PRD §7.10 já exige trilha append-only com hash-chain exportável, mas o repositório ainda não tem uma regra executável que valide esses metadados nos eventos `technical_review.completed` e `certificate.signed`.

## Escopo

- Adicionar em `packages/audit-log` uma API que valide metadados mínimos de revisão técnica e assinatura sobre uma hash-chain já encadeada.
- Exigir que os eventos `technical_review.completed` e `certificate.signed` existam e carreguem `actorId`, `timestampUtc` e `deviceId`.
- Exigir `timestampUtc` em formato UTC ISO-8601 com sufixo `Z`.
- Falhar fechado quando a hash-chain estiver inválida, quando algum evento obrigatório estiver ausente ou quando os metadados estiverem incompletos/inválidos.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-04-technical-review-signature-audit.test.ts`.
- Promover `REQ-PRD-13-04-TECHNICAL-REVIEW-SIGNATURE-AUDIT` para `validated` se a evidência ficar verde.

## Fora de escopo

- Modelar assinatura eletrônica jurídica, MFA, competência do signatário ou RBAC.
- Cobrir emissão, reemissão, QR público ou payload completo do certificado.
- Integrar a validação diretamente com `apps/api/src/domain/emission/**`.

## Critérios de aceite

- A API aceita a trilha quando revisão técnica e assinatura estão presentes com `actorId`, `timestampUtc` e `deviceId` válidos.
- A API falha fechado quando algum dos eventos obrigatórios estiver ausente.
- A API falha fechado quando algum dos eventos obrigatórios tiver metadado ausente ou `timestampUtc` fora do formato UTC esperado.
- O teste de aceite falha se a API não for exportada por `packages/audit-log/src/index.ts`.

## Evidência

- `pnpm exec tsx --test packages/audit-log/src/review-signature-audit.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-04-technical-review-signature-audit.test.ts`
- `pnpm check:all`
