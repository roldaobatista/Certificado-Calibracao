# compliance/cloud-agents-policy.md — Política de Tier 3 (cloud agents)

> **Owner:** `product-governance` + `lgpd-security`. Ratificação: `legal-counsel`.
> Espelha `harness/09-cloud-agents-policy.md`. Status P1-2 — `[~] Em implementação`.

## Status

- **Versão:** 0.2.0-enforced (2026-04-20).
- **Fonte executável:** `compliance/cloud-agents/policy.yaml`.
- **Gate:** `pnpm cloud-agents-policy-check`.
- Implementação: cloud execution (Tier 3) continua proibida fora da allowlist e sem attestation verificável.

## Princípios

1. **Allowlist explícita** — cloud agent só pode rodar tarefas de um conjunto fechado pré-aprovado.
2. **Blocklist dura** — nunca rodar em cloud: emissão oficial, assinatura, DB de produção, KMS.
3. **Fixtures sanitizadas** — dados reais nunca vão para cloud; apenas fixtures sintéticos com `organization_id` de teste.
4. **Provenance attestation** — cada execução cloud produz artefato assinado com SHA do repo + hash do prompt + output.
5. **Fail-closed sem attestation** — user-agent, autor de commit, nome de branch ou metadata fraca não liberam PR.

## Tarefas permitidas em cloud

- Refactor mecânico em paths não-críticos (`apps/web/*` excluindo áreas blocker).
- Testes em lote em `evals/` com fixtures sanitizadas.
- Geração de fixtures de teste.
- Análise estática de repo (lint, tipo) sem escrita.
- Geração de documentação auxiliar em `docs/`.

## Tarefas bloqueadas em cloud

- Mudança em `apps/api/src/domain/emission/**`.
- Mudança em `apps/api/src/domain/audit/**`.
- Mudança em `packages/engine-uncertainty/**`.
- Mudança em `packages/normative-rules/**`.
- Mudança em `packages/audit-log/**` ou `packages/db/**`.
- Mudança em `compliance/**`.
- Acesso a credenciais de produção, KMS, chaves de assinatura.
- Acesso a dados de tenant real.

## Enforcement

- `compliance/cloud-agents/policy.yaml` declara allowlist, blocklist, mecanismos aceitos e issuers permitidos.
- `pnpm cloud-agents-policy-check` valida a política, templates, log e fallback fail-closed.
- `cloud-agents-policy-check pr --branch cloud-agent/<slug> --attestation <manifest>` bloqueia PR sem attestation ou com path fora da allowlist.
- CI deve executar `gh attestation verify` ou `cosign verify-blob` antes de registrar o manifesto em `compliance/cloud-agents/attestations/`.
- `product-governance` revisa todo PR com flag `cloud-generated` antes de merge.

## Attestation aceita

- `slsa-build-level-2-plus`
- `sigstore-cosign`
- `github-artifact-attestations`

O manifesto de attestation deve registrar `subject_commit`, `issuer`, `identity`, `predicate_type`, `verified_at` e o comando verificador executado. O gate local valida o manifesto; a prova criptográfica continua sendo o retorno bem-sucedido de `gh attestation verify` ou `cosign verify-blob` no CI.

## Budgets (Tier 3)

| Métrica | Soft | Hard |
|---------|------|------|
| Custo por cloud task | $3 | $5 |
| Timeout de cloud task | 90 min | 120 min |
| Cloud tasks por dia | 10 | 20 |

## Incidente

Detecção de cloud task tocando path bloqueado:
1. Aborta execução.
2. Abre issue blocker.
3. Revoga credencial cloud da sessão.
4. `product-governance` investiga + ADR explicando causa + correção.
5. Re-habilitação só após fix + aprovação humana.
