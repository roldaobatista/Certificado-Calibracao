#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
# Implementação completa nas camadas P0 dos runbooks.
set -e
mkdir -p compliance/budget-log
echo "{\"ts\":\"$(date -Iseconds)\",\"tool\":\"${CODEX_TOOL_NAME:-}\",\"cli\":\"codex\"}" >> "compliance/budget-log/$(date +%Y-%m-%d).jsonl"
exit 0
