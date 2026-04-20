#!/usr/bin/env bash
# PreCommit — Gate 6 (harness/05-guardrails.md): lint de ownership de imports.
# apps/web, apps/portal, apps/android não podem importar normative-rules,
# engine-uncertainty ou db diretamente. Violação bloqueia commit (fail-closed).
# Owner: backend-api. Referência: packages/ownership-lint.
set -e

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '\.(ts|tsx|js|jsx|mts|cts|kt|kts|java)$' || true)

if [ -z "$FILES" ]; then
  echo "[ownership-lint] sem arquivos de código no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ] && [ ! -d "packages/ownership-lint/node_modules" ]; then
  echo "[ownership-lint] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[ownership-lint] varrendo delta..."
# shellcheck disable=SC2086
pnpm --filter @afere/ownership-lint exec node --import tsx src/cli.ts $FILES
