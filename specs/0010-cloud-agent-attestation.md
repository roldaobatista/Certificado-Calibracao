# Spec 0010 — Gate de attestation para cloud agents Tier 3

## Objetivo

Implementar a primeira fatia funcional do P1-2: política executável de Tier 3 com provenance/attestation forte e bloqueio fail-closed para branches `cloud-agent/*`.

## Escopo

- Política canônica em `compliance/cloud-agents/policy.yaml`.
- Log humano em `compliance/cloud-agents-log.md`.
- Template de attestation em `compliance/cloud-agents/attestations/_template.yaml`.
- Template de incidente em `compliance/incidents/cloud-agent-attestation-failure-template.md`.
- Gate `tools/cloud-agents-policy-check.ts`.
- Testes em `tools/cloud-agents-policy-check.test.ts`.
- Integração em `pnpm check:all` e pre-commit.

## Critérios de aceite

- Política exige `status: enforced`.
- Allowlist e blocklist refletem `harness/09-cloud-agents-policy.md`.
- Mecanismos aceitos incluem SLSA Build Level 2+, Sigstore/cosign e GitHub Artifact Attestations.
- Mecanismos fracos como user-agent, autor de commit ou nome de branch são rejeitados.
- Branch `cloud-agent/*` sem attestation falha fechada.
- Branch `cloud-agent/*` tocando path bloqueado falha mesmo com attestation.
- Branch `cloud-agent/*` só passa com arquivos allowlisted e manifesto de attestation coerente com commit/issuer/verificador.

## Fora de escopo

- Não executa `gh attestation verify` nem `cosign verify-blob` localmente no `check:all`.
- Não integra labels reais do GitHub; esta fatia usa branch `cloud-agent/*` como sinal determinístico.
- Não libera uso de Tier 3 em produção sem CI criptográfico e revisão humana.
