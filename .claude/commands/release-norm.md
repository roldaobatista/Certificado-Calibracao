---
description: Prepara release-norm consolidando pareceres dos 3 auditores + executores
---

Orquestra o fechamento de release `$ARGUMENTS` (ex.: `v1.0.0`) consolidando a cascata L5.

Sequência obrigatória:

1. `qa-acceptance` confirma L4: full regression, snapshot-diff, property tests verdes.
2. `metrology-auditor` emite parecer em `compliance/audits/metrology/release-$ARGUMENTS.md`.
3. `legal-counsel` emite parecer em `compliance/audits/legal/release-$ARGUMENTS.md`.
4. `senior-reviewer` emite parecer em `compliance/audits/code/release-$ARGUMENTS.md`.
5. Este comando consolida os 3 pareceres + pareceres de `regulator`/`lgpd-security`/executores em `compliance/release-norm/$ARGUMENTS.md` com frontmatter:

```yaml
---
release: $ARGUMENTS
date: <ISO>
verdict: PASS | FAIL
auditors:
  metrology: PASS | FAIL | PASS_WITH_FINDINGS
  legal: PASS | FAIL | PASS_WITH_FINDINGS
  code: PASS | FAIL | PASS_WITH_FINDINGS
ac_coverage: <%>
normative_package_hash: <sha>
signed_by: product-governance
---
```

6. Se qualquer auditor BLOQUEIA → release não sai; abre issue; executor corrige; re-auditoria obrigatória.
7. Se todos PASS → tag git + `product-governance` assina release-norm.

Ver `harness/07-governance-gate.md` e `harness/16-agentes-auditores-externos.md` (fluxo de release).
