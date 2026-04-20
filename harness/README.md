# harness/ — Design operacional do ambiente de desenvolvimento Kalibrium

> Pasta de trabalho para conferência e correção do harness multi-agente proposto.
> Cada arquivo aqui é **estratégico**: aborda uma decisão que, se errada, compromete o produto regulado.

## Como ler

A ordem dos arquivos reflete prioridade de revisão — quem revisar deve começar em `01` e descer.

| # | Arquivo | Tema | Prioridade |
|---|---------|------|------------|
| 01 | [principios.md](./01-principios.md) | Princípios não-negociáveis | — |
| 02 | [arquitetura.md](./02-arquitetura.md) | Tiers, monorepo (com `apps/api`), MCP | **P0** |
| 03 | [agentes.md](./03-agentes.md) | Matriz dos 10 agentes, escopo, paths | **P0** |
| 04 | [compliance-pipeline.md](./04-compliance-pipeline.md) | Normative package + validation dossier | **P0** |
| 05 | [guardrails.md](./05-guardrails.md) | Multitenancy, RLS, audit log, WORM | **P0** |
| 06 | [copy-lint.md](./06-copy-lint.md) | Claims regulatórios em copy | **P0** |
| 07 | [governance-gate.md](./07-governance-gate.md) | Agente `product-governance` + CODEOWNERS | **P0** |
| 08 | [sync-simulator.md](./08-sync-simulator.md) | Simulador determinístico offline + fila de revisão humana | **P1** |
| 09 | [cloud-agents-policy.md](./09-cloud-agents-policy.md) | Política de Tier 3 com provenance/attestation | **P1** |
| 10 | [roadmap.md](./10-roadmap.md) | Fatias verticais V1–V5 | **P1** |
| 11 | [budgets.md](./11-budgets.md) | Budgets mensuráveis + circuit breakers | **P0** |
| 12 | [escalation-matrix.md](./12-escalation-matrix.md) | Rito de desempate entre agentes autoritativos | **P0** |
| 13 | [runbooks-recovery.md](./13-runbooks-recovery.md) | Runbooks KMS / hash-chain / WORM / normative package | **P0** |
| 14 | [verification-cascade.md](./14-verification-cascade.md) | Cascata L0 (épico) → L5 (release) + propagação bidirecional | **P0** |
| 15 | [redundancy-and-loops.md](./15-redundancy-and-loops.md) | Property tests, flake gate, dupla checagem, self-consistency | **P0** |
| 16 | [agentes-auditores-externos.md](./16-agentes-auditores-externos.md) | 3 agentes auditores (metrology-auditor, legal-counsel, senior-reviewer) substituem humanos contratados | **P0** |
| 17 | [multi-tooling.md](./17-multi-tooling.md) | Operação dual Claude Code + Codex CLI com `AGENTS.md` canônico | **P0** |
| — | [STATUS.md](./STATUS.md) | Checklist de correções P0/P1/P2 | — |

## Relação com outros documentos

- **Fonte de requisitos**: `../PRD.md` (v1.8) e `../ANALISE_CONSOLIDADA_PRD.md`.
- **Histórico do design original**: `../HARNESS_DESIGN.md` (não é reescrito — este diretório representa a evolução corrigida).
- **Plano de correções**: `../HARNESS_PATCHPLAN.md` (origem deste diretório).

## Fluxo de revisão

1. Revisor lê `01` → `17` em ordem.
2. Comentários inline (ou PR review) em cada arquivo.
3. Mudança aprovada atualiza o arquivo + marca o item em `STATUS.md`.
4. Quando todos os P0 estiverem verdes em `STATUS.md`, o `HARNESS_DESIGN.md` raiz é reescrito a partir daqui como versão consolidada.

## Não-objetivos

- Este diretório **não é código**. É decisão de produto/arquitetura sobre *como* o código será construído.
- Nenhum arquivo aqui substitui spec de feature (que vai para `specs/` quando o bootstrap começar).
