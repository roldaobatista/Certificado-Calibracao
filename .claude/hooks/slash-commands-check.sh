#!/usr/bin/env bash
# PreCommit — P2-2: slash-commands regulatórios.
# Owner: product-governance. Referencia: tools/slash-commands-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.claude/commands/|tools/slash-commands-check\.ts|tools/slash-commands-check\.test\.ts|harness/STATUS\.md|specs/0012-regulatory-slash-commands\.md|adr/0015-regulatory-slash-commands\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[slash-commands-check] sem arquivos P2-2 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[slash-commands-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[slash-commands-check] validando slash-commands regulatórios..."
run_pnpm slash-commands-check
