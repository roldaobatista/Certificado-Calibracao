#!/usr/bin/env bash
# PreCommit — copy-lint regulatório no delta (harness/06-copy-lint.md)
# Claim de severity=error bloqueia commit (fail-closed).
# Owner: copy-compliance. Referência: packages/copy-lint + compliance/approved-claims.md.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

# Paths cobertos. Se não houver delta relevante, passa silencioso.
STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '\.(md|mdx|tsx|ts|html|hbs|mjml)$' || true)

if [ -z "$FILES" ]; then
  echo "[copy-lint] sem arquivos de copy no delta — ok"
  exit 0
fi

# Sem node_modules = harness ainda não buildado; não quebramos o commit por isso
if [ ! -d "node_modules" ] && [ ! -d "packages/copy-lint/node_modules" ]; then
  echo "[copy-lint] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[copy-lint] varrendo delta..."
# shellcheck disable=SC2086
run_pnpm --filter @afere/copy-lint exec node --import tsx src/cli.ts $FILES
