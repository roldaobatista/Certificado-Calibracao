#!/usr/bin/env bash
# PreCommit — Gate RLS: toda tabela multitenant criada em migrations precisa de RLS + policy.
# Owner: db-schema. Referência: tools/rls-policy-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(packages/db/prisma/migrations/.*/migration\.sql|tools/rls-policy-check\.ts|tools/rls-policy-check\.test\.ts|package\.json)$' || true)

if [ -z "$FILES" ]; then
  echo "[rls-policy-check] sem migrações RLS no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[rls-policy-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[rls-policy-check] validando cobertura RLS das migrations..."
run_pnpm rls-policy-check
