---
description: Roda ownership-lint (Gate 6) contra arquivos/globs para detectar imports cruzando boundaries de ownership
---

Executa `@afere/ownership-lint` contra `$ARGUMENTS` (paths relativos ou globs).

## Execução

```bash
pnpm --filter @afere/ownership-lint exec node --import tsx src/cli.ts $ARGUMENTS
```

Se `$ARGUMENTS` estiver vazio, o CLI usa os scopes declarados por regra em `packages/ownership-lint/src/rules.yaml`:
- `apps/web/**` e `apps/portal/**` (TS/TSX/JS/JSX): checa imports contra `@afere/normative-rules`, `@afere/engine-uncertainty`, `@afere/db`.
- `apps/android/**` (Kotlin/Java): idem.

## O que bloquear

Regras atuais (ver `rules.yaml`):
- **OWN-001** — web/portal importando `@afere/normative-rules`.
- **OWN-002** — web/portal importando `@afere/engine-uncertainty`.
- **OWN-003** — android importando `@afere/normative-rules` ou `@afere/engine-uncertainty`.
- **OWN-004** — clientes importando `@afere/db`.

## Interpretação

- Exit 0 → sem violação.
- Exit 1 → pelo menos uma violação `error`. Commit bloqueado pelo hook PreCommit.

## Fluxo após detecção

1. Para cada finding: trocar import direto por chamada via tRPC procedure em `@afere/contracts`.
2. Se a necessidade legítima **não existir** na API, criar procedure em `packages/contracts` + implementação em `apps/api/src/domain/*` via `backend-api`.
3. Nunca adicionar exceção de ownership sem ADR explícito + aprovação de `product-governance`.

Referências: `harness/02-arquitetura.md` (ownership duro), `harness/05-guardrails.md` Gate 6, `compliance/guardrails.md`.
