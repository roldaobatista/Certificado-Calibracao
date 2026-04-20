# ADR 0017 — Texto de Tier 3 no HARNESS_DESIGN.md raiz

Status: Aprovado

Data: 2026-04-20

## Contexto

O `HARNESS_DESIGN.md` raiz é o design histórico do harness. Ele ainda descrevia Tier 3 como "drain de backlog overnight", uma formulação ampla demais para um produto regulado com LGPD, trilha auditável e emissão metrológica.

P1-2 já materializou a política de cloud agents em `harness/09-cloud-agents-policy.md` e `compliance/cloud-agents/policy.yaml`, com allowlist, blocklist e attestation forte. P2-4 exige alinhar o texto raiz com essa política sem reescrever todo o documento histórico.

## Decisão

Atualizar apenas a linha de Tier 3 em `HARNESS_DESIGN.md` §2.1 e adicionar uma nota curta deixando explícito que:

- Tier 3 só cobre tarefas low-risk aprovadas pela política P1-2;
- attestation verificável é obrigatória;
- revisão humana e `product-governance` são obrigatórios;
- sem política e attestation válidas, o uso falha fechado.

Adicionar `tools/harness-design-tier3-check.ts` para impedir regressão à formulação antiga.

## Consequências

O design histórico passa a apontar para a política executável atual, reduzindo risco de alguém interpretar Tier 3 como automação ampla de backlog. O gate entra em `check:all` e no pre-commit.

## Limitação

Esta decisão não torna Tier 3 plenamente operacional. A verificação criptográfica real continua dependente de CI com `gh attestation verify` ou `cosign verify-blob`, como definido em P1-2.
