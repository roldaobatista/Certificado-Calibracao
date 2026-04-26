# compliance/runbooks/ — Runbooks de recuperação

**Owner:** `product-governance`.

Este diretório contém runbooks regulatórios/metrológicos para cenários em que o sistema deve falhar fechado e recuperar operação com evidência arquivada.

## Runbooks obrigatórios

- `r1-kms-key-rotation.md` — rotação de chave KMS comprometida.
- `r2-audit-hash-chain-divergence.md` — divergência de hash-chain no audit log.
- `r3-worm-object-lock-violation.md` — violação de WORM/object lock.
- `r4-normative-package-disaster-recovery.md` — recuperação de pacote normativo.
- `r5-emission-revocation.md` — revogação de certificado emitido.
- `r6-security-incident.md` — incidente de segurança (breach, acesso indevido).
- `r7-backup-restore.md` — restauração de backup.
- `r8-reemission-procedure.md` — reemissão controlada de certificado.

## Comandos

```bash
pnpm runbook-check
```

## Evidência

Toda execução real ou drill deve criar uma pasta em:

```text
compliance/runbooks/executions/<YYYY-MM-DD>-<slug>/
```

A pasta deve conter, no mínimo:

- `summary.md` com incidente, dispatcher, executor, horários, decisão e resultado.
- logs dos comandos executados.
- hashes ou manifests usados na validação.
- links para incidentes, PRs, ADRs e notificações quando existirem.
