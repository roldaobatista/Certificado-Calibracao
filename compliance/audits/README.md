# compliance/audits/ — Pareceres dos 3 auditores

Subpastas por auditor: `metrology/`, `legal/`, `code/`. Frontmatter padronizado em `harness/16-agentes-auditores-externos.md`.

## Gate

`pnpm external-auditors-gate` valida agentes, permissões, templates e casos-limite. Para release, usar:

```bash
pnpm external-auditors-gate release --release <versao>
```

Esse subcomando exige os três pareceres L5 e bloqueia `FAIL` ou `blockers` não vazios.
