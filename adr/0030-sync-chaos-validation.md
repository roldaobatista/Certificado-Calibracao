# ADR 0030 — Validação volumétrica do PRD §13.20 no simulador de sync

- Status: proposto para implementação
- Data: 2026-04-21
- Relacionado: `specs/0027-prd-13-20-sync-chaos-validation.md`, `harness/08-sync-simulator.md`, `PRD.md` §13.20

## Contexto

O simulador determinístico de sync já cobre a matriz canônica `C1-C8`, mas o PRD §13.20 ainda exigia a parte volumétrica: `1.000` OS offline em pelo menos `5` dispositivos com sync randomizado, zero perdas e zero duplicatas.

Sem essa camada, o repositório provava as regras de conflito em exemplos pequenos, mas não tinha evidência ativa de comportamento saudável sob carga determinística.

## Decisão

Adicionar uma rotina `runOfflineSyncChaos()` em `evals/sync-simulator/engine/simulator.ts` que:

1. gere deterministicamente `1.000` OS distribuídas em `5` dispositivos;
2. injete replay duplicado controlado em parte dos eventos;
3. embaralhe a ordem de chegada por seed;
4. processe tudo no mesmo reconciliador server-driven já usado pela suite canônica;
5. devolva um relatório explícito com:
   - eventos esperados;
   - eventos aceitos;
   - replays detectados;
   - comprimento da hash-chain;
   - OS ausentes;
   - propriedades finais de convergência, hash-chain e idempotência.

O teste ativo de PRD passa a viver em `evals/sync-simulator/prd-13-20-offline-sync-chaos.test.ts`.

## Consequências

- O PRD §13.20 pode ser promovido para `validated` de forma honesta, sem depender de backend real ou app Android real.
- A validação continua sendo um artefato determinístico de laboratório, não benchmark de produção.
- A matriz de conflitos `C1-C8` continua sendo a fonte principal de regras regulatórias; o caos volumétrico complementa a evidência com escala e replay.

## Limitações honestas

- O simulador não substitui a futura implementação real de sync em `apps/api` e `apps/android`.
- O teste volumétrico cobre perda/duplicação/convergência, mas não mede throughput, latência ou consumo real de infraestrutura.
- O PRD §13.20 fica validado no nível de modelo e evidência automatizada; rollout operacional ainda depende das fatias V1+.
