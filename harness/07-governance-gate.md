# 07 — Agente `product-governance` + gate de release

> **P0-6**: cria autoridade transversal de bloqueio por violação de política regulatória.

## Mandato

Agente **sem permissão de escrita em código de aplicação**. Só escreve em:
- `compliance/release-norm/**`
- PR reviews (comentários e approvals)
- ADRs específicos de governança

Atua como gate final de qualquer merge que toque áreas regulatoriamente sensíveis.

## Autoridade via CODEOWNERS

Arquivo `.github/CODEOWNERS` (ou equivalente):

```
# Áreas que exigem aprovação do product-governance
apps/api/src/domain/emission/**       @product-governance
apps/api/src/domain/audit/**          @product-governance @lgpd-security
packages/engine-uncertainty/**        @product-governance @metrology-calc
packages/normative-rules/**           @product-governance @regulator
packages/audit-log/**                 @product-governance @db-schema @lgpd-security
compliance/**                         @product-governance
PRD.md                                @product-governance
```

Branch protection exige aprovação dos CODEOWNERS antes do merge.

## Checklist de PR (gerado automaticamente)

Template `.github/pull_request_template.md`:

```markdown
## Governance checklist (product-governance only)

- [ ] Matriz requisito→spec→teste→evidência atualizada
- [ ] Pacote normativo impactado? Se sim, PR de draft criado em compliance/normative-packages/drafts/
- [ ] Copy-lint verde (sem claims proibidos)
- [ ] Guardrails de multitenancy verdes (gates 1-7)
- [ ] RLS tests passam em ≥2 tenants sintéticos
- [ ] Audit hash-chain íntegra
- [ ] Release notes regulatórias preenchidas se o PR afeta emissão, audit ou pacote normativo
- [ ] Cloud agents: se PR veio de cloud agent, tocou apenas paths da allowlist?

## Pareceres dos 3 auditores externos (ver `16-agentes-auditores-externos.md`)

- [ ] `metrology-auditor`: parecer PASS em `compliance/audits/metrology/<release>.md`
- [ ] `legal-counsel`: parecer PASS em `compliance/audits/legal/<release>.md`
- [ ] `senior-reviewer`: parecer PASS em `compliance/audits/code/<release>.md` (ou `compliance/audits/code/pr-<n>.md`)
- [ ] Nenhum dos 3 auditores emitiu BLOQUEIO não resolvido

## Risco regulatório (self-assessment)

- [ ] Este PR pode alterar comportamento de emissão? Se sim, descreva.
- [ ] Este PR pode alterar o que é gravado no audit log?
- [ ] Este PR introduz ou altera claim comercial?
- [ ] Algum dos 5 casos-limite aplicável? (auditoria CGCRE real, processo judicial, incidente LGPD, acidente metrológico, reclamação em órgão regulador) — se sim, escalar ao usuário
```

## Output: release-norm

Cada release cria `compliance/release-norm/<semver>.md`:

```markdown
# Release v<semver> — Veredito de governança

- Data: <ISO-8601>
- Revisor: product-governance
- Escopo: <resumo>

## Checklist
- [x] Pacote normativo vigente: <hash>
- [x] Guardrails verdes: [lista]
- [x] Copy-lint verde
- [x] Dossiê de validação: <cobertura %>

## Riscos aceitos
- <lista, se houver>

## Aprovado para release: SIM / NÃO
Assinatura do revisor: <nome> — <timestamp>
```

## Relação com outros agentes

**Executores:**
- **`regulator`** interpreta; **`product-governance`** bloqueia.
- **`qa-acceptance`** roda testes; **`product-governance`** audita cobertura.
- **`copy-compliance`** sinaliza claim; **`product-governance`** aprova exceção.
- **`lgpd-security`** avalia risco de dados; **`product-governance`** consolida parecer.

**Auditores externos** (parecer vinculante no release-norm):
- **`metrology-auditor`** emite parecer normativo; **`product-governance`** consolida e bloqueia release se FAIL.
- **`legal-counsel`** emite parecer jurídico; **`product-governance`** consolida e bloqueia release se FAIL.
- **`senior-reviewer`** emite review crítico; **`product-governance`** consolida e bloqueia release se FAIL.

## Nunca fazer

- `product-governance` **não escreve código de produto**. Se precisar, escala para o agente dono.
- `product-governance` **não define política sozinho**. Política vive em `compliance/` e é versionada.
- `product-governance` **não dá bypass de gate automático**. Se um gate precisa ser relaxado, abre-se ADR explícita.

## Modelo recomendado

Opus — precisa ler contexto amplo (PRD + specs + release notes + checklists) e sintetizar parecer preciso.
