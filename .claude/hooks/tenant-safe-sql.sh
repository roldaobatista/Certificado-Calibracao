#!/usr/bin/env bash
# PreCommit — tenant-safe SQL linter (Gate 1)
# Bloqueia SQL cru/policy em tabela multitenant sem organization_id.
# Owner: db-schema. Referência: packages/db/tools/tenant-lint.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(packages/db/.*\.(sql|prisma|ts|tsx|mts|cts)|packages/db/prisma/.*|apps/api/src/.*\.(sql|ts|tsx|mts|cts))$' || true)

if [ -z "$FILES" ]; then
  echo "[tenant-safe-sql] sem arquivos SQL/API/Prisma no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[tenant-safe-sql] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[tenant-safe-sql] varrendo delta..."
# shellcheck disable=SC2086
run_pnpm exec tsx packages/db/tools/tenant-lint/src/cli.ts $FILES
