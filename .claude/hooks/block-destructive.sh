#!/usr/bin/env bash
# =============================================================
# block-destructive.sh
# Bloqueia comandos shell perigosos antes de executar.
# Evento: PreToolUse(Bash)
#
# Como funciona:
#   - Claude Code envia JSON via stdin com {tool_input: {command: "..."}}
#   - Este script lê o stdin, extrai o comando com bash puro (sem jq),
#     compara com lista de padrões proibidos.
#   - Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar manualmente (antes de plugar):
#   echo '{"tool_input":{"command":"rm -rf /"}}' | bash .claude/hooks/block-destructive.sh
#   echo $?    # esperar 2 (bloqueou)
#
#   echo '{"tool_input":{"command":"ls"}}' | bash .claude/hooks/block-destructive.sh
#   echo $?    # esperar 0 (permitiu)
# =============================================================

set -u

# Lê o JSON inteiro do stdin
input=$(cat)

# Extrai o campo .tool_input.command usando bash puro (sem jq).
# Estratégia: procurar "command":"..." e capturar o conteúdo até a próxima aspa não-escapada.
# Funciona pra casos comuns; comandos com aspas escapadas no JSON precisariam de jq.
command=$(printf '%s' "$input" | sed -n 's/.*"command"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

# Se não conseguiu extrair o comando, deixa passar (não é nosso problema bloquear)
if [ -z "$command" ]; then
    exit 0
fi

# Padrões proibidos — usar regex bash (=~)
blocked_patterns=(
    '^[[:space:]]*rm[[:space:]]+-rf?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-fr?[[:space:]]'
    '^[[:space:]]*rm[[:space:]]+-[rRf]+([[:space:]]|$)'
    'git[[:space:]]+push[[:space:]]+.*--force'
    'git[[:space:]]+push[[:space:]]+-f([[:space:]]|$)'
    'git[[:space:]]+reset[[:space:]]+--hard'
    'git[[:space:]]+clean[[:space:]]+-fdx?'
    'git[[:space:]]+branch[[:space:]]+-D[[:space:]]'
    '(^|[[:space:];|&])drop[[:space:]]+table'
    '(^|[[:space:];|&])truncate[[:space:]]'
    'chmod[[:space:]]+777'
    'curl[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'wget[[:space:]]+.*\|[[:space:]]*(ba)?sh'
    'mkfs\.'
    'dd[[:space:]]+if='
    '>[[:space:]]*/dev/sd'
)

# Converter pra lowercase pra match case-insensitive
command_lower=$(printf '%s' "$command" | tr '[:upper:]' '[:lower:]')

for pattern in "${blocked_patterns[@]}"; do
    if [[ "$command_lower" =~ $pattern ]]; then
        # Mensagem em stderr (não polui stdout, que é onde Claude lê resposta)
        echo "❌ Comando bloqueado por block-destructive: $command" >&2
        echo "Padrão proibido detectado." >&2
        exit 2
    fi
done

# Permite
exit 0
