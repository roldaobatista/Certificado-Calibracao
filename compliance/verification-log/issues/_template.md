---
issue_type: verification-cascade-snapshot-diff
status: open
severity: blocker
labels:
  - compliance
  - verification-cascade
  - snapshot-diff
  - blocker
---

# {{issue_title}}

## Contexto

- Código: {{finding_code}}
- Snapshot: {{snapshot_id}}
- Perfil: {{profile}}
- Manifesto: {{manifest_path}}
- Baseline: {{baseline_path}}
- Current: {{current_path}}
- Branch: {{branch}}
- Commit: {{commit_sha}}
- Workflow run: {{workflow_run}}

## Evidencia

- Baseline SHA-256: {{baseline_hash}}
- Current SHA-256: {{current_hash}}
- Hash esperado no manifesto: {{expected_hash}}
- Findings:
{{findings_list}}
- Comando local: `pnpm snapshot-diff-check`

## Reauditoria obrigatoria

- regulator
- product-governance
- qa-acceptance

## Fechamento

- ADR/PR de correção:
- Novo baseline aprovado:
- Issue GitHub vinculada:
