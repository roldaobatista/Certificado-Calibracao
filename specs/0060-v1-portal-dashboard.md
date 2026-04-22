# 0060 - Dashboard canonico do cliente no portal V1

## Contexto

O PRD detalha um dashboard autenticado do cliente com resumo de equipamentos, certificados recentes e proximos vencimentos na secao 17.5.2. Hoje o `apps/portal` materializa apenas a verificacao publica por QR, o que deixa sem leitura canonica a experiencia logada do cliente final.

Sem essa fatia, o portal ainda nao traduz de forma auditavel a carteira de equipamentos e certificados do cliente nem destaca vencimentos proximos ou atrasados.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo do dashboard do cliente;
  - lista de equipamentos com vencimento;
  - lista de certificados recentes com atalho para verificacao.
- Implementar em `apps/api/src/domain/portal` um builder canonico do dashboard.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /portal/dashboard`.
- Materializar em `apps/portal/src` o loader e o view model legivel para o dashboard.
- Adicionar a pagina `apps/portal/app/dashboard/page.tsx`.
- Integrar atalhos para o dashboard a partir da home do portal.

## Fora de escopo

- Login real do cliente, sessao persistida, permissao por usuario final ou vinculo real com organization membership.
- Paginas detalhadas de equipamentos, visualizador autenticado de certificados, documentos e suporte.
- Download real de PDF, solicitacao transacional de nova calibracao ou mensageria proativa.

## Criterios de aceite

- O contrato compartilhado representa resumo, equipamentos com vencimento e certificados recentes com status e atalho de verificacao.
- O builder canonico oferece um cenario estavel, um cenario com vencimentos proximos e um cenario bloqueado por equipamento vencido.
- O endpoint `GET /portal/dashboard` responde com catalogo tipado e selecao por querystring.
- A pagina do portal traduz a carteira do cliente em leitura operacional e permanece fail-closed sem payload valido do backend.
- A home do portal passa a oferecer atalhos coerentes para o dashboard autenticado.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/portal/portal-dashboard-scenarios.test.ts`
- `pnpm exec tsx --test apps/portal/src/portal-dashboard-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
