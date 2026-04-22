# 0053 — Lista canônica de OS e detalhe de revisão técnica em V1

## Contexto

O PRD detalha no back-office uma lista de ordens de serviço (§17.4.3) e uma tela de detalhe/revisão técnica da OS (§17.4.4) antes da aprovação e da fila de assinatura. O repositório já possui workspace operacional, workflow de revisão/assinatura, prévia do certificado e fila final de assinatura, mas ainda não materializa a leitura canônica da própria OS em revisão.

Sem essa fatia, o operador consegue navegar entre prontidão, prévia e assinatura, mas ainda não enxerga de forma auditável a peça intermediária que reúne linha do tempo, dados de execução, checklist técnico e ações de aprovação/devolução ao técnico.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para a lista canônica de OS e o detalhe de revisão técnica.
- Implementar em `apps/api/src/domain/emission` um builder canônico que componha lista, detalhe, checklist, timeline e ações da OS.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /emission/service-order-review`.
- Materializar em `apps/web/src/emission` um view model legível para a lista e o detalhe da OS.
- Adicionar a página `apps/web/app/emission/service-order-review/page.tsx`.
- Integrar a nova leitura canônica na home operacional e nas rotas adjacentes do fluxo de emissão.

## Fora de escopo

- Persistência real de OS, filtros reais, paginação real, anexos binários ou timeline vinda do banco.
- Aprovação transacional da revisão técnica, devolução real ao técnico ou mudança de status persistida.
- Editor rico de comentários, anexos de fotos reais ou visualização do balanço de incerteza completo.
- Substituir a futura tela operacional definitiva conectada a autenticação e autorização reais.

## Critérios de aceite

- O contrato compartilhado representa resumo da lista, itens de OS, timeline, métricas de execução, checklist técnico, comentários e ações disponíveis.
- O builder canônico deriva o detalhe da OS a partir das leituras já existentes de prévia, workflow e fila, sem inventar estado fora do backend.
- Um cenário pronto para revisão mostra checklist completo, timeline coerente e ação liberada para aprovar a revisão.
- Um cenário em atenção mostra pendência explícita no checklist e mantém a revisão fail-closed até a conferência final.
- Um cenário bloqueado mostra conflitos de revisão ou gates críticos que impedem a aprovação da OS.
- O endpoint `GET /emission/service-order-review` responde com catálogo tipado e seleção por querystring.
- A página web traduz lista e detalhe da OS em leitura operacional legível e permanece fail-closed sem payload válido do backend.
- A home operacional passa a resumir também a leitura canônica de OS em revisão.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/emission/service-order-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/emission/service-order-review-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
