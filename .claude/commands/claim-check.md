---
description: Roda copy-lint regulatório contra arquivo/glob e sugere reescrita via copy-compliance
---

Roda `packages/copy-lint` contra `$ARGUMENTS` (arquivo ou glob) para detectar claims proibidos.

Escopo padrão se `$ARGUMENTS` vazio: `apps/web/**/*.{tsx,md,mdx}`, `apps/portal/**`, templates de e-mail em `apps/api/templates/emails/**`, `README.md`, `PRD.md`, `ideia.md`, `compliance/**`.

Passos:

1. Carrega regex proibidas de `packages/copy-lint/rules.yaml`.
2. Varre paths-alvo; lista matches com arquivo:linha, padrão e severidade.
3. Para cada match, delega a `copy-compliance` para sugerir alternativa dentro do claim-set aprovado em `compliance/approved-claims.md`.
4. Se claim for novo (não listado), escala para `legal-counsel` + `product-governance`.

Severidade `error` bloqueia commit. `warning` exige revisão jurídica documentada.

Ver `harness/06-copy-lint.md` e `compliance/approved-claims.md`.
