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
blocked_patterns=(
    '^[[:space:]]*rm[[:space:]]+-rf?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-fr?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-[rRf]+([[:space:]]|$)'
    'git[[:space:]]+push[[:space:]]+.*--force'
    'git[[:space:]]+push[[:space:]]+-f([[:space:]]|$)'
    'git[[:space:]]+reset[[:space:]]+--hard'
    'git[[:space:]]+clean[[:space:]]+-fdx?'
    'git[[:space:]]+branch[[:space:]]+-D[[:space:]]'
    '(^|[[:space:];|&="'\''`(])drop[[:space:]]+table'
    '(^|[[:space:];|&="'\''`(])truncate[[:space:]]+(table[[:space:]]+)?[a-z_]'
    'chmod[[:space:]]+777'
    'curl[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'wget[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'mkfs\.'
    'dd[[:space:]]+if='
    '>[[:space:]]*/dev/sd'
)

command_lower=$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')

for pattern in "${blocked_patterns[@]}"; do
    if [[ "$command_lower" =~ $pattern ]]; then
        echo "Comando bloqueado por block-destructive: $command" >&2
        echo "Padrao proibido detectado." >&2
        exit 2
    fi
done

exit 0
