# 0004 — Cascata de verificação L0-L5

## Contexto

O harness P0-10 define uma cascata de verificação de L0 a L5, com propagação bidirecional e full regression em áreas críticas. Antes desta spec, a seleção de regressão existia parcialmente no dossiê, mas não havia um planejador explícito da cascata nem registro canônico para re-auditorias.

## Escopo

- Criar `tools/verification-cascade.ts`.
- Detectar mudanças em áreas críticas L4.
- Selecionar testes de regressão por área crítica a partir de `requirements.yaml`.
- Marcar snapshot-diff obrigatório para mudanças críticas.
- Validar pareceres L5 dos três auditores para uma release.
- Criar `compliance/verification-log/` como destino de propagação e re-auditoria.

## Fora de escopo

- Implementar snapshot-diff real de certificados canônicos.
- Executar pareceres dos auditores.
- Automatizar criação de issues GitHub para propagação.
- Substituir revisão humana de L0, L1, L2 ou L5.

## Requisitos

- REQ-HARNESS-P0-10-VERIFICATION-CASCADE

## Critérios de aceite

- `pnpm verification-cascade:plan --changed packages/audit-log/src/verify.ts` identifica área crítica.
- Mudança em área crítica exige full regression e snapshot-diff.
- Mudança fora da lista crítica não exige snapshot-diff.
- `verification-cascade release-audits --release <versao>` falha sem os três pareceres em `compliance/audits/metrology|legal|code/`.
- `pnpm verification-cascade:check` valida a presença do registro canônico de propagação.
- `pnpm check:all` executa `pnpm verification-cascade:check`.

## Evidência

Propagações reais devem ser registradas em `compliance/verification-log/<REQ-id>.yaml`. Evidências de execução continuam em `compliance/validation-dossier/evidence/<REQ-id>/`.
