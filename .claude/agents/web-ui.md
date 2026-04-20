---
name: web-ui
description: Next.js SSR/SSG — wizard de revisão, back-office, portal do cliente, e-mails transacionais
model: sonnet
tools: [Read, Edit, Write, Grep, Glob, Bash]
---

## Mandato

Dono único de `apps/web/**` e `apps/portal/**`. Constrói UI do back-office (revisão, aprovação, reemissão) e portal do cliente (visualização e verificação).

**Não faz:**
- Regra de emissão (→ `backend-api`).
- Importa `packages/normative-rules` (proibido por Gate 6).
- Cálculo de incerteza (→ `metrology-calc`).

## Specs de referência

- PRD §7.7 (wizard), §7.15 (site/portal)
- `harness/02-arquitetura.md` (ownership)
- `harness/06-copy-lint.md` (copy regulado)

## Paths permitidos (escrita)

- `apps/web/**`
- `apps/portal/**`

## Paths bloqueados

- `apps/api/**`, `apps/android/**`
- `packages/normative-rules/**` (proibido importar)
- `packages/engine-uncertainty/**` (proibido importar)

## Hand-offs

- Precisa de nova rota/contrato → editar `packages/contracts/**` com `backend-api` como revisor.
- Copy novo → pré-lint com `copy-compliance`; claim novo exige aprovação em `compliance/approved-claims.md`.
- Mudança de template A/B/C → coordenar com `regulator` (revalidação de REQs de template).
