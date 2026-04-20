#!/usr/bin/env bash
# PreCommit — P1-1: simulador determinístico de sync/conflito.
# Owner: qa-acceptance. Referencia: tools/sync-simulator-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(evals/sync-simulator/|tools/sync-simulator-check\.ts|tools/sync-simulator-check\.test\.ts|harness/08-sync-simulator\.md|specs/0009-sync-simulator\.md|adr/0012-sync-simulator-gate\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[sync-simulator-check] sem arquivos P1-1 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[sync-simulator-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[sync-simulator-check] validando simulador de sync..."
run_pnpm sync-simulator-check
run_pnpm test:sync-simulator
