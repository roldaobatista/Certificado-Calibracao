# ADR 0048 — Backend distingue liveness e readiness com probes reais de Postgres e Redis

- Status: proposto para implementacao
- Data: 2026-04-21
- Relacionado: `specs/0045-backend-runtime-readiness.md`, `adr/0001-backend-framework.md`, P0-1 em `harness/STATUS.md`

## Contexto

O backend `apps/api` já estava de pé como scaffold Fastify, mas o endpoint `/readyz` era apenas um stub. Em ambiente regulado, declarar prontidão sem dependências essenciais disponíveis mascara falha operacional e pode deixar o orquestrador enviar tráfego para uma API incapaz de acessar Postgres ou Redis.

## Decisão

1. `apps/api/src/app.ts` passa a montar o Fastify de forma testável, separado do bootstrap de `server.ts`.
2. `/healthz` permanece como liveness do processo, sem depender de Postgres ou Redis.
3. `/readyz` passa a executar `SELECT 1` via `@prisma/client` para Postgres e `PING` via cliente Redis oficial.
4. Qualquer falha nessas dependências retorna `503` com status `not_ready`, sem declarar prontidão parcial.
5. Os clientes usados pela readiness são fechados no `onClose` do Fastify.
6. O healthcheck do container passa a consultar `/readyz`, alinhando runtime local com o contrato HTTP.

## Consequências

- O backend deixa de reportar falso positivo de prontidão.
- O contrato fica coberto por testes locais sem exigir Postgres/Redis reais para cada teste unitário.
- `server.ts` fica mais simples e o app passa a poder ser validado por `inject()`.

## Limitações honestas

- A ADR não adiciona circuit breakers nem retries distribuídos.
- O probe de Postgres valida conectividade e execução mínima, não semântica de migrations.
- O probe de Redis valida `PING`, não filas, memória ou latência operacional.
