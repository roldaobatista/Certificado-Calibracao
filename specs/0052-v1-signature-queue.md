# 0052 — Fila canônica de assinatura e tela final de re-autenticação em V1

## Contexto

O PRD detalha a continuidade natural da emissão depois da prévia do certificado: uma fila operacional de assinaturas pendentes (§17.4.5) e a tela final de assinatura com re-autenticação do signatário (§17.4.6). O repositório já possui dry-run de emissão, workflow de revisão/assinatura, workspace operacional e prévia canônica do certificado, mas ainda não materializa uma leitura dedicada da fila de assinatura e do ato final de autorização.

Sem essa fatia, o back-office consegue dizer que um fluxo está pronto ou bloqueado, mas ainda não oferece uma visão auditável de quais certificados aguardam assinatura, quais pré-validações sustentam cada item e quando a assinatura deve falhar fechada antes da emissão.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para a fila de assinatura e o painel final de assinatura com re-autenticação.
- Estender os cenários canônicos de revisão/assinatura com um estado aprovado e pronto para assinar.
- Implementar em `apps/api/src/domain/emission` um builder canônico da fila de assinatura a partir da prévia do certificado e do workflow de revisão/assinatura.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /emission/signature-queue`.
- Materializar em `apps/web/src/emission` um view model legível para a fila e para o painel final de assinatura.
- Adicionar a página `apps/web/app/emission/signature-queue/page.tsx`.
- Integrar a nova leitura canônica na home operacional e nos atalhos do fluxo de emissão.

## Fora de escopo

- Assinatura eletrônica real, persistência transacional da emissão ou invalidação criptográfica do documento.
- Lote real com seleção persistida, paginação real de filas ou filtros conectados ao banco.
- Re-autenticação real com senha, TOTP ou sessão autenticada do usuário.
- Geração do PDF/A final ou publicação do certificado ao portal do cliente.

## Critérios de aceite

- O contrato compartilhado representa resumo da fila, itens pendentes, pré-validações, item selecionado e painel de assinatura final.
- O builder canônico deriva a fila a partir dos cenários já existentes de prévia e revisão/assinatura, sem inventar estados fora do backend.
- Itens com revisão aprovada, prévia pronta, QR autenticado e MFA válido aparecem como prontos para assinar.
- Itens com warnings regulatórios aparecem em atenção, mas continuam explicitando os riscos visíveis ao operador.
- Itens com MFA ausente, revisão incompatível ou prévia bloqueada permanecem fail-closed e impedem a assinatura final.
- O endpoint `GET /emission/signature-queue` responde com catálogo tipado e seleção por querystring.
- A página web traduz a fila e o painel final de assinatura em leitura operacional legível e permanece fail-closed sem payload válido do backend.
- A home operacional passa a resumir também a fila canônica de assinatura.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/emission/signature-queue-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/emission/review-signature-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/signature-queue-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
