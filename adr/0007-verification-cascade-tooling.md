# ADR 0007 — Tooling da cascata de verificação

## Status

Proposto para P0-10 em 2026-04-20.

## Contexto

O harness define L0-L5, full regression em áreas críticas, snapshot-diff obrigatório e pareceres L5. Sem uma ferramenta local, cada PR dependeria de interpretação manual para descobrir quais gates aplicar.

## Decisão

1. Criar `tools/verification-cascade.ts`.
2. A lista fechada de áreas críticas L4 fica codificada no tool, espelhando `harness/14-verification-cascade.md`.
3. `verification-cascade plan --changed <arquivo>` gera um plano determinístico para o delta.
4. Mudanças em área crítica exigem:
   - full regression dos REQs `blocker` e `high` ligados à área;
   - snapshot-diff de certificados canônicos.
5. `verification-cascade release-audits --release <versao>` valida a presença dos três pareceres externos obrigatórios:
   - `compliance/audits/metrology/<versao>.md`;
   - `compliance/audits/legal/<versao>.md`;
   - `compliance/audits/code/<versao>.md`.
6. `compliance/verification-log/` é o destino canônico dos registros de propagação bidirecional.
7. `pnpm verification-cascade:check` entra em `pnpm check:all`.

## Consequências

- A seleção de regressão L4 deixa de ser ad hoc.
- Release sem pareceres dos três auditores pode ser bloqueado por comando determinístico.
- Snapshot-diff ainda é apenas um requisito sinalizado; a implementação real dos 30 certificados canônicos fica para fatia posterior.
- Propagação bidirecional ganha diretório canônico, mas automação de criação de issue e validação semântica dos logs ainda é incremental.
