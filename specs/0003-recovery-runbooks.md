# 0003 — Runbooks de recuperação regulatória

## Contexto

Os gates P0 já detectam falhas em assinatura normativa, hash-chain e WORM, mas a operação precisa de resposta versionada quando esses gates disparam. O harness P0-9 exige runbooks treináveis e evidência arquivada em `compliance/runbooks/`.

## Escopo

- Criar runbooks R1-R4 em `compliance/runbooks/`.
- Criar calendário de drills versionado.
- Criar área padrão para evidências de execução.
- Adicionar gate local `pnpm runbook-check`.
- Incluir `runbook-check` no `pnpm check:all`.

## Fora de escopo

- Executar drills reais de staging.
- Provisionar KMS, WORM ou storage frio de produção.
- Automatizar incident response completo fora da camada regulatória/metrológica.
- Substituir avaliação jurídica humana em incidente LGPD real.

## Requisitos

- REQ-HARNESS-P0-9-RUNBOOKS

## Critérios de aceite

- `pnpm runbook-check` falha se qualquer runbook R1-R4 estiver ausente.
- `pnpm runbook-check` falha se o calendário de drills não cobrir todos os runbooks.
- Cada runbook possui frontmatter com `id`, `version`, `status`, `owner`, `rto` e `rpo`.
- Cada runbook possui seções de trigger, impacto, papéis, passos, validação, evidência, drill e revisão.
- `pnpm check:all` executa `pnpm runbook-check`.

## Evidência

Evidências reais ou simuladas devem ser arquivadas em `compliance/runbooks/executions/<YYYY-MM-DD>-<slug>/`, com logs, decisões, responsáveis e resultado do drill ou incidente.
