# 0001 — Harness de compliance executável

## Contexto

Aferê precisa transformar regras do harness em gates executáveis antes das fatias de produto regulado. Esta spec cobre a primeira implementação dos gates de multitenancy, trilha imutável, WORM, sync de agentes e dossiê de validação.

## Escopo

- Validar SQL e policies RLS contra ausência de `organization_id`.
- Executar smoke e fuzz de isolamento RLS em Postgres real.
- Verificar hash-chain de audit log em artefatos JSONL.
- Bloquear IaC de buckets regulatórios sem WORM/Object Lock.
- Sincronizar agentes Codex a partir dos agentes Claude canônicos.
- Gerar dossiê de validação com requisitos, matriz de rastreabilidade e relatório de cobertura.

## Fora de escopo

- Implementar domínio completo de emissão de certificados.
- Substituir auditoria humana final da organização.
- Assinar pacotes normativos com KMS real.
- Criar RBAC aplicacional antes do backend de autenticação existir.

## Requisitos

- REQ-PRD-13-13-RLS-ISOLATION
- REQ-PRD-13-18-VALIDATION-DOSSIER
- REQ-PRD-13-19-TENANT-SQL-LINTER
- REQ-PRD-13-19-AUDIT-HASH-CHAIN
- REQ-PRD-13-19-WORM-STORAGE-CHECK
- REQ-HARNESS-P0-13-AGENT-SYNC

## Critérios de aceite

- `pnpm tenant-lint` retorna erro para SQL multitenant sem `organization_id`.
- `pnpm test:tenancy` executa smoke e fuzz cross-tenant contra Postgres.
- `pnpm audit-chain:verify <audit.jsonl>` retorna erro quando payload ou `prevHash` diverge.
- `pnpm worm-check` retorna erro para buckets regulatórios Terraform sem lock imutável.
- `pnpm sync:agents:check` falha quando `.codex/agents/*.toml` diverge de `.claude/agents/*.md`.
- `pnpm validation-dossier:check` falha se `requirements.yaml` ou `traceability-matrix.yaml` estiver inválido ou desatualizado.

## Evidência

Evidência de execução fica em `compliance/validation-dossier/evidence/<REQ-id>/` e o resumo consolidado é gerado em `compliance/validation-dossier/coverage-report.md`.
