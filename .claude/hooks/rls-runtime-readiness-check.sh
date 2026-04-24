#!/usr/bin/env bash
# PreCommit — Gate RLS runtime: impede adoção silenciosa de owner-bypass, app role ou FORCE RLS.
# Owner: db-schema + lgpd-security. Referência: tools/rls-runtime-readiness-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.env\.example|docker-compose\.yml|packages/db/prisma/migrations/.*/migration\.sql|packages/db/src/tenant-context\.ts|tools/rls-runtime-readiness-check\.(ts|test\.ts)|specs/0099-rls-runtime-role-readiness\.md|adr/0065-rls-runtime-role-readiness\.md|compliance/validation-dossier/findings/2026-04-24-rls-owner-bypass-risk\.md|package\.json)$' || true)

if [ -z "$FILES" ]; then
  echo "[rls-runtime-readiness-check] sem runtime RLS no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[rls-runtime-readiness-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[rls-runtime-readiness-check] validando prontidão de role/runtime RLS..."
run_pnpm rls-runtime-readiness-check
