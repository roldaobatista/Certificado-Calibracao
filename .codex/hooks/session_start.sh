#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
# Implementação completa nas camadas P0 dos runbooks.
set -e
test -f AGENTS.md || { echo "AGENTS.md ausente" >&2; exit 2; }
test -f harness/STATUS.md || { echo "harness/STATUS.md ausente" >&2; exit 2; }
echo "[codex:session_start] harness carregado"
exit 0
