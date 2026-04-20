#!/usr/bin/env bash
# PreCommit - P0-10/Gate 7: snapshot-diff canonico de certificados.
# Owner: qa-acceptance + regulator. Referencia: tools/verification-cascade.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/validation-dossier/snapshots/|tools/verification-cascade\.ts|tools/verification-cascade\.test\.ts|specs/0019-snapshot-diff-gate\.md|adr/0022-snapshot-diff-gate\.md|harness/STATUS\.md|package\.json|\.githooks/pre-commit|\.claude/hooks/snapshot-diff-check\.sh)$' || true)

if [ -z "$FILES" ]; then
  echo "[snapshot-diff-check] sem arquivos P0-10/Gate 7 no delta - ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[snapshot-diff-check] workspace nao instalado - pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[snapshot-diff-check] validando manifesto e hashes de snapshots..."
run_pnpm snapshot-diff-check
