# Escalations

Registro canônico de divergências D1-D9 descritas em `harness/12-escalation-matrix.md`.

## Regra de merge

Entradas com `status: open` não podem ser mergeadas. A abertura de escalation deve acontecer no PR ou branch de trabalho; o merge só é permitido quando a entrada estiver resolvida, assinada e com `resolved_at`.

## Como abrir uma escalation

1. Copiar `_template.md` para `compliance/escalations/<YYYY-MM-DD>-<slug>.md`.
2. Preencher frontmatter, posições dos agentes, impacto e caminhos afetados.
3. Manter `status: open` enquanto houver divergência.
4. Ao resolver, trocar para `status: resolved`, preencher `resolved_at`, `## Resolução`, `## Assinaturas` e `## Aprendizado`.
5. Rodar `pnpm escalation-check` antes do merge.

## Status permitidos no repositório principal

- `resolved`: divergência decidida e assinada.
- `superseded`: substituída por outra escalation ou ADR posterior, com justificativa em `## Resolução`.

`open` é deliberadamente bloqueado pelo gate para preservar fail-closed.
