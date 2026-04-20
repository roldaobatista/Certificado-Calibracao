#!/usr/bin/env bash
# PreCommit — P2-4: texto de Tier 3 no HARNESS_DESIGN.md raiz.
# Owner: product-governance. Referência: tools/harness-design-tier3-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(HARNESS_DESIGN\.md|tools/harness-design-tier3-check\.ts|tools/harness-design-tier3-check\.test\.ts|specs/0014-tier3-harness-design.md|adr/0017-tier3-harness-design.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[harness-design-tier3] sem arquivos P2-4 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[harness-design-tier3] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[harness-design-tier3] validando texto Tier 3..."
run_pnpm harness-design-tier3-check
