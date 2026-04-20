---
id: FINDING-2026-04-19-001
source: copy-lint (packages/copy-lint)
tool_version: 0.0.1
date_detected: 2026-04-19
status: open
severity: error
owner: copy-compliance
escalated_to: product-governance
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

- **Não corrigir imediatamente** nesta sessão de bootstrap — P0-5 visava validar o pipeline, e validou.
- **Corrigir na próxima sessão** de trabalho sobre copy/landing (parte da V1 ou spec dedicada).
- O CI (futuro) + hook `PreCommit` permanecem bloqueando — logo, ninguém consegue **alterar** o PRD sem consertar essas linhas junto, o que é o comportamento desejado.
- `PRD.md` é caso especial: alterações exigem aprovação de `product-governance` via CODEOWNERS. A correção desses claims deve vir como mudança revisada + ADR de convenção de copy.

## Sugestões de reescrita

| Texto atual | Sugestão |
|-------------|----------|
| "100% conforme — passa em qualquer auditoria — impossível errar" | "cobertura das não conformidades listadas em §9, com trilha imutável; pré-auditoria automatizada antes da auditoria humana" |
| "passam em qualquer auditoria" | "atendem os bloqueios regulatórios automatizáveis declarados em §9" |

Sugestões alinhadas ao claim-set aprovado em `compliance/approved-claims.md`.

## Status

- [x] detectado automaticamente por copy-lint.
- [ ] revisado por `copy-compliance` (agente aprovado conceitualmente; falta sessão de revisão).
- [ ] parecer de `legal-counsel` em `compliance/audits/legal/claim-prd-wireframe.md`.
- [ ] correção commitada com aprovação de `product-governance`.
- [ ] finding fechado após re-execução do linter retornar errors: 0 em `PRD.md`.
