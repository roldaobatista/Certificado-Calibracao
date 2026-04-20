#!/usr/bin/env bash
# PreCommit — P0-12: auditores externos e pareceres L5.
# Owner: product-governance. Referencia: tools/external-auditors-gate.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.claude/agents/(metrology-auditor|legal-counsel|senior-reviewer)\.md|compliance/audits/|tools/external-auditors-gate\.ts|tools/external-auditors-gate\.test\.ts|harness/16-agentes-auditores-externos\.md|specs/0007-external-auditors\.md|adr/0010-external-auditor-gates\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[external-auditors-gate] sem arquivos P0-12 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[external-auditors-gate] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[external-auditors-gate] validando auditores externos..."
run_pnpm external-auditors-gate
