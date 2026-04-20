---
description: Roda copy-lint regulatório contra arquivo/glob; sugere reescrita via copy-compliance para cada match
---

Executa `@afere/copy-lint` contra `$ARGUMENTS` (paths relativos ou globs).

## Execução

Rode este comando no terminal e me mostre o resultado:

```bash
pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts $ARGUMENTS
```

Se `$ARGUMENTS` estiver vazio, o CLI varre a cobertura padrão declarada em `packages/copy-lint/src/rules.yaml` (apps/web, apps/portal, e-mails, compliance, specs, adr, README.md, PRD.md, ideia.md, AGENTS.md, CLAUDE.md).

## Interpretação

- Exit 0 + `errors: 0` → sem claims proibidos; warnings podem existir sem bloqueio.
- Exit 1 → pelo menos um claim proibido (severity=error). **Delegar `copy-compliance`** para propor alternativa dentro do claim-set aprovado em `compliance/approved-claims.md`.
- Cada finding traz `sugestão:` com redação defensável já pensada.

## Fluxo após detecção

1. Para cada finding: verificar se a sugestão cabe no contexto ou se é caso novo.
2. Se caso **novo** (categoria de claim não listada): escalar para `legal-counsel` (parecer em `compliance/audits/legal/claim-<slug>.md`) + `product-governance` antes de aprovar.
3. Se claim é **aprovado pós-revisão**: adicionar a `compliance/approved-claims.md` + registrar parecer datado em `compliance/legal-opinions/`.
4. Commit: PreCommit hook `.claude/hooks/copy-lint.sh` roda automaticamente contra delta e bloqueia se algum error sobrou.

Referências: `harness/06-copy-lint.md`, `compliance/approved-claims.md`, `packages/copy-lint/src/rules.yaml`.
