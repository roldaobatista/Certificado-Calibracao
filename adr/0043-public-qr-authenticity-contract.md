# ADR 0043 — QR público validado contra certificado publicado e hash-chain

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0040-prd-13-05-public-qr-authenticity.md`, `PRD.md` §13.5

## Contexto

O QR público precisa confirmar autenticidade sem depender de UI real. A evidência mais útil neste estágio é uma função de domínio que valide a URL pública, o token do certificado e a presença de emissão/reemissão na trilha imutável.

## Decisão

1. `apps/api/src/domain/certificates/public-qr.ts` passa a exportar `verifyPublicCertificateQrAuthenticity()`.
2. A função exige URL HTTPS no host público esperado, `certificateId` e token público não vazios.
3. O token deve corresponder exatamente ao certificado publicado consultado pelo `certificateId`.
4. A hash-chain do certificado precisa ser íntegra e conter `certificate.emitted`.
5. Certificados reemitidos só retornam `reissued` se a trilha também satisfizer a evidência mínima de reemissão controlada.
6. A decisão é fail-closed: qualquer inconsistência retorna `not_found` para o público.

## Consequências

- O PRD §13.5 ganha evidência executável antes de existir endpoint HTTP real.
- O contrato pode ser reutilizado pelo backend futuro como guardrail do endpoint público.
- O público não recebe diferenciação entre token incorreto e falha interna da trilha.

## Limitações honestas

- A ADR não gera QR gráfico nem cobre o endpoint HTTP/SSR real.
- Não há assinatura criptográfica do token público nesta fatia; a validação é por correspondência exata com o certificado publicado.
- Revogação pública e políticas de consulta ainda não foram modeladas.
