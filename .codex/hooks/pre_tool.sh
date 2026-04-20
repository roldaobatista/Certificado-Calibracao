#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
# Implementação completa nas camadas P0 dos runbooks.
set -e
cmd="${CODEX_TOOL_INPUT:-}"
case "$cmd" in
  *"git push --force"*|*"git push -f"*) echo "BLOQUEADO: git push force" >&2; exit 1 ;;
  *"--no-verify"*) echo "BLOQUEADO: --no-verify" >&2; exit 1 ;;
  *"rm -rf /"*|*"rm -rf ~"*) echo "BLOQUEADO: rm -rf raiz" >&2; exit 1 ;;
esac
exit 0
