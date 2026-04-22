#!/usr/bin/env bash
# Helpers compartilhados pelos hooks do Aferê.

run_pnpm_windows() {
  local repo_root
  repo_root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

  local windows_repo_root="$repo_root"
  if command -v wslpath >/dev/null 2>&1; then
    windows_repo_root="$(wslpath -w "$repo_root")"
  elif command -v cygpath >/dev/null 2>&1; then
    windows_repo_root="$(cygpath -w "$repo_root")"
  elif [[ "$windows_repo_root" =~ ^[A-Za-z]:/ ]]; then
    windows_repo_root="${windows_repo_root//\//\\}"
  fi

  if command -v cmd.exe >/dev/null 2>&1; then
    local cmdline
    printf -v cmdline 'call "%s\\tools\\ensure-node-env.cmd" pnpm.cmd' "$windows_repo_root"
    local arg
    for arg in "$@"; do
      cmdline+=" \"$arg\""
    done
    cmd.exe /d /c "$cmdline"
    return $?
  fi

  if command -v pwsh.exe >/dev/null 2>&1; then
    pwsh.exe -NoProfile -ExecutionPolicy Bypass -File "$windows_repo_root\\tools\\ensure-node-env.ps1" -- pnpm "$@"
    return $?
  fi

  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$windows_repo_root\\tools\\ensure-node-env.ps1" -- pnpm "$@"
}

run_pnpm() {
  case "$(uname -s 2>/dev/null)" in
    MINGW*|MSYS*|CYGWIN*)
      if command -v pnpm.cmd >/dev/null 2>&1; then
        pnpm.cmd "$@"
        return $?
      fi
      if command -v powershell.exe >/dev/null 2>&1; then
        run_pnpm_windows "$@"
        return $?
      fi
      ;;
  esac

  if command -v node >/dev/null 2>&1; then
    pnpm "$@"
    return $?
  fi

  if command -v cmd.exe >/dev/null 2>&1; then
    cmd.exe /d /c call tools\\ensure-node-env.cmd pnpm.cmd "$@"
    return $?
  fi

  echo "[hooks] node não encontrado no ambiente bash e cmd.exe indisponível."
  echo "[hooks] Rode pelo PowerShell/Git Bash com Node no PATH ou instale Node no WSL."
  return 127
}
