# STATUS — Checklist de correções P0/P1/P2

> Cada item aponta para o arquivo do `harness/` que contém a decisão detalhada. Marque `[x]` ao aprovar.

## P0 — Hard blockers

| ID | Correção | Arquivo | Status |
|----|----------|---------|--------|
| P0-1 | Backend `apps/api` como peça de 1ª classe + agente `backend-api` | [02-arquitetura.md](./02-arquitetura.md), [03-agentes.md](./03-agentes.md) | [ ] Proposto |
| P0-2 | Pipeline de normative package assinado e versionado | [04-compliance-pipeline.md](./04-compliance-pipeline.md) | [ ] Proposto |
| P0-3 | Dossiê formal de validação contínua | [04-compliance-pipeline.md](./04-compliance-pipeline.md) | [ ] Proposto |
| P0-4 | Hard gates de multitenancy e trilha imutável | [05-guardrails.md](./05-guardrails.md) | [ ] Proposto |
| P0-5 | Copy-lint regulatório | [06-copy-lint.md](./06-copy-lint.md) | [ ] Proposto |
| P0-6 | Agente `product-governance` + CODEOWNERS | [07-governance-gate.md](./07-governance-gate.md) | [ ] Proposto |
| P0-7 | Budgets mensuráveis (tokens, custo, paralelismo, retries) | [11-budgets.md](./11-budgets.md) | [ ] Proposto |
| P0-8 | Matriz de escalonamento e rito de desempate | [12-escalation-matrix.md](./12-escalation-matrix.md) | [ ] Proposto (revisado, +D8) |
| P0-9 | Runbooks de recuperação (KMS, hash-chain, WORM, normative package) | [13-runbooks-recovery.md](./13-runbooks-recovery.md) | [ ] Proposto |
| P0-10 | Cascata de verificação L0→L5 + propagação bidirecional | [14-verification-cascade.md](./14-verification-cascade.md) | [ ] Proposto (revisado, L5 inclui 3 auditores) |
| P0-11 | Redundância, loops e auto-consistência (property tests, flake gate, dupla checagem) | [15-redundancy-and-loops.md](./15-redundancy-and-loops.md) | [ ] Proposto |
| P0-12 | 3 agentes auditores externos substituem humanos contratados (metrology-auditor, legal-counsel, senior-reviewer) | [16-agentes-auditores-externos.md](./16-agentes-auditores-externos.md) | [ ] Proposto |
| P0-13 | Operação dual Claude Code + Codex CLI com `AGENTS.md` canônico | [17-multi-tooling.md](./17-multi-tooling.md) | [~] Em implementação (bootstrap Camada 1: `.claude/` + `.codex/` espelhados; falta `tools/sync-agents.ts` e CI drift detection) |

## P1 — Estrutural

| ID | Correção | Arquivo | Status |
|----|----------|---------|--------|
| P1-1 | Simulador determinístico de sync/conflito + fila de revisão humana | [08-sync-simulator.md](./08-sync-simulator.md) | [ ] Proposto (revisado) |
| P1-2 | Política de Tier 3 com provenance/attestation (SLSA/sigstore) | [09-cloud-agents-policy.md](./09-cloud-agents-policy.md) | [ ] Proposto (revisado) |
| P1-3 | Diretório `/compliance/` canônico | [02-arquitetura.md](./02-arquitetura.md) | [~] Em implementação (árvore canônica criada no bootstrap; scaffolds de `approved-claims.md`, `guardrails.md`, `cloud-agents-policy.md` em v0.1.0-draft) |
| P1-4 | Roadmap em fatias verticais V1–V5 | [10-roadmap.md](./10-roadmap.md) | [ ] Proposto |

## P2 — Refinamento

| ID | Correção | Onde | Status |
|----|----------|------|--------|
| P2-1 | Nomenclatura de agentes (frontmatter padrão) | [03-agentes.md](./03-agentes.md) | [ ] Proposto |
| P2-2 | Slash-commands regulatórios (`/spec-norm-diff`, `/ac-evidence`, `/claim-check`, `/tenant-fuzz`, `/emit-cert-dry`) | pendente | [ ] Não iniciado |
| P2-3 | Dashboard de observabilidade do harness | pendente | [ ] Não iniciado |
| P2-4 | Reescrever texto do Tier 3 no `HARNESS_DESIGN.md` raiz | — | [ ] Não iniciado |

## Legenda de status

- `[ ] Proposto` — decisão escrita neste diretório, aguarda revisão humana.
- `[x] Aprovado` — revisado e aceito; pode ser implementado.
- `[~] Em implementação` — aprovado, código sendo criado.
- `[✓] Implementado` — código em produção + dossiê arquivado.
- `[!] Rejeitado` — revisor vetou; motivo em comentário.

## Fluxo de aprovação

1. Revisor lê o arquivo apontado.
2. Se ok → troca `[ ] Proposto` por `[x] Aprovado` + assinatura (`— nome/data`).
3. Se pedir ajuste → comenta no arquivo, mantém status em `Proposto`.
4. Quando **todos os P0** estiverem `Aprovado`, `HARNESS_DESIGN.md` raiz é reescrito a partir deste diretório.
5. P1 segue mesmo fluxo; P2 pode ser deferido para pós-V1.

## Dependências de implementação

```
P0-1 (backend) ─┬─► P0-2 (normative package) ─► P0-3 (dossiê) ─► P0-9 (runbooks)
                ├─► P0-4 (guardrails) ─► P0-9 (runbooks)
                └─► P0-6 (governance gate) ─► P0-8 (escalation matrix)

P0-3 (dossiê) ─► P0-10 (cascata L0→L5) ─► P0-11 (redundância/loops)

P0-5 (copy-lint) — independente, pode rodar em paralelo
P0-7 (budgets) — transversal, ativado já no bootstrap do harness

P1-1, P1-2 — dependem de P0-1 estar em pé
P1-3 — ativado junto com P0-3
P1-4 — deve ser aprovado antes de qualquer V1 começar
```

## Última atualização

- `2026-04-19` — proposta inicial criada em `harness/`.
- `2026-04-19` — emendas P0-7, P0-8, P0-9 adicionadas após 2ª rodada de revisão; P1-1 e P1-2 revisados.
- `2026-04-19` — emendas P0-10 (cascata L0→L5) e P0-11 (redundância/loops) adicionadas após 3ª rodada; D8 adicionado a P0-8; Gate 7 adicionado a P0-4.
- `2026-04-19` — emenda P0-12 adicionada após decisão de operar sem especialistas humanos contratados: 3 agentes auditores (metrology-auditor, legal-counsel, senior-reviewer) substituem humanos em 1ª linha; D9 adicionado a P0-8; L5 em P0-10 atualizado; checklist de P0-6 inclui 3 pareceres.
- `2026-04-19` — emenda P0-13 adicionada: operação dual Claude Code + Codex CLI com `AGENTS.md` canônico na raiz; `.claude/` e `.codex/` são espelhos gerados; roteamento por tipo de tarefa documentado.
- `2026-04-19` — **ADRs 0001, 0002, 0003 aprovados** pelo usuário: Fastify + TS; sync event-log + idempotency + fila humana; Hostinger VPS KVM 4 + Backblaze B2 Object Lock + AWS KMS sa-east-1 + Grafana/Axiom. Camada 2 (scaffold `apps/api`) destravada.
- `2026-04-19` — produto renomeado **Kalibrium → Aferê** (placeholder virou nome oficial; slug técnico `afere`).
- `2026-04-19` — **bootstrap Camada 1 executado**: `CLAUDE.md` raiz; árvore do monorepo (`apps/`, `packages/`, `evals/`, `compliance/`, `specs/`, `adr/`, `infra/`) com 34 READMEs; 13 subagentes em `.claude/agents/*.md` + espelho em `.codex/agents/*.toml`; `.claude/settings.json` + `.codex/config.toml` com hooks, allowlist, MCPs e budgets; 6 slash-commands (`spec-new`, `ac-check`, `claim-check`, `emit-cert-dry`, `release-norm`, `tenant-fuzz`); 9 hooks Claude + 4 hooks Codex (stubs); scaffolds `compliance/approved-claims.md`, `compliance/guardrails.md`, `compliance/cloud-agents-policy.md`. P0-13 e P1-3 marcados `[~] Em implementação`; demais P0 continuam `[ ] Proposto` (exigem código de aplicação — Camadas seguintes).
