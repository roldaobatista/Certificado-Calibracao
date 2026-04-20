#!/usr/bin/env bash
# tools/install-mcp.sh — registra MCP servers do Aferê na(s) CLI(s).
# Idempotente dentro dos limites da CLI (se já registrado, a CLI retorna
# erro mas este script segue em frente).
#
# Uso:
#   bash tools/install-mcp.sh claude
#   bash tools/install-mcp.sh codex
#   bash tools/install-mcp.sh both
#
# Ajuste POSTGRES_URL antes se seu dev DB estiver fora do docker compose local.
set -u

POSTGRES_URL="${POSTGRES_URL:-postgresql://afere:afere@localhost:5433/afere?schema=public}"

target="${1:-}"
if [ -z "$target" ] || ! [[ "$target" =~ ^(claude|codex|both)$ ]]; then
  echo "uso: bash $0 {claude|codex|both}"
  exit 2
fi

try() {
  # Executa comando, não falha o script se der erro (idempotência cosmética)
  echo "→ $*"
  "$@" || echo "  (não fatal — talvez já registrado)"
}

install_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    echo "✗ 'claude' não está no PATH. Instale: npm i -g @anthropic-ai/claude-code"
    return 1
  fi
  echo "=== Registrando MCPs no Claude Code ==="
  try claude mcp add context-mode
  try claude mcp add context7
  try claude mcp add playwright
  try claude mcp add vitest
  try claude mcp add github
  try claude mcp add postgres -e POSTGRES_URL="$POSTGRES_URL"
  echo ""
  claude mcp list || true
}

install_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "✗ 'codex' não está no PATH. Instale: npm i -g @openai/codex"
    return 1
  fi
  echo "=== Registrando MCPs no Codex CLI ==="
  try codex mcp add context-mode
  try codex mcp add context7
  try codex mcp add playwright
  try codex mcp add vitest
  try codex mcp add github
  try codex mcp add postgres --env POSTGRES_URL="$POSTGRES_URL"
  echo ""
  codex mcp list || true
}

case "$target" in
  claude) install_claude ;;
  codex)  install_codex ;;
  both)   install_claude; echo ""; install_codex ;;
esac
