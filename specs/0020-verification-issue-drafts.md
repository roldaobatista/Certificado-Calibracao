# Spec 0020 — Issue drafts automáticos da cascata de verificação

## Objetivo

Fechar a lacuna remanescente de P0-10 em que `tools/verification-cascade.ts` já detectava snapshot diff, mas ainda não gerava um artefato canônico para abrir issue automaticamente no GitHub.

## Escopo

- Estruturar `compliance/verification-log/issues/` com `README.md`, `_template.md` e `drafts/`.
- Fazer `tools/verification-cascade.ts` expor findings estruturados para `CASCADE-003`.
- Adicionar `buildVerificationIssueDrafts()` e `writeVerificationIssueDrafts()`.
- Adicionar o comando raiz `pnpm verification-cascade:issue-drafts`.
- Integrar o workflow `required-gates` para gerar drafts JSON e abrir issue real quando houver finding elegível.
- Ampliar `tools/compliance-structure-check.ts` para exigir a árvore canônica de issue drafts.

## Critérios de aceite

- Snapshot diff gera exatamente um draft determinístico por snapshot afetado.
- Repositório sem finding elegível não gera drafts.
- `pnpm verification-cascade:issue-drafts -- --write` grava Markdown em `compliance/verification-log/issues/drafts/`.
- O workflow `required-gates` tenta abrir issue real a partir do JSON dos drafts, sem duplicar título já aberto.
- A estrutura canônica adicional entra em `compliance-structure-check`.

## Fora de escopo

- Não fecha a issue automaticamente após a correção.
- Não cobre ainda gatilhos como `spec-review-flag` ou falta de parecer L5.
- Não substitui a futura bateria de 30 certificados canônicos em PDF/A.
