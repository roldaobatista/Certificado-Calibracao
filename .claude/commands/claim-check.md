---
description: Roda copy-lint regulatório contra arquivo ou glob e orienta correção de claims
owner: copy-compliance
risk_level: high
required_commands: ["pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts $ARGUMENTS"]
---

# /claim-check

## Objetivo

Detectar claims regulatórios proibidos ou arriscados antes de merge, release ou publicação de copy comercial.

## Execução

```bash
pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts $ARGUMENTS
```

Se `$ARGUMENTS` estiver vazio, o CLI usa a cobertura padrão de `packages/copy-lint/src/rules.yaml`.

## Evidência

- Registrar saída completa do comando.
- Para cada finding `error`, anexar path, linha, regra `CL-*` e sugestão.
- Se houver claim novo aprovado, registrar parecer em `compliance/legal-opinions/` e atualizar `compliance/approved-claims.md`.

## Escalonamento

- `error` bloqueia commit, PR e release.
- Claim novo ou ambíguo escala para `legal-counsel` e `product-governance`.
- Correção textual em UI ou e-mail volta para `web-ui` após parecer.

## Referências

- `harness/06-copy-lint.md`
- `compliance/approved-claims.md`
- `packages/copy-lint/src/rules.yaml`
