#!/usr/bin/env bash
# =============================================================
# block-destructive.sh
# Bloqueia comandos shell perigosos antes de executar.
# Evento: PreToolUse(Bash)
#
# Como funciona:
#   - Claude Code envia JSON via stdin com {tool_input: {command: "..."}}
#   - Este script usa perl (JSON::PP, nativo desde Perl 5.14) pra
#     decodificar o JSON corretamente, inclusive aspas escapadas
#     como `command: "sqlite3 db \"DROP TABLE x\""`. Não usar sed
#     puro pra isso: a regex quebra na primeira aspa e bypassa o filtro.
#   - Compara o comando decodificado com lista de padrões proibidos.
#   - Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar manualmente:
#   echo '{"tool_input":{"command":"rm -rf /"}}' | bash .claude/hooks/block-destructive.sh
#   echo $?    # esperar 2 (bloqueou)
#
#   echo '{"tool_input":{"command":"ls"}}' | bash .claude/hooks/block-destructive.sh
#   echo $?    # esperar 0 (permitiu)
#
#   echo '{"tool_input":{"command":"sqlite3 db.sqlite \"DROP TABLE x\""}}' | bash .claude/hooks/block-destructive.sh
#   echo $?    # esperar 2 (regressão: bypass via aspas escapadas)
# =============================================================

set -u

input=$(cat)

# Extrai .tool_input.command via perl + JSON::PP.
# Se perl não existir OU o JSON for inválido, falha aberta (exit 0) —
# bloqueador mais conservador romperia até `ls`. A defesa secundária
# fica nos padrões `permissions.deny` do settings.json.
command=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $cmd = $j->{tool_input}{command};
    print $cmd if defined $cmd;
' 2>/dev/null)

if [ -z "$command" ]; then
    exit 0
fi

# Padrões proibidos — regex bash (=~), case-insensitive via lowercase.
# Caracteres aceitos ANTES de drop/truncate incluem aspas e `=` porque
# DROP/TRUNCATE quase sempre aparecem dentro de string passada a cliente
# de banco: `sqlite3 db "DROP TABLE x"`, `psql -c 'DROP TABLE x'`,
# `mysql --execute=DROP TABLE x`.
# Padrões SHELL-perigosos — buscados no comando inteiro.
# Aqui o pattern em si tem que ser tóxico (não cabe em string benigna).
# Caracteres aceitos ANTES de drop/truncate incluem aspas e `=` porque
# DROP/TRUNCATE quase sempre aparecem dentro de string passada a cliente
# de banco: `sqlite3 db "DROP TABLE x"`, `psql -c 'DROP TABLE x'`,
# `mysql --execute=DROP TABLE x`.
shell_patterns=(
    '^[[:space:]]*rm[[:space:]]+-rf?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-fr?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-[rRf]+([[:space:]]|$)'
    '(^|[[:space:];|&="'\''`(])drop[[:space:]]+table'
    '(^|[[:space:];|&="'\''`(])truncate[[:space:]]+(table[[:space:]]+)?[a-z_]'
    'chmod[[:space:]]+777'
    'curl[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'wget[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'mkfs\.'
    'dd[[:space:]]+if='
    '>[[:space:]]*/dev/sd'
)

# Padrões GIT-flag — buscados SÓ na parte do comando antes da primeira aspa.
# Justificativa: regex sem look-around não distingue flag real de literal
# dentro de uma mensagem de commit (`git commit -m "fala de --no-verify"`).
# Truncar na primeira aspa isola os flags reais da mensagem.
git_patterns=(
    'git[[:space:]]+push[[:space:]]+.*--force'
    'git[[:space:]]+push[[:space:]]+-f([[:space:]]|$)'
    'git[[:space:]]+reset[[:space:]]+--hard'
    'git[[:space:]]+clean[[:space:]]+-fdx?'
    'git[[:space:]]+branch[[:space:]]+-D[[:space:]]'
    # Bypass de quality gates / hooks (Plano anti-erros-ia, Grupo 1).
    # REGRAS-INEGOCIAVEIS.md SEC-* e CLAUDE.md proíbem --no-verify.
    'git[[:space:]]+(commit|push|merge|rebase|cherry-pick|am)[[:space:]]+.*--no-verify'
    'git[[:space:]]+(commit|push|merge|rebase|cherry-pick|am)[[:space:]]+.*--no-gpg-sign'
)

command_lower=$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')

# Comando "fora de string" — substitui o CONTEÚDO de aspas pareadas por
# espaço, preservando flags que aparecem antes E depois das strings.
# Truncar na primeira aspa não basta: `git commit -m "msg" --no-verify`
# tem flag real APÓS a string. Stripping completo é o jeito.
cmd_flags_only=$(printf '%s' "$command_lower" | perl -pe '
    s/"[^"]*"/ /g;
    s/'\''[^'\'']*'\''/ /g;
' 2>/dev/null)
[ -z "$cmd_flags_only" ] && cmd_flags_only="$command_lower"

# Caso especial: git commit -n (curto ou combinado tipo -an/-na/-anm)
# também bypassa pre-commit. Procurado em cmd_flags_only.
if [[ "$cmd_flags_only" =~ git[[:space:]]+commit ]]; then
    if [[ "$cmd_flags_only" =~ (^|[[:space:]])-[a-z]*n[a-z]*($|[[:space:]]) ]]; then
        echo "Comando bloqueado por block-destructive: $command" >&2
        echo "git commit com -n bypassa pre-commit hook. Proibido." >&2
        exit 2
    fi
fi

for pattern in "${git_patterns[@]}"; do
    if [[ "$cmd_flags_only" =~ $pattern ]]; then
        echo "Comando bloqueado por block-destructive: $command" >&2
        echo "Padrao git proibido detectado." >&2
        exit 2
    fi
done

for pattern in "${shell_patterns[@]}"; do
    if [[ "$command_lower" =~ $pattern ]]; then
        echo "Comando bloqueado por block-destructive: $command" >&2
        echo "Padrao shell proibido detectado." >&2
        exit 2
    fi
done

exit 0
