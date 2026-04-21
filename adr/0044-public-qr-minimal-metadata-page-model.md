# ADR 0044 — Página pública do QR expõe apenas metadados mínimos

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0041-prd-13-17-public-qr-minimal-metadata.md`, `PRD.md` §13.17

## Contexto

A página pública do QR deve responder para três estados regulatórios (`authentic`, `reissued`, `not_found`) sem vazar dados pessoais, resultado metrológico completo ou segredos de verificação. Como o portal ainda não existe, a melhor evidência imediata é um modelo puro de página que imponha esse whitelist.

## Decisão

1. `apps/portal/src/public-certificate-page.ts` passa a exportar `buildPublicCertificatePageModel()`.
2. O estado `authentic` expõe apenas `certificateNumber`, `issuedAtUtc`, `revision`, `instrumentDescription` e `serialNumber`.
3. O estado `reissued` reutiliza a whitelist base e adiciona apenas `reissuedAtUtc` e `replacementCertificateNumber`.
4. O estado `not_found` não expõe metadados.
5. Campos como nome/endereço do cliente, resultado, incerteza, token público, hash completo ou identidade do signatário ficam proibidos por construção.

## Consequências

- O PRD §13.17 ganha uma evidência executável de minimização de dados antes do portal real.
- O frontend futuro pode consumir o mesmo modelo como camada anti-vazamento.
- A distinção entre estados regulatórios fica explícita e testável.

## Limitações honestas

- A ADR não cobre layout, i18n, acessibilidade visual ou deploy do portal.
- O contrato depende de um resultado de verificação já resolvido pelo backend/domínio.
- Ainda não há integração com LGPD notices, rate limiting ou cache público.
