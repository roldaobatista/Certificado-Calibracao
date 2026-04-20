#!/usr/bin/env bash
# SessionStart — valida CLAUDE.md, AGENTS.md e harness/STATUS.md
# Stub inicial — implementação completa nas camadas P0 dos runbooks.
# Falha fail-closed em implementação final; este stub registra e passa.
set -e
echo "[hook:session-start.sh] SessionStart — valida CLAUDE.md, AGENTS.md e harness/STATUS.md"
test -f CLAUDE.md || { echo "CLAUDE.md ausente — harness incompleto" >&2; exit 2; }
test -f AGENTS.md || { echo "AGENTS.md ausente — harness incompleto" >&2; exit 2; }
test -f harness/STATUS.md || { echo "harness/STATUS.md ausente" >&2; exit 2; }
exit 0
