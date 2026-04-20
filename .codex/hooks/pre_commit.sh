#!/usr/bin/env bash
# Codex CLI hook — espelho de .claude/hooks/. Mesmos gates duros.
set -e
# Espelha .claude/hooks/*. Gates duros rodam também pelo git hook canônico.
# Gates duros em git hooks rodam independentes da CLI escolhida.
for h in copy-lint ownership-lint tenant-safe-sql audit-hash-chain validation-dossier redundancy-check governance-gate escalation-check external-auditors-gate roadmap-check sync-simulator-check cloud-agents-policy-check; do
  if [ -f ".claude/hooks/${h}.sh" ]; then
    bash ".claude/hooks/${h}.sh" || exit 1
  fi
done
exit 0
