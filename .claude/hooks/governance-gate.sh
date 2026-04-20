#!/usr/bin/env bash
# PreCommit — P0-6: CODEOWNERS + template de PR + product-governance sem escrita em codigo.
# Owner: product-governance. Referencia: harness/07-governance-gate.md.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.github/CODEOWNERS|\.github/pull_request_template\.md|\.claude/agents/product-governance\.md|tools/governance-gate\.ts|tools/governance-gate\.test\.ts|harness/07-governance-gate\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[governance-gate] sem arquivos de governanca no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[governance-gate] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[governance-gate] validando CODEOWNERS e product-governance..."
run_pnpm governance-gate
