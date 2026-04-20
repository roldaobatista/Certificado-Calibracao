# ADR 0013 — Gate de attestation para cloud agents Tier 3

Status: Aprovado

Data: 2026-04-20

## Contexto

O P1-2 exige política de Tier 3 com provenance/attestation forte. A política existia em Markdown, mas sem fonte executável nem gate que falhasse fechado para cloud agents sem prova de origem.

## Decisão

Criar `compliance/cloud-agents/policy.yaml` como fonte executável e `tools/cloud-agents-policy-check.ts` como gate:

- `check` valida política, templates, log, allowlist, blocklist e mecanismos aceitos;
- `pr` avalia branch `cloud-agent/*`, paths alterados e manifesto de attestation;
- sem attestation, path fora da allowlist ou path bloqueado resulta em erro;
- mecanismos fracos são explicitamente rejeitados;
- o gate entra em `pnpm check:all` e no pre-commit.

## Consequências

Tier 3 deixa de ser apenas orientação documental e passa a ter enforcement local e em CI. A política continua fail-closed: se a plataforma não produzir attestation verificável, ela não pode abrir PR cloud-agent.

## Limitação

Esta fatia valida o manifesto e a política. A verificação criptográfica real depende do CI executar `gh attestation verify` ou `cosign verify-blob` contra o commit/artefato antes de registrar a attestation.
