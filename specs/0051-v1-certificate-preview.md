# 0051 — Prévia canônica do certificado antes da assinatura em V1

## Contexto

O PRD §7.7.5 exige que, antes de fechar a execução, o sistema renderize uma prévia integral do certificado com todos os campos relevantes já preenchidos. Hoje o repositório já possui dry-run real de emissão, workflow de revisão/assinatura e workspace operacional, mas ainda não materializa uma leitura canônica dedicada da pré-visualização do certificado.

Sem essa fatia, o back-office consegue validar gates e prontidão, mas ainda não mostra de forma auditável a peça que o operador realmente deve conferir antes da assinatura final.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para a prévia do certificado.
- Enriquecer os cenários do dry-run com dados mínimos de apresentação necessários para a prévia.
- Implementar em `apps/api/src/domain/emission` um builder canônico da pré-visualização do certificado a partir do dry-run.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /emission/certificate-preview`.
- Materializar em `apps/web/src/emission` um view model legível para a prévia.
- Adicionar a página `apps/web/app/emission/certificate-preview/page.tsx`.

## Fora de escopo

- Geração de PDF/A final ou renderer visual fiel ao layout definitivo do certificado.
- Persistência real de OS, evidências, assinatura eletrônica, revisão técnica ou emissão oficial.
- Edição livre da prévia fora do fluxo controlado.
- Portal autenticado do cliente ou envio de notificações após conferência.

## Critérios de aceite

- O contrato compartilhado representa status, seções visuais, QR, template, política de símbolo e passo sugerido de retorno.
- O builder canônico traduz os cenários do dry-run em uma prévia integral com cabeçalho, identificação, padrões, ambiente, resultados, decisão, autorização e rodapé.
- Quando o dry-run estiver bloqueado, a prévia continua fail-closed e sugere o menor passo do wizard ao qual o operador deve retornar.
- O endpoint `GET /emission/certificate-preview` responde com catálogo tipado e seleção por querystring.
- A página web traduz a prévia em seções legíveis e permanece fail-closed sem payload válido do backend.
- O dry-run e o workspace passam a oferecer navegação direta para a prévia canônica.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/emission/certificate-preview-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/certificate-preview-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
