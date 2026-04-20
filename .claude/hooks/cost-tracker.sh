#!/usr/bin/env bash
# PostToolUse — atualiza compliance/budget-log/ com tokens e custo
# Stub inicial — implementação completa nas camadas P0 dos runbooks.
# Falha fail-closed em implementação final; este stub registra e passa.
set -e
echo "[hook:cost-tracker.sh] PostToolUse — atualiza compliance/budget-log/ com tokens e custo"
mkdir -p compliance/budget-log
echo "{\"ts\":\"$(date -Iseconds)\",\"tool\":\"${CLAUDE_TOOL_NAME:-}\"}" >> "compliance/budget-log/$(date +%Y-%m-%d).jsonl"
exit 0
