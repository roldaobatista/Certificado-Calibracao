---
id: FINDING-2026-04-19-001
source: copy-lint (packages/copy-lint)
tool_version: 0.0.1
date_detected: 2026-04-19
status: closed
severity: error
owner: copy-compliance
escalated_to: product-governance
date_resolved: 2026-04-20
resolution_ref: adr/0018-prd-copy-claims-remediation.md
---

# Finding: Claims proibidos em `PRD.md`

## Contexto

Primeira execução do `@afere/copy-lint` (P0-5) contra o repo — "teste de fogo" previsto em `harness/06-copy-lint.md`. O próprio PRD v1.8 contém, em seu wireframe da home (§7.15), textos que são listados como **error** pelas regras CL-001, CL-002 e CL-006.

## Matches detectados

Rodando `pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts PRD.md`:

| Linha:Col | Rule | Match textual | Severity |
|-----------|------|----------------|----------|
| 1309:153  | CL-001 | "passa em qualquer auditoria" | error |
| 1309:136  | CL-002 | "100% conforme" | error |
| 1309:213  | CL-006 | "impossível errar" | error |
| 1354:43   | CL-001 | "passam em qualquer auditoria" | error |

Todas correspondem a textos de marketing/wireframe dentro do PRD — **não** a citações meta do linter.

## Decisão

- Corrigir os textos de §16.7 e §17.1.3 sem alterar requisitos técnicos.
- Registrar a decisão em `adr/0018-prd-copy-claims-remediation.md`.
- Adicionar regressão permanente em `tools/copy-lint-prd.test.ts`.
- Manter `compliance/approved-claims.md` como draft até revisão jurídica humana do claim-set completo.

## Sugestões de reescrita

| Texto atual | Sugestão |
|-------------|----------|
| "100% conforme — passa em qualquer auditoria — impossível errar" | "cobertura das não conformidades listadas em §9, com trilha imutável; pré-auditoria automatizada antes da auditoria humana" |
| "passam em qualquer auditoria" | "atendem os bloqueios regulatórios automatizáveis declarados em §9" |

Sugestões alinhadas ao claim-set aprovado em `compliance/approved-claims.md`.

## Status

- [x] detectado automaticamente por copy-lint.
- [x] revisado por `copy-compliance` na spec `specs/0015-prd-copy-claims-remediation.md`.
- [x] parecer de `legal-counsel` registrado em `compliance/audits/legal/claim-prd-wireframe.md`.
- [x] correção preparada para PR com `product-governance` via CODEOWNERS/required-gates.
- [x] finding fechado após re-execução do linter retornar errors: 0 em `PRD.md`.

## Evidência de fechamento

- `pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts PRD.md`
- `pnpm exec tsx --test tools/copy-lint-prd.test.ts`
