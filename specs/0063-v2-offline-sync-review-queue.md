# 0063 - Fila canonica de sync offline e revisao humana V2

## Contexto

O roadmap em `harness/10-roadmap.md` define V2 como a fatia de sync offline-first robusto, com Android 100% offline, reconciliacao server-side e fila humana para conflitos C1-C8. O repositório ja possui o simulador deterministico em `evals/sync-simulator/`, mas ainda nao traduz essa disciplina em uma leitura operacional auditavel para o dispositivo, o backend e o back-office.

Sem essa fatia, o comportamento de sync existe apenas nos testes e no workflow offline basico. Falta uma fonte canonica para enxergar o outbox do Android, bloquear a emissao quando houver conflito aberto e materializar a triagem humana prevista no harness.

## Escopo

- Adicionar em `packages/contracts` um contrato compartilhado para:
  - resumo operacional do sync offline;
  - itens da outbox do Android com replay protection e status de armazenamento protegido;
  - fila de conflitos com SLA, responsavel e detalhe da decisao humana.
- Implementar em `apps/android/src` um builder canonico do item de outbox offline com fail-closed para storage nao protegido ou payload inconsistente.
- Implementar em `apps/api/src/domain/sync` um builder canonico da fila de revisao humana com cenarios alinhados a C1, C4 e C5 do simulador.
- Expor em `apps/api/src/interfaces/http` o endpoint canonico `GET /sync/review-queue`.
- Materializar em `apps/web/src` o loader e o view model para a leitura operacional do sync.
- Adicionar a pagina `apps/web/app/sync/review-queue/page.tsx`.
- Integrar a nova leitura de sync a partir da home do back-office.

## Fora de escopo

- Persistencia real da outbox Android em SQLCipher, transporte real de eventos ou reconciliacao transacional no banco.
- Push notification, websocket, retriable uploads reais, job scheduler do Android ou fila real de mensageria no backend.
- Resolucao automatica definitiva do conflito, edicao persistida da decisao humana ou escalacao real para um regulador externo.

## Criterios de aceite

- O contrato compartilhado representa resumo, outbox, fila de conflitos e detalhe da decisao humana com links para OS, workspace e trilha de auditoria.
- O builder Android falha fechado quando o storage do device nao estiver protegido, quando faltar replay protection ou quando o draft offline estiver invalido.
- O builder backend oferece:
  - um cenario estavel com upload convergente e sem conflito aberto;
  - um cenario com conflito humano aberto bloqueando a emissao da OS;
  - um cenario escalado por interpretacao regulatoria antes da resolucao.
- O endpoint `GET /sync/review-queue` responde com catalogo tipado e permite selecionar cenario, item de outbox e conflito por querystring.
- A pagina web traduz a fila humana de sync com SLA, decisao sugerida, requisitos de auditoria e bloqueio explicito de emissao enquanto o conflito estiver aberto.
- A home operacional passa a expor a leitura de sync como mais uma rota canonica do back-office.

## Evidencia

- `pnpm exec tsx --test apps/android/src/offline-sync.test.ts`
- `pnpm exec tsx --test apps/api/src/domain/sync/offline-sync-scenarios.test.ts`
- `pnpm exec tsx --test apps/web/src/sync/offline-sync-scenarios.test.ts`
- `pnpm exec tsx --test apps/api/src/app.test.ts`
- `pnpm exec tsx --test apps/web/src/home/operations-overview.test.ts`
- `pnpm check:all`
- `pnpm test:tenancy`
