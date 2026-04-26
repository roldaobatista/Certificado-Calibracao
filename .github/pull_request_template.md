## Governance checklist (product-governance only)

- [ ] Matriz requisito->spec->teste->evidencia atualizada
- [ ] Pacote normativo impactado? Se sim, PR de draft criado em compliance/normative-packages/drafts/
- [ ] Copy-lint verde (sem claims proibidos)
- [ ] Guardrails de multitenancy verdes (gates 1-7)
- [ ] RLS tests passam em >=2 tenants sinteticos
- [ ] Audit hash-chain integra
- [ ] Release notes regulatorias preenchidas se o PR afeta emissao, audit ou pacote normativo
- [ ] Cloud agents: se PR veio de cloud agent, tocou apenas paths da allowlist?

## Pareceres dos 3 auditores externos

> **Nota:** Os 3 auditores abaixo são agentes automatizados de pré-auditoria. Eles **não substituem** auditoria humana externa contratada, que continua sendo obrigatória nos 5 casos-limite (auditoria CGCRE real, processo judicial, incidente LGPD, acidente metrológico, reclamação em órgão regulador).

- [ ] metrology-auditor: parecer PASS em compliance/audits/metrology/<release>.md
- [ ] legal-counsel: parecer PASS em compliance/audits/legal/<release>.md
- [ ] senior-reviewer: parecer PASS em compliance/audits/code/<release>.md ou compliance/audits/code/pr-<n>.md
- [ ] Nenhum dos 3 auditores emitiu BLOQUEIO nao resolvido

## Risco regulatorio (self-assessment)

- [ ] Este PR pode alterar comportamento de emissao? Se sim, descreva.
- [ ] Este PR pode alterar o que e gravado no audit log?
- [ ] Este PR introduz ou altera claim comercial?
- [ ] Algum dos 5 casos-limite aplicavel? Se sim, escalar ao usuario
