#!/usr/bin/env bash
# =============================================================
# context-budget.sh
# Avisa quando docs canonicos passam do orcamento de tokens.
# Evento: SessionStart (nao bloqueia — so emite warning em stderr)
#
# Como funciona:
#   - Le tamanho em chars de docs canonicos
#   - Estima tokens como chars/4 (heuristica do tokenizer)
#   - Emite warning se passar threshold
#   - SEMPRE exit 0 (informativo, nao bloqueante)
#
# Limites (alinhados com docs/orcamento-contexto.md):
#   - CLAUDE.md: 150 linhas / ~3500 tokens
#   - AGENTS.md: 250 linhas / ~6000 tokens
#   - REGRAS-INEGOCIAVEIS.md: ~10000 tokens (cresce com IDs)
#   - INDICE.md: ~3000 tokens
#   - MAPA-DO-DONO.md: ~2000 tokens
#
# Como testar:
#   echo '{}' | bash .claude/hooks/context-budget.sh
#   echo $?    # esperar 0 (nunca bloqueia)
# =============================================================

set -u

# Le projeto root via env (Claude Code injeta CLAUDE_PROJECT_DIR)
root="${CLAUDE_PROJECT_DIR:-$(pwd)}"

declare -A docs=(
    ["CLAUDE.md"]=3500
    ["AGENTS.md"]=6000
    ["REGRAS-INEGOCIAVEIS.md"]=12000
    ["docs/INDICE.md"]=3500
    ["docs/MAPA-DO-DONO.md"]=2500
)

total_tokens=0
warnings=()

for doc in "${!docs[@]}"; do
    limit="${docs[$doc]}"
    path="$root/$doc"
    if [ ! -f "$path" ]; then
        continue
    fi
    chars=$(wc -c < "$path" 2>/dev/null || echo 0)
    tokens=$((chars / 4))
    total_tokens=$((total_tokens + tokens))
    if [ "$tokens" -gt "$limit" ]; then
        warnings+=("$doc: ~${tokens} tokens (limite ${limit}) — mover regras pra .claude/rules/ ou cortar")
    fi
done

if [ ${#warnings[@]} -gt 0 ]; then
    echo "[context-budget] Docs canonicos acima do orcamento:" >&2
    for w in "${warnings[@]}"; do
        echo "  - $w" >&2
    done
    echo "  Total estimado em docs canonicos: ~${total_tokens} tokens" >&2
fi

exit 0
