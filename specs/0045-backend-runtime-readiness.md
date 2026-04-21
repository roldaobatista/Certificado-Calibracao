# 0045 — Readiness real do backend técnico

## Contexto

O scaffold de `apps/api` já diferenciava `/healthz` e `/readyz`, mas o endpoint de readiness ainda retornava `200 OK` sem verificar Postgres ou Redis. Isso cria falso positivo operacional: o processo sobe, mas o backend pode continuar incapaz de atender `apps/web`, `apps/portal` e sync server-side.

## Escopo

- Extrair a construção do Fastify para um `buildApp()` testável.
- Fazer `/healthz` permanecer como liveness do processo.
- Fazer `/readyz` executar checagem real de Postgres e Redis antes de responder pronto.
- Retornar `503` fail-closed quando qualquer dependência obrigatória falhar.
- Fechar clientes de readiness no shutdown da aplicação.
- Cobrir o contrato com testes locais em `apps/api/src`.

## Fora de escopo

- Orquestração Kubernetes.
- Pooling avançado, circuit breaker distribuído ou retries exponenciais.
- Auth, RBAC ou domínio de emissão propriamente dito.

## Requisitos

- REQ-HARNESS-P0-1-BACKEND-READINESS

## Critérios de aceite

- `/healthz` continua retornando `200` apenas para liveness do processo.
- `/readyz` retorna `200` somente quando Postgres responde a `SELECT 1` e Redis responde `PONG`.
- `/readyz` retorna `503` com motivo por dependência quando Postgres ou Redis falha.
- O shutdown do app fecha os recursos usados pela readiness.
- O healthcheck do container da API passa a apontar para `/readyz`.

## Evidência

- `pnpm exec tsx --test apps/api/src/infra/runtime-readiness.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm check:all`
