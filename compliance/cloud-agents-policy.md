# compliance/cloud-agents-policy.md — Política de Tier 3 (cloud agents)

> **Owner:** `product-governance` + `lgpd-security`. Ratificação: `legal-counsel`.
> Espelha `harness/09-cloud-agents-policy.md`. Status P1-2 — `[ ] Proposto`.

## Status

- **Versão:** 0.1.0-bootstrap (2026-04-19).
- Implementação: cloud execution (Tier 3) só após V1 estabilizar.

## Princípios

1. **Allowlist explícita** — cloud agent só pode rodar tarefas de um conjunto fechado pré-aprovado.
2. **Blocklist dura** — nunca rodar em cloud: emissão oficial, assinatura, DB de produção, KMS.
3. **Fixtures sanitizadas** — dados reais nunca vão para cloud; apenas fixtures sintéticos com `organization_id` de teste.
4. **Provenance attestation** — cada execução cloud produz artefato assinado com SHA do repo + hash do prompt + output.

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

- `.claude/settings.json` e `.codex/config.toml` negam spawn de cloud task fora da allowlist.
- CI valida que PR gerado por cloud agent tem `provenance.json` assinado.
- `product-governance` revisa todo PR com flag `cloud-generated` antes de merge.

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
