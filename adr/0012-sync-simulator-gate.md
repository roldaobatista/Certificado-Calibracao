# ADR 0012 — Gate do simulador determinístico de sync

Status: Aprovado

Data: 2026-04-20

## Contexto

O P1-1 exige simulador determinístico para conflitos de sync offline. O diretório existia apenas como placeholder, sem cenários C1-C8 executáveis nem gate de estrutura.

## Decisão

Criar a primeira fatia funcional do simulador em `evals/sync-simulator/`:

- motor determinístico server-driven com idempotency key;
- ordenação Lamport;
- lock de assinatura;
- fila humana para conflito regulatório;
- hash-chain local para audit log simulado;
- 100 seeds determinísticos em `pnpm test:sync-simulator`;
- `pnpm sync-simulator-check` como gate estrutural.

## Consequências

O harness passa a detectar regressão estrutural no simulador antes de V2. A implementação ainda é um modelo de avaliação, não o backend real de sync.

## Limitação

O simulador ainda não cobre 1.000 OS em 5 dispositivos nem endpoints reais. Esses itens permanecem para a fatia V2 do roadmap.
