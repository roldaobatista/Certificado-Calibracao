#!/usr/bin/env bash
# PreCommit — P2-1: frontmatter padrão dos agentes.
# Owner: product-governance. Referencia: tools/agent-frontmatter-check.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(\.claude/agents/|\.codex/agents/|tools/agent-frontmatter-check\.ts|tools/agent-frontmatter-check\.test\.ts|harness/03-agentes\.md|specs/0011-agent-frontmatter-standard\.md)$' || true)

if [ -z "$FILES" ]; then
  echo "[agent-frontmatter-check] sem arquivos P2-1 no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[agent-frontmatter-check] workspace nao instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[agent-frontmatter-check] validando frontmatter dos agentes..."
run_pnpm agent-frontmatter-check
