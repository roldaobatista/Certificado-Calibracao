# 0058 — Módulo canônico de não conformidades no back-office V1

## Contexto

O PRD detalha um módulo de não conformidades com lista operacional, severidade, responsável e idade (§17.4.13). O repositório já possui workspace, procedimentos, trilha de auditoria e revisão técnica, mas ainda não materializa uma leitura canônica das NCs que conecte origem, gravidade, ações e vínculos com os fluxos de emissão.

Sem essa fatia, a equipe consegue identificar bloqueios pontuais em páginas isoladas, mas ainda não tem uma visão auditável e consolidada das NCs abertas, críticas ou encerradas no back-office.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canônica de não conformidades;
  - resumo por criticidade/estado;
  - detalhe da NC selecionada no próprio catálogo.
- Implementar em `apps/api/src/domain/quality` um builder canônico das NCs.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /quality/nonconformities`.
- Materializar em `apps/web/src/quality` o loader e o view model legível para NCs.
- Adicionar a página `apps/web/app/quality/nonconformities/page.tsx`.
- Integrar atalhos de NCs a partir do workspace e da trilha de auditoria.

## Fora de escopo

- Workflow transacional de abrir/fechar NC, anexos binários, comentários persistidos e plano de ação real.
- Filtros persistidos, paginação real, workflow CAPA completo ou indicadores mensais agregados.
- Integração com e-mail, SLA automático ou aprovação formal de encerramento.

## Critérios de aceite

- O contrato compartilhado representa lista, resumo e detalhe da NC selecionada com origem, severidade, responsável, idade e ações.
- O builder canônico oferece um cenário de NC aberta moderada, um cenário crítico bloqueante e um cenário histórico resolvido.
- O endpoint `GET /quality/nonconformities` responde com catálogo tipado e seleção por querystring.
- A página web traduz a lista de NCs em leitura operacional legível e permanece fail-closed sem payload válido do backend.
- Workspace e trilha de auditoria passam a oferecer atalhos coerentes para o módulo de NCs.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/quality/nonconformity-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/nonconformity-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
