#!/usr/bin/env bash
# Helpers compartilhados pelos hooks do Aferê.

run_pnpm() {
  if command -v node >/dev/null 2>&1; then
    pnpm "$@"
    return $?
  fi

  if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /d /c pnpm.cmd "$@"
    return $?
  fi

  echo "[hooks] node não encontrado no ambiente bash e cmd.exe indisponível."
  echo "[hooks] Rode pelo PowerShell/Git Bash com Node no PATH ou instale Node no WSL."
  return 127
}
