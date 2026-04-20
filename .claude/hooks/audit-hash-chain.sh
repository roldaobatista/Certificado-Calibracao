#!/usr/bin/env bash
# PreCommit — audit hash-chain verifier (Gate 3)
# Valida artefatos JSONL de audit hash-chain quando presentes no delta.
# Owner: db-schema + lgpd-security. Referência: packages/audit-log.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '(^|/)(audit|audit-log|hash-chain).*\.(jsonl)$|\.audit\.jsonl$' || true)

if [ -z "$FILES" ]; then
  echo "[audit-hash-chain] sem artefatos JSONL de audit chain no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[audit-hash-chain] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[audit-hash-chain] verificando JSONL..."
for file in $FILES; do
  run_pnpm audit-chain:verify "$file"
done
