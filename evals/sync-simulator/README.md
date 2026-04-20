# evals/sync-simulator — Sync offline-first

Simulador determinístico de conflito. Ver `harness/08-sync-simulator.md` (P1-1).

## Cenários canônicos

- C1: mesma OS editada em 2 dispositivos offline, com conflito em fila humana.
- C2: assinatura cria lock e edição posterior recebe `OS_LOCKED_FOR_SIGNATURE`.
- C3: assinatura paralela permite apenas um sucesso.
- C4: reemissão preserva hash-chain e bloqueia nova emissão concorrente.
- C5: partição de rede converge com ordenação Lamport determinística.
- C6: replay por `(device_id, client_event_id)` é idempotente.
- C7: evento fora de ordem é aplicado por Lamport.
- C8: clock adulterado é normalizado pelo servidor e auditado.

## Execução

```bash
pnpm test:sync-simulator
pnpm sync-simulator-check
```

Falhas devem registrar seed, cenário e trace em `reports/`.
