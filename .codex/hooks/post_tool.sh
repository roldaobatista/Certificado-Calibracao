#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
set -e
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
. "$REPO_ROOT/.claude/hooks/lib.sh"

cd "$REPO_ROOT"
NODE_REPO_ROOT="$REPO_ROOT"
if command -v wslpath >/dev/null 2>&1; then
  NODE_REPO_ROOT="$(wslpath -w "$REPO_ROOT")"
fi

if [ ! -d "node_modules" ]; then
  echo "[codex:budget] workspace nao instalado; fail-closed para preservar budget-log (rode pnpm install)" >&2
  exit 1
fi

args=(record --workspace "$NODE_REPO_ROOT" --cli codex --hook PostToolUse --tool "${CODEX_TOOL_NAME:-unknown}")

add_arg() {
  local name="$1"
  local value="$2"
  if [ -n "$value" ]; then
    args+=("$name" "$value")
  fi
}

add_arg --task-id "${AFERE_TASK_ID:-${CODEX_TASK_ID:-${CODEX_SESSION_ID:-}}}"
add_arg --pr-id "${AFERE_PR_ID:-${CODEX_PR_ID:-}}"
add_arg --input-tokens "${AFERE_BUDGET_INPUT_TOKENS:-${CODEX_USAGE_INPUT_TOKENS:-${CODEX_INPUT_TOKENS:-}}}"
add_arg --output-tokens "${AFERE_BUDGET_OUTPUT_TOKENS:-${CODEX_USAGE_OUTPUT_TOKENS:-${CODEX_OUTPUT_TOKENS:-}}}"
add_arg --tokens "${AFERE_BUDGET_TOKENS:-${CODEX_USAGE_TOTAL_TOKENS:-${CODEX_TOTAL_TOKENS:-}}}"
add_arg --cost-usd "${AFERE_BUDGET_COST_USD:-${CODEX_USAGE_COST_USD:-${CODEX_COST_USD:-}}}"

run_pnpm exec tsx tools/budget-tracker.ts "${args[@]}"
