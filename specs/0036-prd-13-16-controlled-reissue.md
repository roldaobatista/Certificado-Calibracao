# 0036 — Evidência executável para reemissão controlada

## Contexto

O PRD §13.16 exige que a reemissão de certificado seja controlada por dupla aprovação, versionamento `R1/R2`, preservação do hash anterior e notificação automática ao cliente. O roadmap V4 reforça que o novo certificado deve referenciar o anterior e manter a hash-chain verificável.

O repositório já tem hash-chain verificável em `@afere/audit-log`, mas ainda não existe uma regra executável que prove, em uma trilha de reemissão, a presença dessa sequência mínima de evidências.

## Escopo

- Adicionar em `packages/audit-log` uma API que valide a trilha mínima de reemissão controlada.
- Exigir pelo menos dois eventos `certificate.reissue.approved` com aprovadores distintos antes do evento `certificate.reissued`.
- Exigir que `certificate.reissued` carregue `previousCertificateHash`, `previousRevision` e `newRevision`, com salto sequencial de revisão.
- Exigir um evento `certificate.reissue.notified` após a reemissão, com destinatário e timestamp.
- Falhar fechado quando a hash-chain estiver inválida, quando faltar aprovação suficiente, quando o hash anterior não estiver preservado, quando o versionamento for inválido ou quando a notificação ao cliente não estiver registrada.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-16-controlled-reissue.test.ts`.
- Promover `REQ-PRD-13-16-CONTROLLED-REISSUE` para `validated` se a evidência ficar verde.

## Fora de escopo

- Integrar a regra com `apps/api/src/domain/reissue/**` ou disparo real de e-mail/SMS.
- Modelar RBAC, competência ou MFA dos aprovadores.
- Cobrir QR público e renderização do certificado reemitido.

## Critérios de aceite

- A API aceita a trilha quando existem duas aprovações distintas antes da reemissão, o hash anterior é preservado, a revisão avança sequencialmente e a notificação ocorre depois da reemissão.
- A API falha fechado quando há menos de dois aprovadores distintos.
- A API falha fechado quando `previousCertificateHash` não é um SHA-256 hexadecimal ou quando `newRevision` não sucede `previousRevision`.
- A API falha fechado quando a notificação ao cliente está ausente ou registrada antes da reemissão.
- O teste de aceite falha se a API não for exportada por `packages/audit-log/src/index.ts`.

## Evidência

- `pnpm exec tsx --test packages/audit-log/src/controlled-reissue.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-16-controlled-reissue.test.ts`
- `pnpm check:all`
