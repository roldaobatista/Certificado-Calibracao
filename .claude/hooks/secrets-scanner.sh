#!/usr/bin/env bash
# =============================================================
# secrets-scanner.sh
# Bloqueia gravacao acidental de arquivos com segredos.
# Evento: PreToolUse(Write|Edit)
#
# Como funciona:
#   - Claude Code envia JSON via stdin com {tool_input: {file_path, content}}
#     (Write) ou {tool_input: {file_path, new_string}} (Edit).
#   - Este script usa perl (JSON::PP, nativo) pra decodificar o JSON
#     corretamente, inclusive content com aspas escapadas. Sed puro
#     vazava: cortava na primeira aspa e o scanner via so um pedaco.
#   - Bloqueia se file_path for arquivo de segredo, OU se content/new_string
#     contem padrao de chave/token conhecido.
#   - Exit 0 = permite | Exit 2 = bloqueia.
#
# Como testar manualmente:
#   echo '{"tool_input":{"file_path":".env","content":"FOO=bar"}}' | bash .claude/hooks/secrets-scanner.sh
#   echo $?    # esperar 2 (bloqueia pelo nome)
#
#   echo '{"tool_input":{"file_path":"src/foo.ts","content":"const x = 1"}}' | bash .claude/hooks/secrets-scanner.sh
#   echo $?    # esperar 0
#
#   Regressao (token AWS-like dentro de string escapada):
#     printf '%s' '{"tool_input":{"file_path":"src/x.ts","content":"const k=\"<AWS_KEY_16_CHARS>\""}}' \
#       | bash .claude/hooks/secrets-scanner.sh
#     # com chave AWS real no lugar do placeholder, exit=2.
# =============================================================

set -u

input=$(cat)

# Extrai file_path + content/new_string via perl + JSON::PP.
# Saida: 2 linhas — file_path na 1a, content na 2a (vazias se ausentes).
parsed=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $fp = $j->{tool_input}{file_path} // "";
    my $c  = $j->{tool_input}{content} // $j->{tool_input}{new_string} // "";
    $fp =~ s/\n/ /g;
    $c  =~ s/\x00//g;
    print $fp, "\n";
    print $c;
' 2>/dev/null)

file_path=$(printf '%s' "$parsed" | head -n 1)
content=$(printf '%s' "$parsed" | tail -n +2)

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
        echo "Gravacao bloqueada por secrets-scanner: $file_path" >&2
        echo "Arquivo parece ser de segredo. Se for intencional, mover pra fora ou ajustar o hook." >&2
        exit 2
    fi
done

# 2) Bloquear por conteudo (padroes de token comum)
if [ -n "$content" ]; then
    blocked_content_patterns=(
        'AKIA[0-9A-Z]{16}'                          # AWS access key
        'aws_secret_access_key[[:space:]]*=[[:space:]]*[A-Za-z0-9/+=]{40}'
        'ghp_[A-Za-z0-9]{30,}'                      # GitHub personal token
        'github_pat_[A-Za-z0-9_]{50,}'
        'sk-[A-Za-z0-9]{40,}'                       # OpenAI / Anthropic style
        '-----BEGIN[[:space:]]+(RSA|OPENSSH|DSA|EC|PGP)[[:space:]]+PRIVATE[[:space:]]+KEY-----'
        'xox[bpars]-[A-Za-z0-9-]{10,}'              # Slack token
    )

    for pattern in "${blocked_content_patterns[@]}"; do
        if [[ "$content" =~ $pattern ]]; then
            echo "Gravacao bloqueada por secrets-scanner: conteudo parece conter segredo." >&2
            echo "Arquivo: $file_path" >&2
            echo "Padrao detectado: $pattern" >&2
            exit 2
        fi
    done
fi

exit 0
