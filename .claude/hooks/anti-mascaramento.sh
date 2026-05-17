#!/usr/bin/env bash
# =============================================================
# anti-mascaramento.sh
# Bloqueia gravacao de codigo com padroes de mascaramento de bug.
# Enforce TST-001, TST-002, TST-003 de REGRAS-INEGOCIAVEIS.md
# Evento: PreToolUse(Write|Edit)
#
# Como funciona:
#   - Le tool_input.content (Write) ou tool_input.new_string (Edit)
#   - Detecta padroes de mascaramento listados abaixo
#   - Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar:
#   echo '{"tool_input":{"file_path":"test_x.py","content":"def test_x():\n    pytest.skip()"}}' | bash .claude/hooks/anti-mascaramento.sh
#   echo $?    # esperar 2 (TST-001)
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    my $c = $ti->{content} // $ti->{new_string} // "";
    print $c;
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0

# So aplica a arquivos de codigo (Python, JS, TS, Dart, Ruby, Go, Java)
case "$file_path" in
    *.py|*.js|*.ts|*.tsx|*.jsx|*.dart|*.rb|*.go|*.java|*.kt|*.swift) ;;
    *) exit 0 ;;
esac

# TST-002: assertions vazias (mascaramento direto)
empty_assert_patterns=(
    'assert[[:space:]]+(true|1)[[:space:]]*(#|$|\))'
    'assert[[:space:]]+1[[:space:]]*==[[:space:]]*1'
    'asserttrue\([[:space:]]*true[[:space:]]*\)'
    'assertequals\([[:space:]]*1[[:space:]]*,[[:space:]]*1[[:space:]]*\)'
    'expect\([[:space:]]*true[[:space:]]*\)\.tobe\([[:space:]]*true[[:space:]]*\)'
    'expect\([[:space:]]*1[[:space:]]*\)\.tobe\([[:space:]]*1[[:space:]]*\)'
    'xctasserttrue\([[:space:]]*true[[:space:]]*\)'
)

content_lc=$(printf '%s' "$content" | tr '[:upper:]' '[:lower:]')

for pattern in "${empty_assert_patterns[@]}"; do
    if printf '%s' "$content_lc" | grep -qE "$pattern"; then
        echo "anti-mascaramento (TST-002): assertion vazia detectada em $file_path" >&2
        echo "Padrao: $pattern" >&2
        echo "Veja REGRAS-INEGOCIAVEIS.md TST-002" >&2
        exit 2
    fi
done

# TST-001: skip sem comentario com data e dono
# Permite "skip 2026-XX-XX (Nome)" ou similar nas 3 linhas adjacentes
if printf '%s' "$content" | grep -nE '(pytest\.skip|unittest\.skip|@Disabled|xit\(|it\.skip|test\.skip|@pytest\.mark\.skip)' > /tmp/_amask_skip 2>/dev/null; then
    skip_lines=$(cat /tmp/_amask_skip)
    rm -f /tmp/_amask_skip
    # Para cada linha com skip, verifica se ha comentario com data na propria linha
    # ou nas 2 linhas acima do content
    if ! printf '%s' "$content" | grep -B 2 -E '(pytest\.skip|unittest\.skip|@Disabled|xit\(|it\.skip|test\.skip|@pytest\.mark\.skip)' | grep -qE '#.*20[0-9]{2}-[0-9]{2}-[0-9]{2}.*\([A-Za-z]'; then
        echo "anti-mascaramento (TST-001): skip() sem comentario com data e dono em $file_path" >&2
        echo "$skip_lines" >&2
        echo "Formato aceito: # skip YYYY-MM-DD (Nome) — razao tecnica" >&2
        exit 2
    fi
fi

# TST-003: bypass silencioso sem justificativa na MESMA linha
# Aceita: '@ts-ignore -- bug do typechecker em X', '# type: ignore  # lib Y nao tem stubs'
# Recusa: '@ts-ignore' solto, '# noqa' solto
bypass_patterns=(
    '@ts-ignore'
    '@ts-expect-error'
    '@ts-nocheck'
    'eslint-disable'
    'eslint-disable-next-line'
    'eslint-disable-line'
    '# type:[[:space:]]*ignore'
    '# noqa'
    '# pragma:[[:space:]]*no[[:space:]]*cover'
)

for pattern in "${bypass_patterns[@]}"; do
    # Procura linhas com o padrao
    matches=$(printf '%s' "$content" | grep -nE "$pattern" || true)
    [ -z "$matches" ] && continue
    # Para cada match, verifica se a linha tem justificativa apos o padrao
    while IFS= read -r line; do
        # Justificativa = '--', ':', '#' seguido de texto explicativo apos o pattern
        # Versao leve: exige >= 10 chars apos o pattern (excluindo so simbolos)
        cleaned=$(printf '%s' "$line" | sed -E "s/.*${pattern}//" | tr -d '[:space:]' )
        if [ "${#cleaned}" -lt 10 ]; then
            echo "anti-mascaramento (TST-003): bypass '$pattern' sem justificativa em $file_path" >&2
            echo "Linha: $line" >&2
            echo "Adicione justificativa na MESMA linha apos o pattern (>= 10 chars uteis)" >&2
            exit 2
        fi
    done <<< "$matches"
done

exit 0
