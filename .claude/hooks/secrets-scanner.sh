#!/usr/bin/env bash
# =============================================================
# secrets-scanner.sh
# Bloqueia gravação acidental de arquivos com segredos.
# Evento: PreToolUse(Write|Edit)
#
# Como funciona:
#   - Claude Code envia JSON via stdin com {tool_input: {file_path: "...", content: "..."}}
#   - Este script:
#     1) Bloqueia se o file_path é nome de arquivo de segredo (.env, *.key, credentials, etc.)
#     2) Bloqueia se o content tem padrões de chave/token comum
#   - Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar manualmente:
#   echo '{"tool_input":{"file_path":".env","content":"FOO=bar"}}' | bash .claude/hooks/secrets-scanner.sh
#   echo $?    # esperar 2 (bloqueou pelo nome)
#
#   echo '{"tool_input":{"file_path":"src/foo.ts","content":"const x = 1"}}' | bash .claude/hooks/secrets-scanner.sh
#   echo $?    # esperar 0 (permitiu)
# =============================================================

set -u

input=$(cat)

# Extrair file_path do JSON usando bash puro
file_path=$(printf '%s' "$input" | sed -n 's/.*"file_path"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' | head -n 1)

# 1) Bloquear por nome de arquivo
blocked_filenames=(
    '\.env($|\.)'
    '\.env\.[a-z]+$'
    'secrets?/'
    'credentials?\.(json|yaml|yml|txt)$'
    '\.pem$'
    '\.key$'
    '\.p12$'
    '\.pfx$'
    'id_rsa($|\.)'
    '\.ssh/'
    'aws/credentials'
    '\.aws/'
    '\.npmrc$'
    '\.pypirc$'
)

file_path_lower=$(printf '%s' "$file_path" | tr '[:upper:]' '[:lower:]')

for pattern in "${blocked_filenames[@]}"; do
    if [[ "$file_path_lower" =~ $pattern ]]; then
        echo "❌ Gravação bloqueada por secrets-scanner: $file_path" >&2
        echo "Arquivo parece ser de segredo. Se for intencional, mover pra fora ou ajustar o hook." >&2
        exit 2
    fi
done

# 2) Bloquear por conteúdo (padrões de token comum)
# Extrai content de forma best-effort. JSON com conteúdo grande/escapado pode escapar dessa heurística;
# por isso o bloqueio por nome de arquivo é a defesa principal.
content=$(printf '%s' "$input" | sed -n 's/.*"content"[[:space:]]*:[[:space:]]*"\(.*\)"[[:space:]]*}*.*/\1/p' | head -n 1)

if [ -n "$content" ]; then
    blocked_content_patterns=(
        'AKIA[0-9A-Z]{16}'                          # AWS access key
        'aws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{40}'
        'ghp_[A-Za-z0-9]{30,}'                      # GitHub personal token
        'github_pat_[A-Za-z0-9_]{50,}'
        'sk-[A-Za-z0-9]{40,}'                       # OpenAI/Anthropic style
        '-----BEGIN[[:space:]]+(RSA|OPENSSH|DSA|EC|PGP)[[:space:]]+PRIVATE[[:space:]]+KEY-----'
        'xox[bpars]-[A-Za-z0-9-]{10,}'              # Slack token
    )

    for pattern in "${blocked_content_patterns[@]}"; do
        if [[ "$content" =~ $pattern ]]; then
            echo "❌ Gravação bloqueada por secrets-scanner: conteúdo parece conter segredo." >&2
            echo "Arquivo: $file_path" >&2
            echo "Padrão detectado: $pattern" >&2
            exit 2
        fi
    done
fi

# Permite
exit 0
