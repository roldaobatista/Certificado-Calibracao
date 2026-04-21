# 0027 — Validação volumétrica do PRD §13.20 no simulador de sync

## Contexto

O PRD §13.20 exige que o modelo de sincronização offline esteja documentado e testado com caos de `1.000` OS geradas offline em pelo menos `5` dispositivos, com sync randomizado e resultado final de zero perdas e zero duplicatas.

A primeira fatia de `evals/sync-simulator/` já cobre a matriz canônica `C1-C8`, idempotência, ordenação Lamport, lock de assinatura e fila humana. O gap pendente é a validação volumétrica do comportamento saudável sob carga determinística.

## Escopo

- Estender o motor em `evals/sync-simulator/engine/simulator.ts` com uma rotina determinística de caos volumétrico.
- Adicionar teste ativo em `evals/sync-simulator/prd-13-20-offline-sync-chaos.test.ts`.
- Exercitar exatamente `1.000` OS em `5` dispositivos com ordem de sync randomizada por seed determinística.
- Validar zero perdas, zero duplicatas, convergência e hash-chain íntegra.
- Promover `REQ-PRD-13-20-OFFLINE-SYNC-CHAOS` para `validated` no dossiê se a evidência ficar completa.

## Fora de escopo

- Implementar endpoints reais de sync em `apps/api`.
- Implementar cliente Android offline-first real.
- Substituir a matriz canônica `C1-C8`; ela continua sendo a fonte de regras de conflito.
- Introduzir infraestrutura externa, filas reais ou banco de dados para a simulação.

## Critérios de aceite

- O teste `evals/sync-simulator/prd-13-20-offline-sync-chaos.test.ts` roda em CI e falha se a carga não atingir `1.000` OS e `5` dispositivos.
- O cenário volumétrico detecta replay duplicado sem gerar efeito colateral duplicado no estado final ou no audit log.
- O relatório do cenário comprova:
  - `0` OS perdidas;
  - `0` duplicatas aceitas;
  - convergência final;
  - hash-chain íntegra.
- `REQ-PRD-13-20-OFFLINE-SYNC-CHAOS` deixa de ser `planned` e passa a `validated` apenas com teste ativo apontando para o arquivo novo.

## Evidência

- `pnpm exec tsx --test evals/sync-simulator/prd-13-20-offline-sync-chaos.test.ts`
- `pnpm test:sync-simulator`
- `pnpm validation-dossier:check -- --strict-prd`
