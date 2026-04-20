---
description: Gera diff semântico entre draft normativo e pacote aprovado vigente
owner: regulator
risk_level: high
required_commands: ["git diff --no-index -- compliance/normative-packages/approved/2026-04-20-baseline-v0.1.0/package.yaml $ARGUMENTS", "pnpm test:tools"]
---

# /spec-norm-diff

## Objetivo

Comparar um draft normativo com o pacote aprovado vigente e identificar impacto em regras do PRD §9, testes regulatórios e dossiê.

## Execução

```bash
git diff --no-index -- compliance/normative-packages/approved/2026-04-20-baseline-v0.1.0/package.yaml $ARGUMENTS
pnpm test:tools
```

`$ARGUMENTS` deve apontar para um draft em `compliance/normative-packages/drafts/<YYYY-MM-DD>-<slug>.yaml`.

## Evidência

- Registrar diff completo.
- Listar regras §9 afetadas.
- Listar testes `evals/regulatory/**` ou planned tests afetados.
- Registrar pacote baseline comparado e hash de `package.sha256`.

## Escalonamento

- Draft sem fonte normativa bloqueia PR.
- Mudança em regra blocker escala para `metrology-auditor` e `product-governance`.
- Divergência jurídica ou claim público escala para `legal-counsel`.

## Referências

- `harness/04-compliance-pipeline.md`
- `packages/normative-rules/src/package.ts`
- `compliance/normative-packages/releases/manifest.yaml`
