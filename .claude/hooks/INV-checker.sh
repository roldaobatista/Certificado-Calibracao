#!/usr/bin/env bash
# =============================================================
# INV-checker.sh
# Enforce TST-004: toda INV-* critica tem >=1 teste cujo nome cita o ID.
# Evento: PostToolUse(Write|Edit) em REGRAS-INEGOCIAVEIS.md
#
# Como funciona:
#   - Apos gravar REGRAS-INEGOCIAVEIS.md, le IDs INV-NNN e INV-TENANT-NNN
#   - Procura testes que mencionem cada ID (test_INV_NNN_*, INV-NNN no nome)
#   - Emite warning em stderr se faltarem testes (nao bloqueia)
#   - Pre-codigo de produto: pasta tests/ pode nao existir → so reporta IDs sem teste
#
# Exit codes:
#   - 0 sempre (informativo, nao bloqueante neste estagio)
# =============================================================

set -u

root="${CLAUDE_PROJECT_DIR:-$(pwd)}"
regras="$root/REGRAS-INEGOCIAVEIS.md"

input=$(cat 2>/dev/null || echo '{}')

# So roda se o ultimo Write/Edit tocou REGRAS-INEGOCIAVEIS.md
file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

case "$file_path" in
    *REGRAS-INEGOCIAVEIS.md) ;;
    "") ;;
    *) exit 0 ;;
esac

[ ! -f "$regras" ] && exit 0

# Extrai IDs INV-NNN, INV-TENANT-NNN, INV-AGENT-NNN da REGRAS-INEGOCIAVEIS
ids=$(grep -oE '\bINV-(TENANT-|AGENT-)?[0-9]{3}\b' "$regras" 2>/dev/null | sort -u)

[ -z "$ids" ] && exit 0

# Procura testes (varias linguagens) em locais comuns
test_dirs=("$root/tests" "$root/test" "$root/src/__tests__" "$root/spec")
test_files=""
for d in "${test_dirs[@]}"; do
    [ -d "$d" ] && test_files="$test_files $(find "$d" -type f \( -name '*.py' -o -name '*.ts' -o -name '*.js' -o -name '*.dart' -o -name '*.go' \) 2>/dev/null)"
done

missing=()
for id in $ids; do
    # Variantes: INV-001, INV_001, INV001
    id_under=$(printf '%s' "$id" | tr '-' '_')
    id_compact=$(printf '%s' "$id" | tr -d '-')
    if [ -n "$test_files" ]; then
        if ! grep -qE "($id|$id_under|$id_compact)" $test_files 2>/dev/null; then
            missing+=("$id")
        fi
    else
        # Sem pasta de testes ainda — todos faltam por definicao
        missing+=("$id")
    fi
done

if [ ${#missing[@]} -gt 0 ]; then
    echo "[INV-checker] IDs sem teste correspondente (TST-004):" >&2
    for m in "${missing[@]}"; do
        echo "  - $m" >&2
    done
    echo "  Crie teste cujo nome cite o ID (ex: test_INV_001_*) quando codigo existir." >&2
fi

exit 0
