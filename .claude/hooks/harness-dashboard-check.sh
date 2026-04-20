#!/usr/bin/env bash
# PreCommit — P2-3: dashboard de observabilidade do harness.
# Owner: product-governance. Referencia: tools/harness-dashboard.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(harness/STATUS\.md|compliance/harness-dashboard\.md|compliance/validation-dossier/coverage-report\.md|package\.json|tools/harness-dashboard\.ts|tools/harness-dashboard\.test\.ts|specs/0013-harness-observability-dashboard\.md|adr/0016-harness-observability-dashboard\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[harness-dashboard] sem arquivos P2-3 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[harness-dashboard] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[harness-dashboard] validando dashboard gerado..."
run_pnpm harness-dashboard:check
