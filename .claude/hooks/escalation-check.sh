#!/usr/bin/env bash
# PreCommit — P0-8: matriz de escalonamento e rito de desempate.
# Owner: product-governance. Referencia: tools/escalation-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/escalations/|adr/0009-tiebreaker-designation\.md|tools/escalation-check\.ts|tools/escalation-check\.test\.ts|harness/12-escalation-matrix\.md|specs/0006-escalation-matrix\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[escalation-check] sem arquivos P0-8 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[escalation-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[escalation-check] validando rito de desempate..."
run_pnpm escalation-check
