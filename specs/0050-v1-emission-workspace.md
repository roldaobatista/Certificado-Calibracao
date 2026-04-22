# 0050 — Workspace canonico de prontidao de emissao para V1

## Contexto

O roadmap V1 ja ganhou leituras canonicas isoladas para auto-cadastro, onboarding, diretorio de usuarios, dry-run de emissao e workflow de revisao/assinatura. Ainda falta uma visao agregada do back-office que una esses sinais em um unico workspace operacional antes da emissao oficial.

Sem essa consolidacao, a home lista cards independentes, mas a operacao continua sem um payload auditavel que responda de forma direta: "o laboratorio pode seguir agora, precisa agir preventivamente ou esta bloqueado por gates criticos?".

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para o workspace de prontidao de emissao.
- Implementar em `apps/api/src/domain/emission` um agregador canonico que compose auth, onboarding, equipe, dry-run e workflow de revisao/assinatura.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /emission/workspace`.
- Materializar em `apps/web/src/emission` um view model legivel para o workspace.
- Adicionar a pagina `apps/web/app/emission/workspace/page.tsx`.
- Integrar o workspace na home operacional do back-office.

## Fora de escopo

- Persistencia real de OS, sessao autenticada, fila real de assinatura ou workflow transacional.
- PDF/A final, assinatura eletronica real, notificacoes ou portal autenticado do cliente.
- Dashboard historico, analytics ou telemetria de produtividade.
- Substituir as telas canonicas individuais de auth, onboarding, diretorio, dry-run e workflow.

## Criterios de aceite

- O contrato compartilhado representa status consolidado, modulos, referencias de cenarios e proximas acoes do workspace.
- O agregador classifica o workspace como `ready`, `attention` ou `blocked` de forma deterministica a partir dos modulos canonicos.
- O endpoint `GET /emission/workspace` responde com catalogo tipado e selecao por querystring.
- A pagina web traduz o workspace em resumo operacional, links para os modulos e lista de proximas acoes.
- A home do back-office passa a resumir tambem o workspace canonico de emissao.
- Sem payload valido do backend, a leitura web permanece fail-closed.

## Evidencia

- `pnpm exec tsx --test apps/api/src/domain/emission/emission-workspace-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/emission-workspace-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
