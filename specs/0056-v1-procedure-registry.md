# 0056 — Lista canônica de procedimentos versionados em V1

## Contexto

O PRD detalha no back-office uma lista versionada de procedimentos (§17.4.12), com revisões vigentes e obsoletas visíveis para consulta. O repositório já materializa OS, revisão técnica, dry-run, padrões e cadastros, mas ainda não oferece uma leitura canônica dos procedimentos que sustentam o método aplicado em cada emissão.

Sem essa fatia, o operador vê o rótulo do procedimento dentro da OS, mas não consegue navegar pela carteira versionada, distinguir revisão vigente de revisão obsoleta e entender rapidamente o escopo operacional e os vínculos do procedimento selecionado.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canônica de procedimentos;
  - resumo com vigentes, atenção de revisão e obsoletos;
  - detalhe do procedimento selecionado no próprio catálogo.
- Implementar em `apps/api/src/domain/registry` um builder canônico de procedimentos versionados.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /registry/procedures`.
- Materializar em `apps/web/src/registry` o loader e o view model legível para procedimentos.
- Adicionar a página `apps/web/app/registry/procedures/page.tsx`.
- Integrar atalhos de procedimentos a partir do workspace e da revisão técnica da OS.

## Fora de escopo

- CRUD real de procedimentos, editor rich text, aprovação transacional, anexos binários e diffs reais entre revisões.
- Seleção automática do procedimento dentro da OS real, workflow de publicação de revisão ou bloqueio persistido em banco.
- Matriz documental completa de MQ/PG/PT/IT/FR ou assinatura real de documentos da qualidade.

## Critérios de aceite

- O contrato compartilhado representa lista, resumo e detalhe do procedimento selecionado, incluindo revisões vigentes e obsoletas.
- O builder canônico mostra um cenário operacional com procedimento vigente, um cenário em atenção por revisão próxima e um cenário com revisão obsoleta visível apenas para consulta.
- O endpoint `GET /registry/procedures` responde com catálogo tipado e seleção por querystring.
- A página web traduz a lista versionada em leitura operacional legível e permanece fail-closed sem payload válido do backend.
- Workspace e revisão técnica da OS passam a oferecer atalhos coerentes para a carteira de procedimentos.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/registry/procedure-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/registry/procedure-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
