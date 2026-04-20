#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
# Implementação completa nas camadas P0 dos runbooks.
set -e
# Espelha .claude/hooks/copy-lint.sh, tenant-safe-sql.sh, audit-hash-chain.sh
# Gates duros em git hooks rodam independentes da CLI escolhida.
for h in copy-lint tenant-safe-sql audit-hash-chain; do
  if [ -x ".claude/hooks/${h}.sh" ]; then
    bash ".claude/hooks/${h}.sh" || exit 1
  fi
done
exit 0
