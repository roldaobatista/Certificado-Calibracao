# Spec 0006 — Matriz de escalonamento e rito de desempate

## Objetivo

Implementar o P0-8 como gate executável para garantir que divergências entre agentes autoritativos tenham rito formal, tiebreaker designado e bloqueio fail-closed enquanto abertas.

## Escopo

- `compliance/escalations/README.md` documenta o registro canônico.
- `compliance/escalations/_template.md` define frontmatter e seções obrigatórias.
- `adr/0009-tiebreaker-designation.md` designa o Responsável Técnico do Produto.
- `tools/escalation-check.ts` valida estrutura e bloqueia escalations abertas.
- `pnpm escalation-check` entra em `pnpm check:all` e no pre-commit quando arquivos P0-8 são alterados.

## Critérios de aceite

- O gate falha se `README.md`, `_template.md` ou a ADR de tiebreaker estiverem ausentes.
- O gate falha se uma escalation real estiver com `status: open`.
- O gate falha se uma escalation real não declarar tipo D1-D9, agentes, caminhos afetados, SLA, owner, ADR de tiebreaker e timestamps ISO-8601.
- O gate falha se uma escalation resolvida não tiver resolução e assinatura com timestamp ISO-8601.
- O gate passa quando a governança canônica existe e todas as escalations versionadas estão resolvidas ou substituídas.

## Fora de escopo

- Não automatiza consenso entre agentes.
- Não decide mérito normativo, jurídico ou técnico.
- Não substitui parecer humano quando o próprio harness exige escalonamento.
