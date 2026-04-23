# Spec 0081 — Pós-V5: calendário mínimo da análise crítica

## Contexto

Depois da V5, a análise crítica passou a operar sobre reuniões persistidas do tenant, com pauta, deliberações e entradas automáticas reais. Ainda assim, o módulo seguia sem uma agenda consolidada mínima nem uma exportação simples para calendário externo.

Sem esta fatia pós-V5, a direção consegue ler a reunião no back-office, mas não consegue reaproveitar o agendamento em fluxo operacional real nem preservar uma ponte auditável mínima entre pauta persistida e compromisso de calendário.

## Escopo

- Reaproveitar `scheduledForUtc` das reuniões persistidas da análise crítica para montar um calendário consolidado mínimo.
- Expandir o contrato compartilhado da análise crítica com:
  - rótulo de agendamento da reunião selecionada;
  - resumo do calendário consolidado;
  - link de exportação `.ics` por reunião.
- Fazer `GET /quality/management-review` expor o calendário tanto nos cenários canônicos quanto na leitura persistida autenticada.
- Adicionar `GET /quality/management-review/calendar.ics` para exportação autenticada da reunião persistida e exportação canônica por `?scenario=`.
- Atualizar a página web da análise crítica para mostrar agendamento, calendário consolidado e link de exportação `.ics`.

## Fora de escopo

- Integração bidirecional com Google Calendar, Outlook ou qualquer agenda externa.
- Ata binária, GED, upload/download de anexo da reunião ou assinatura eletrônica da análise crítica.
- Lembretes automáticos, recorrência avançada, RSVP, convites por e-mail ou sincronização mobile.
- Mudança de schema de banco; esta fatia deve reutilizar `scheduledForUtc` já persistido na V5.

## Critérios de aceite

- `packages/contracts/src/management-review.ts` versiona o calendário mínimo da análise crítica sem quebrar o payload existente.
- `apps/api/src/domain/quality/management-review-scenarios.ts` e `apps/api/src/domain/quality/persisted-quality-catalogs.ts` expõem `scheduledForLabel`, `calendar` e `calendarExportHref`.
- `GET /quality/management-review/calendar.ics` retorna `text/calendar` com uma reunião válida para cenário canônico ou tenant autenticado.
- A exportação persistida exige sessão e RBAC de leitura da Qualidade quando não houver `?scenario=`.
- `apps/web/app/quality/management-review/page.tsx` explicita calendário, agendamento e exportação `.ics` da reunião selecionada.
- Os testes do backend cobrem leitura canônica, leitura persistida e exportação `.ics`, e os testes web continuam verdes com o contrato expandido.

## Evidência

- `pnpm --filter @afere/contracts build`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/management-review-scenarios.test.ts`
- `pnpm test:tenancy`
- `pnpm harness-dashboard:write`
- `pnpm check:all`
