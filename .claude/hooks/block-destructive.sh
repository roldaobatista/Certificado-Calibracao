#!/usr/bin/env bash
# PreToolUse:Bash — bloqueia destrutivas sem autorização
# Stub inicial — implementação completa nas camadas P0 dos runbooks.
# Falha fail-closed em implementação final; este stub registra e passa.
set -e
echo "[hook:block-destructive.sh] PreToolUse:Bash — bloqueia destrutivas sem autorização"
cmd="${CLAUDE_TOOL_INPUT:-}"
case "$cmd" in
  *"git push --force"*|*"git push -f"*) echo "BLOQUEADO: git push force" >&2; exit 1 ;;
  *"--no-verify"*) echo "BLOQUEADO: --no-verify proibido (AGENTS.md §5)" >&2; exit 1 ;;
  *"rm -rf /"*|*"rm -rf ~"*) echo "BLOQUEADO: rm -rf raiz" >&2; exit 1 ;;
esac
exit 0
