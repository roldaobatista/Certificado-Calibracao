#!/usr/bin/env bash
# PreCommit — P1-2: política Tier 3 com provenance/attestation.
# Owner: product-governance + lgpd-security. Referencia: tools/cloud-agents-policy-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/cloud-agents-policy\.md|compliance/cloud-agents/|compliance/cloud-agents-log\.md|compliance/incidents/cloud-agent-attestation-failure-template\.md|tools/cloud-agents-policy-check\.ts|tools/cloud-agents-policy-check\.test\.ts|harness/09-cloud-agents-policy\.md|specs/0010-cloud-agent-attestation\.md|adr/0013-cloud-agent-attestation-gate\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[cloud-agents-policy-check] sem arquivos P1-2 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[cloud-agents-policy-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[cloud-agents-policy-check] validando politica Tier 3..."
run_pnpm cloud-agents-policy-check
