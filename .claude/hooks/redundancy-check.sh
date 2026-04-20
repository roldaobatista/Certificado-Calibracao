#!/usr/bin/env bash
# PreCommit — P0-11: N por criticidade, flake gate e precedentes regulatorios.
# Owner: qa-acceptance. Referencia: tools/redundancy-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.github/workflows/nightly-flake-gate\.yml|evals/property-config\.yaml|evals/.*/reports/|compliance/validation-dossier/flake-log/|compliance/regulator-decisions/|tools/redundancy-check\.ts|tools/redundancy-check\.test\.ts|harness/15-redundancy-and-loops\.md|specs/0005-redundancy-loops\.md|adr/0008-redundancy-loop-gates\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[redundancy-check] sem arquivos P0-11 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[redundancy-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[redundancy-check] validando politica de redundancia..."
run_pnpm redundancy-check
