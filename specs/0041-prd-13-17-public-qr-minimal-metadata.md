# 0041 — Página pública do QR com metadados mínimos

## Contexto

O PRD §13.17 exige que a página pública do QR responda para certificado autêntico, reemitido e não localizado, expondo apenas metadados mínimos. O repositório ainda não possui um contrato que materialize esse recorte seguro de dados no portal.

## Escopo

- Adicionar em `apps/portal/src` uma função que monte o modelo da página pública do certificado.
- Expor somente metadados mínimos para certificados autênticos e reemitidos.
- Expor `replacementCertificateNumber` e `reissuedAtUtc` apenas quando o certificado estiver reemitido.
- Garantir que o estado `not_found` não exponha nenhum metadado.
- Validar o comportamento por teste ativo em `evals/ac/prd-13-17-public-qr-minimal-metadata.test.ts`.
- Promover `REQ-PRD-13-17-PUBLIC-QR-MINIMAL-METADATA` para `validated` se a evidência ficar verde.

## Fora de escopo

- Layout visual em Next.js ou SSR real.
- Download de PDF do certificado.
- Exibição pública de resultado metrológico completo, endereço do cliente ou dados pessoais do signatário.

## Critérios de aceite

- A página pública responde com título e metadados mínimos para `authentic`.
- A página pública responde com título e metadados mínimos para `reissued`, incluindo referência ao certificado substituto.
- A página pública responde com `not_found` sem expor qualquer metadado do certificado.
- O teste de aceite falha se a função do portal expuser campos sensíveis como `customerName`, `customerAddress`, `resultSummary`, `expandedUncertainty`, token público ou hash completo.

## Evidência

- `pnpm exec tsx --test apps/portal/src/public-certificate-page.test.ts`
- `pnpm exec tsx --test evals/ac/prd-13-17-public-qr-minimal-metadata.test.ts`
- `pnpm check:all`
