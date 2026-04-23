# Dossiê de Validação — Pós-V5: histórico dos indicadores

## Escopo validado

- Persistência mensal dedicada dos indicadores da Qualidade por tenant.
- Leitura autenticada de `GET /quality/indicators` usando histórico consolidado real.
- Escrita mínima de snapshots via `POST /quality/indicators/manage`.
- Alinhamento do painel web para explicitar o uso de histórico mensal consolidado.

## Evidências executadas

- `pnpm --filter @afere/db prisma:generate` — verde.
- `pnpm --filter @afere/api typecheck` — verde.
- `pnpm --filter @afere/web typecheck` — verde.
- `pnpm exec tsx --test apps/api/src/app.test.ts` — verde, incluindo:
  - leitura persistida dos indicadores com janela histórica real;
  - gravação autenticada de snapshot mensal por `POST /quality/indicators/manage`.
- `pnpm exec tsx --test apps/web/src/quality/quality-indicator-scenarios.test.ts` — verde.
- `pnpm test:tenancy` — verde.
- `pnpm check:all` — verde.

## Resultado

PASS

## Limitações honestas

- O histórico persistido continua mensal e manual; não há scheduler automático nesta fatia.
- O painel segue sem exportação binária, filtros analíticos avançados ou warehouse dedicado.
- Metas por tenant, ata binária, calendário e assinatura eletrônica da análise crítica seguem para evolução futura.
