# Spec 0080 — Pós-V5: BI histórico dos indicadores da Qualidade

## Contexto

O fechamento da V5 colocou NCs, trabalho não conforme, auditoria interna, análise crítica, hub e perfil regulatório sobre dados reais do tenant. Mesmo assim, o módulo de indicadores ainda sintetiza snapshots mensais em memória, sem trilha persistida própria para leitura histórica consolidada.

Sem esta fatia pós-V5, o painel continua útil para operação corrente, mas não sustenta um BI histórico minimamente auditável para a direção revisar tendência, deriva e estabilização mês a mês.

## Escopo

- Materializar snapshots históricos mensais dos indicadores da Qualidade em tabela dedicada por tenant.
- Permitir gravação mínima desses snapshots por `POST /quality/indicators/manage`, mantendo RBAC de escrita igual ao restante da camada de Qualidade persistida.
- Fazer `GET /quality/indicators` preferir o histórico persistido do tenant para:
  - janela mensal consolidada;
  - valor atual consolidado;
  - tendência baseada na série real;
  - snapshots exibidos no detalhe do indicador.
- Reaproveitar o contrato existente do painel de indicadores, sem abrir uma API paralela de BI.
- Alinhar o hub e a página web para deixar explícito que a leitura usa histórico mensal consolidado.
- Popular o seed local com uma série mínima auditável para os três indicadores persistidos da V5.

## Fora de escopo

- Warehouse dedicado, OLAP, cubos, filtros analíticos avançados, exportação binária, CSV/XLSX ou integrações externas de BI.
- Metas configuráveis por tenant, job scheduler mensal automático ou recomputação assíncrona.
- Calendário, ata binária ou assinatura eletrônica da análise crítica.
- Substituir o recorte operacional vivo da V5 por fechamento contábil/regulatório completo; esta fatia adiciona histórico persistido, não um data mart completo.

## Critérios de aceite

- `packages/db/prisma/schema.prisma` materializa snapshots mensais de indicadores por tenant, com unicidade por indicador+mês.
- `apps/api/src/domain/quality/quality-persistence.ts` lista e persiste snapshots históricos de indicadores.
- `GET /quality/indicators` sem `?scenario=` usa snapshots persistidos quando existirem e mantém fallback fail-closed para tenants sem histórico.
- `POST /quality/indicators/manage` grava snapshot mensal autenticado com RBAC de Qualidade.
- O payload existente do painel continua válido, mas passa a refletir janela mensal real, valor atual consolidado e tendência baseada no histórico persistido.
- `apps/web/app/quality/indicators/page.tsx` explicita que a leitura autenticada usa histórico mensal consolidado.
- O seed local contém pelo menos 6 meses de histórico para os indicadores persistidos da V5.

## Evidência

- `pnpm --filter @afere/db prisma:generate`
- `pnpm --filter @afere/api typecheck`
- `pnpm --filter @afere/web typecheck`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/quality/quality-indicator-scenarios.test.ts`
- `pnpm test:tenancy`
- `pnpm check:all`
