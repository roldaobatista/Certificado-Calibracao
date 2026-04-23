# Dossiê de Validação — Pós-V5: calendário da análise crítica

## Escopo validado

- Calendário mínimo da análise crítica reaproveitando `scheduledForUtc` das reuniões reais.
- Expansão do payload de `GET /quality/management-review` com agendamento, calendário consolidado e link de exportação `.ics`.
- Exportação `GET /quality/management-review/calendar.ics` para cenário canônico e para tenant autenticado.
- Atualização da tela web da análise crítica para explicitar calendário e exportação.

## Evidências executadas

- `pnpm --filter @afere/contracts build` — verde.
- `pnpm exec tsx --test apps/api/src/app.test.ts` — verde, incluindo:
  - leitura canônica da análise crítica com calendário mínimo;
  - leitura persistida autenticada com calendário consolidado;
  - exportação `.ics` canônica e persistida.
- `pnpm exec tsx --test apps/web/src/quality/management-review-scenarios.test.ts` — verde.
- `pnpm test:tenancy` — verde.
- `pnpm harness-dashboard:write` — verde.
- `pnpm check:all` — verde.

## Resultado

PASS

## Limitações honestas

- Ainda não existe integração bidirecional com calendários externos.
- O arquivo `.ics` não representa ata binária nem assinatura eletrônica da análise crítica.
- A exportação `.ics` continua pontual; qualquer sincronização contínua dependerá de nova fatia pós-V5.
