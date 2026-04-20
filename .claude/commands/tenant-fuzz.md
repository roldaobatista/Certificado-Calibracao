---
description: Executa fuzz cross-tenant para detectar vazamento entre organizações
owner: qa-acceptance
risk_level: blocker
required_commands: ["pnpm test:tenancy"]
---

# /tenant-fuzz

## Objetivo

Validar Gate 5 de multitenancy com smoke RLS e fuzz determinístico contra leituras e escritas cross-tenant.

## Execução

```bash
pnpm test:tenancy
```

Se `$ARGUMENTS` indicar uma área (`emission`, `audit` ou `sync`), registrar o filtro na evidência mesmo quando a suíte atual ainda roda completa.

## Evidência

- Registrar saída de `pnpm test:rls` e `pnpm test:fuzz`.
- Confirmar quantidade de seeds executados.
- Arquivar finding em `compliance/validation-dossier/findings/` se qualquer payload atravessar tenant.

## Escalonamento

- Qualquer falha bloqueia emissão e release.
- Vazamento RLS escala para `db-schema`.
- Vazamento por rota/API escala para `backend-api`.
- Regressão de cobertura escala para `qa-acceptance` e `product-governance`.

## Referências

- `harness/05-guardrails.md`
- `evals/tenancy/rls/rls-smoke.test.ts`
- `evals/tenancy/fuzz/cross-tenant-fuzz.test.ts`
