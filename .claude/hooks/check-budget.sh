#!/usr/bin/env bash
# PreToolUse — consulta contador de tokens/custo; fail-closed em hard cap
set -e
HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HOOK_DIR/lib.sh"

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"
NODE_REPO_ROOT="$REPO_ROOT"
if command -v wslpath >/dev/null 2>&1; then
  NODE_REPO_ROOT="$(wslpath -w "$REPO_ROOT")"
fi

if [ ! -d "node_modules" ]; then
  echo "[budget] workspace nao instalado; fail-closed para preservar caps (rode pnpm install)" >&2
  exit 1
fi

args=(check --write-events --workspace "$NODE_REPO_ROOT" --cli claude --hook PreToolUse --tool "${CLAUDE_TOOL_NAME:-unknown}")

add_arg() {
  local name="$1"
  local value="$2"
  if [ -n "$value" ]; then
    args+=("$name" "$value")
  fi
}

add_arg --task-id "${AFERE_TASK_ID:-${CLAUDE_TASK_ID:-${CLAUDE_SESSION_ID:-}}}"
add_arg --pr-id "${AFERE_PR_ID:-${CLAUDE_PR_ID:-}}"
add_arg --input-tokens "${AFERE_BUDGET_INPUT_TOKENS:-${CLAUDE_USAGE_INPUT_TOKENS:-${CLAUDE_INPUT_TOKENS:-}}}"
add_arg --output-tokens "${AFERE_BUDGET_OUTPUT_TOKENS:-${CLAUDE_USAGE_OUTPUT_TOKENS:-${CLAUDE_OUTPUT_TOKENS:-}}}"
add_arg --tokens "${AFERE_BUDGET_TOKENS:-${CLAUDE_USAGE_TOTAL_TOKENS:-${CLAUDE_TOTAL_TOKENS:-}}}"
add_arg --cost-usd "${AFERE_BUDGET_COST_USD:-${CLAUDE_USAGE_COST_USD:-${CLAUDE_COST_USD:-}}}"

run_pnpm exec tsx tools/budget-tracker.ts "${args[@]}"
