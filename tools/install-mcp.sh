#!/usr/bin/env bash
# tools/install-mcp.sh — registra MCP servers do Aferê nas CLIs.
# Sintaxe 2026: Codex exige `codex mcp add <NAME> -- <command>`. Claude Code
# aceita tanto marketplace shortcuts (`claude mcp add github`) quanto forma
# explícita via `--`; aqui usamos explícita para ser portável.
#
# Uso:
#   bash tools/install-mcp.sh claude
#   bash tools/install-mcp.sh codex
#   bash tools/install-mcp.sh both
#
# Variáveis opcionais:
#   POSTGRES_URL      default: dev do docker-compose (localhost:5433)
#   GITHUB_TOKEN      token PAT do GitHub (scope: repo, read:org)
set -u

POSTGRES_URL="${POSTGRES_URL:-postgresql://afere:afere@localhost:5433/afere?schema=public}"
GITHUB_TOKEN="${GITHUB_TOKEN:-}"

target="${1:-}"
if [ -z "$target" ] || ! [[ "$target" =~ ^(claude|codex|both)$ ]]; then
  echo "uso: bash $0 {claude|codex|both}"
  exit 2
fi

try() {
  echo "→ $*"
  "$@" || echo "  (não fatal — talvez já registrado)"
  echo ""
}

install_codex() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "✗ 'codex' não está no PATH. Instale: npm i -g @openai/codex"
    return 1
  fi
  echo "=== Registrando MCPs no Codex CLI ==="
  # GitHub (exige token)
  if [ -n "$GITHUB_TOKEN" ]; then
    try codex mcp add github \
      --env GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" \
      -- npx -y @modelcontextprotocol/server-github
  else
    echo "⚠️  GITHUB_TOKEN não definido — pulando github. Registre manualmente:"
    echo "    codex mcp add github --env GITHUB_PERSONAL_ACCESS_TOKEN=ghp_... -- npx -y @modelcontextprotocol/server-github"
    echo ""
  fi
  # Postgres (aceita URL no args do servidor)
  try codex mcp add postgres \
    --env POSTGRES_URL="$POSTGRES_URL" \
    -- npx -y @modelcontextprotocol/server-postgres "$POSTGRES_URL"
  # Playwright (oficial)
  try codex mcp add playwright -- npx -y @playwright/mcp@latest
  # Context7 (docs de libs, Upstash)
  try codex mcp add context7 -- npx -y @upstash/context7-mcp

  echo ""
  echo "ℹ️  MCPs sem pacote público conhecido (2026-04):"
  echo "   - context-mode: plugin Claude-específico; sem equivalente Codex oficial."
  echo "     Alternativa: pode rodar Codex COMO MCP para Claude (ver tools/setup-mcp.md)."
  echo "   - vitest: não há server MCP oficial para vitest ainda."
  echo "     Workaround: use 'codex exec -- pnpm test' em vez de MCP dedicado."
  echo ""
  codex mcp list
}

install_claude() {
  if ! command -v claude >/dev/null 2>&1; then
    echo "✗ 'claude' não está no PATH. Instale: npm i -g @anthropic-ai/claude-code"
    return 1
  fi
  echo "=== Registrando MCPs no Claude Code ==="
  # Forma explícita para paridade com Codex. Se preferir marketplace, rode
  # 'claude mcp add <nome>' interativamente.
  if [ -n "$GITHUB_TOKEN" ]; then
    try claude mcp add github \
      --env GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" \
      -- npx -y @modelcontextprotocol/server-github
  else
    echo "⚠️  GITHUB_TOKEN não definido — pulando github. Registre manualmente:"
    echo "    claude mcp add github -- npx -y @modelcontextprotocol/server-github"
    echo ""
  fi
  try claude mcp add postgres \
    --env POSTGRES_URL="$POSTGRES_URL" \
    -- npx -y @modelcontextprotocol/server-postgres "$POSTGRES_URL"
  try claude mcp add playwright -- npx -y @playwright/mcp@latest
  try claude mcp add context7 -- npx -y @upstash/context7-mcp
  # context-mode no Claude entra via plugin marketplace
  echo "→ claude /plugin install context-mode (execute dentro de uma sessão Claude)"
  echo ""
  claude mcp list || true
}

case "$target" in
  claude) install_claude ;;
  codex)  install_codex ;;
  both)   install_claude; echo ""; install_codex ;;
esac
