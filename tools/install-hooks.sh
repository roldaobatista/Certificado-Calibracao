#!/usr/bin/env bash
# tools/install-hooks.sh — configura git para usar .githooks/ do repo.
# Idempotente. Seguro para rodar múltiplas vezes.
#
# Após clonar o repo, rode UMA VEZ:
#   bash tools/install-hooks.sh
#
# Efeito:
#   git config core.hooksPath .githooks   (escopo local, não --global)
#   chmod +x nos scripts de .githooks e .claude/hooks
set -e

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

if [ ! -d ".githooks" ]; then
  echo "✗ .githooks/ não encontrado — está no repo errado?"
  exit 1
fi

echo "→ apontando git hooksPath para .githooks (escopo local)"
git config core.hooksPath .githooks

echo "→ garantindo +x em scripts de hook"
chmod +x .githooks/* 2>/dev/null || true
chmod +x .claude/hooks/*.sh 2>/dev/null || true
chmod +x .codex/hooks/*.sh 2>/dev/null || true
chmod +x tools/*.sh 2>/dev/null || true

echo ""
echo "✓ git hooks instalados."
echo "   Validação: $(git config core.hooksPath)"
echo ""
echo "Gates ativados em pre-commit:"
echo "  - copy-lint (claims proibidos)"
echo "  - ownership-lint (Gate 6)"
echo "  - tenant-safe-sql (Gate 1, stub)"
echo "  - audit-hash-chain (Gate 3, stub)"
echo ""
echo "Para pular em emergência (desencorajado):"
echo "  SKIP_GATES=1 git commit -m '...'"
