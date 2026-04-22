#!/usr/bin/env bash
# PreCommit — P1-4: backlog executável do roadmap foundation-first.
# Owner: product-governance. Referencia: tools/roadmap-backlog-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(compliance/roadmap/execution-backlog\.yaml|compliance/roadmap/README\.md|compliance/roadmap/v1-v5\.yaml|tools/roadmap-backlog-check\.ts|tools/roadmap-backlog-check\.test\.ts|specs/0073-roadmap-execution-backlog\.md|adr/0051-roadmap-execution-backlog\.md|harness/10-roadmap\.md|harness/STATUS\.md|package\.json|\.githooks/pre-commit|\.claude/hooks/roadmap-backlog-check\.sh)$' || true)

if [ -z "$FILES" ]; then
  echo "[roadmap-backlog-check] sem arquivos do backlog executável no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[roadmap-backlog-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[roadmap-backlog-check] validando backlog executável do roadmap..."
run_pnpm roadmap-backlog-check
