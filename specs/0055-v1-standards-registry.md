# 0055 — Gestão canônica de padrões e detalhe do padrão para V1

## Contexto

O PRD detalha no back-office uma gestão de padrões com painel de vencimentos (§17.4.10) e um detalhe dedicado do padrão (§17.4.11). O repositório já possui regra executável para elegibilidade do padrão na emissão, mas ainda não materializa uma leitura canônica da carteira de padrões, dos vencimentos próximos e do histórico de calibrações que sustentam o uso auditável desses artefatos.

Sem essa fatia, o operador consegue saber que um dry-run bloqueou por padrão vencido, mas não consegue navegar de forma auditável pela lista de padrões, entender o vencimento iminente e inspecionar o histórico do padrão responsável por uma OS.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - lista canônica de padrões;
  - painel resumido de vencimentos;
  - detalhe do padrão com histórico de calibrações e uso recente em OS.
- Implementar em `apps/api/src/domain/registry` um builder canônico para padrões, reaproveitando a regra de `evaluateStandardEligibility`.
- Expor em `apps/api/src/interfaces/http` o endpoint canônico `GET /registry/standards`.
- Materializar em `apps/web/src/registry` o loader e o view model legível para padrões.
- Adicionar as páginas:
  - `apps/web/app/registry/standards/page.tsx`
  - `apps/web/app/registry/standard-detail/page.tsx`
- Integrar atalhos de padrões a partir do workspace e da lista global de equipamentos.

## Fora de escopo

- CRUD real de padrões, anexos binários reais, upload de certificados e solicitação real de nova calibração.
- Geração de gráfico interativo, filtros persistidos, paginação real ou download real do PDF do padrão.
- Workflow transacional de reserva/liberação do padrão em OS reais.

## Critérios de aceite

- O contrato compartilhado representa lista, painel de vencimentos, detalhe do padrão, histórico de calibrações e uso recente em OS.
- O builder canonico deriva o status do padrão usando `evaluateStandardEligibility`, sem duplicar a regra regulatória no web.
- Um cenario operacional mostra padrões válidos e sem vencimento crítico no horizonte curto.
- Um cenario em atenção destaca padrão ainda elegível, mas já entrando em janela crítica de vencimento.
- Um cenario bloqueado destaca padrão vencido ou inelegível para uso em emissão.
- O endpoint `GET /registry/standards` responde com catálogo tipado e seleção por querystring.
- As páginas web traduzem a lista e o detalhe do padrão em leitura operacional legível e permanecem fail-closed sem payload válido do backend.
- Workspace e lista global de equipamentos passam a oferecer atalhos para a gestão de padrões.

## Evidência

- `pnpm exec tsx --test apps/api/src/domain/registry/standard-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/registry/standard-registry-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
