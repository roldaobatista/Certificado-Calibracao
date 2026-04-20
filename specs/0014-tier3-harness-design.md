# Spec 0014 — Texto de Tier 3 no HARNESS_DESIGN.md raiz

## Objetivo

Implementar P2-4: atualizar o texto histórico de Tier 3 no `HARNESS_DESIGN.md` raiz para refletir a política P1-2 de cloud agents com allowlist, blocklist, attestation forte e revisão humana.

## Escopo

- Alterar apenas o trecho de Tier 3 em `HARNESS_DESIGN.md` §2.1.
- Criar gate `tools/harness-design-tier3-check.ts`.
- Cobrir o gate com `tools/harness-design-tier3-check.test.ts`.
- Integrar o gate em `pnpm check:all` e no pre-commit.
- Atualizar `harness/STATUS.md` e o dashboard gerado.

## Critérios de aceite

- O texto de Tier 3 deixa de apresentar cloud agents como "drain de backlog overnight" sem qualificação.
- O novo texto restringe Tier 3 a tarefas low-risk aprovadas pela política P1-2.
- O texto exige attestation verificável, revisão humana e `product-governance`.
- O texto aponta para `harness/09-cloud-agents-policy.md` e `compliance/cloud-agents/policy.yaml`.
- O gate falha para a formulação antiga e passa para a formulação restrita.

## Fora de escopo

- Não altera a política P1-2 nem a allowlist/blocklist executável.
- Não libera cloud agents em produção além do que já está definido em P1-2.
- Não reescreve todo o `HARNESS_DESIGN.md`; o arquivo continua como histórico parcialmente corrigido.
