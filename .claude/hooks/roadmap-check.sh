#!/usr/bin/env bash
# PreCommit — P1-4: roadmap em fatias verticais V1-V5.
# Owner: product-governance. Referencia: tools/roadmap-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/roadmap/|tools/roadmap-check\.ts|tools/roadmap-check\.test\.ts|harness/10-roadmap\.md|specs/0008-vertical-roadmap\.md|adr/0011-vertical-roadmap-gate\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[roadmap-check] sem arquivos P1-4 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[roadmap-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[roadmap-check] validando roadmap V1-V5..."
run_pnpm roadmap-check
