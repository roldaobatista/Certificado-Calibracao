#!/usr/bin/env bash
# PreCommit — P0-3: requirements.yaml e traceability-matrix.yaml devem ficar sincronizados.
# Owner: qa-acceptance. Referência: tools/validation-dossier.ts.
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

STAGED=$(git diff --cached --name-only --diff-filter=AM 2>/dev/null || true)
FILES=$(echo "$STAGED" | grep -E '^(PRD\.md|specs/|compliance/validation-dossier/|tools/validation-dossier\.ts|tools/validation-dossier\.test\.ts)' || true)

if [ -z "$FILES" ]; then
  echo "[validation-dossier] sem arquivos rastreáveis no delta — ok"
  exit 0
fi

if [ ! -d "node_modules" ]; then
  echo "[validation-dossier] workspace não instalado — pulando (rode 'pnpm install' primeiro)"
  exit 0
fi

echo "[validation-dossier] validando matriz de rastreabilidade..."
run_pnpm exec tsx tools/validation-dossier.ts check --quiet
