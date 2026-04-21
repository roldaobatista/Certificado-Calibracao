# 0040 — Autenticidade pública do QR do certificado

## Contexto

O PRD §13.5 exige que o QR code impresso no certificado permita validação pública de autenticidade. O repositório ainda não possui um contrato executável que valide o payload do QR contra um certificado publicado e contra a trilha imutável de emissão.

## Escopo

- Adicionar em `apps/api/src/domain/certificates` uma API que valide o QR público do certificado.
- Exigir URL HTTPS apontando para o host público esperado.
- Exigir correspondência entre `certificateId`, token público e certificado publicado.
- Exigir evidência de `certificate.emitted` na hash-chain imutável do certificado.
- Falhar fechado quando o QR estiver malformado, o token não corresponder, o certificado não existir ou a trilha de auditoria estiver adulterada.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-05-public-qr-authenticity.test.ts`.
- Promover `REQ-PRD-13-05-PUBLIC-QR-AUTHENTICITY` para `validated` se a evidência ficar verde.

## Fora de escopo

- Geração real de imagem QR no PDF.
- Endpoint HTTP público ou deploy do portal.
- Revogação pública, rate limiting ou analytics de consulta.

## Critérios de aceite

- A API aceita o QR quando `certificateId` e token batem com um certificado publicado e existe evento `certificate.emitted` na hash-chain íntegra.
- A API classifica o certificado como `reissued` quando houver evidência mínima de reemissão controlada.
- A API falha fechado com `not_found` quando a URL é inválida, o token não confere, o certificado não existe ou a trilha foi adulterada.
- O teste de aceite falha se a API não existir em `apps/api/src/domain/certificates/public-qr.ts`.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/certificates/public-qr.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-05-public-qr-authenticity.test.ts`
- `pnpm check:all`
