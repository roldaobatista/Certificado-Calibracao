#!/usr/bin/env bash
# PreCommit — P1-3: estrutura canônica de compliance/.
# Owner: product-governance. Referencia: tools/compliance-structure-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/|tools/compliance-structure-check\.ts|tools/compliance-structure-check\.test\.ts|specs/0017-compliance-structure-gate\.md|adr/0020-compliance-structure-gate\.md|harness/STATUS\.md|package\.json|\.githooks/pre-commit|\.claude/hooks/compliance-structure-check\.sh)$' || true)

if [ -z "$FILES" ]; then
  echo "[compliance-structure-check] sem arquivos P1-3 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[compliance-structure-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[compliance-structure-check] validando estrutura canônica de compliance/..."
run_pnpm compliance-structure-check
