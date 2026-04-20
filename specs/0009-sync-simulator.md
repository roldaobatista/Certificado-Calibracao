# Spec 0009 — Simulador determinístico de sync/conflito

## Objetivo

Implementar a primeira fatia funcional do P1-1: simulador determinístico C1-C8 com propriedades mínimas e gate estrutural.

## Escopo

- Motor determinístico em `evals/sync-simulator/engine/simulator.ts`.
- Cenários canônicos C1-C8 em `evals/sync-simulator/scenarios/canonical.yaml`.
- Seeds canônicos em `evals/sync-simulator/seeds/canonical/seeds.yaml`.
- Propriedades documentadas: convergência, hash-chain, lock de assinatura e idempotência.
- Teste `evals/sync-simulator/sync-simulator.test.ts` rodando 100 seeds determinísticos.
- Gate `pnpm sync-simulator-check` integrado ao `pnpm check:all` e pre-commit.

## Critérios de aceite

- C1 gera conflito em fila humana e bloqueia emissão da OS.
- C2 rejeita edição após assinatura com `OS_LOCKED_FOR_SIGNATURE`.
- C3 aceita apenas uma assinatura concorrente.
- C4 preserva hash-chain em reemissão e bloqueia nova emissão concorrente.
- C5 converge com ordenação Lamport determinística.
- C6 deduplica replay por `(device_id, client_event_id)`.
- C7 aplica eventos fora de ordem por Lamport.
- C8 normaliza clock futuro pelo relógio do servidor e registra divergência.

## Fora de escopo

- Não implementa endpoints reais de sync em `apps/api`.
- Não implementa Android offline.
- Não substitui a futura simulação volumétrica de V2; esta fatia estabelece o contrato determinístico e o gate.
