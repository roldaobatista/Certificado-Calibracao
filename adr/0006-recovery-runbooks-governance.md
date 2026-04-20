# ADR 0006 — Governança dos runbooks de recuperação

## Status

Proposto para P0-9 em 2026-04-20.

## Contexto

O Aferê já possui gates para falhar fechado em cenários críticos: pacote normativo inválido, hash-chain divergente, storage WORM sem retenção e falhas de governança. Sem runbooks executáveis, a organização detecta o problema, mas não possui rito versionado para contenção, restauração, evidência e retorno seguro.

## Decisão

1. Runbooks regulatórios vivem em `compliance/runbooks/`.
2. Os quatro runbooks P0-9 são obrigatórios:
   - R1: rotação de chave KMS comprometida.
   - R2: hash-chain divergente no audit log.
   - R3: violação de WORM/object lock.
   - R4: disaster recovery de pacote normativo.
3. Cada runbook possui frontmatter mínimo (`id`, `version`, `status`, `owner`, `rto`, `rpo`) e seções obrigatórias.
4. `drill-schedule.yaml` registra frequência, próximo vencimento, owner e destino de evidência de cada drill.
5. `pnpm runbook-check` passa a validar a presença e estrutura mínima dos runbooks.
6. `pnpm check:all` passa a executar `pnpm runbook-check`.
7. Execuções reais e drills arquivam evidência em `compliance/runbooks/executions/<YYYY-MM-DD>-<slug>/`.

## Consequências

- Falhas críticas passam a ter resposta operacional rastreável.
- Mudanças em runbook entram no fluxo de PR + ADR por alterarem `compliance/**`.
- P0-9 fica implementado em estrutura e gate, mas drills reais de staging ainda precisam ser executados para declarar maturidade operacional.
- O dossiê pode rastrear P0-9 por requisito validado contra `tools/runbook-check.test.ts`.
