#!/usr/bin/env bash
# =============================================================
# pyproject-validator.sh
# Valida pyproject.toml em PreToolUse(Edit|Write).
# Pega bugs descobertos no drill F-A 2026-05-18:
#   - Bug 1: versao "0.1.0-foundation-f-a" violava PEP 440
#   - Bug 2: sintaxe "package[extras] = version" invalida pro Poetry
#
# Como funciona:
#   - Le tool_input.content / new_string + file_path
#   - Se nao for pyproject.toml -> pass
#   - Se for: valida (a) version PEP 440; (b) [tool.poetry] presente;
#     (c) dependencies com extras usam inline table {version=,extras=[]}
#
# Como testar:
#   echo '{"tool_input":{"file_path":"pyproject.toml","content":"[tool.poetry]\nversion=\"0.1-bad\""}}' | bash .claude/hooks/pyproject-validator.sh
#   echo $?  # esperar 2 (PEP 440 invalida)
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

norm_path="${file_path//\\//}"

# So aciona em pyproject.toml
case "$norm_path" in
    *pyproject.toml) ;;
    *) exit 0 ;;
esac

# =============================================================
# Validacao 1: versao PEP 440
# =============================================================
# PEP 440: N(.N)*[{a|b|c|rc}N][.postN][.devN][+<local>]
# Exemplos validos: 0.1.0, 0.1.0a1, 1.0.0.dev0, 1.0.0+local
# Invalidos (drill F-A): 0.1.0-foundation-f-a, 0.1-beta-2026
version_line=$(printf '%s' "$content" | grep -E '^version[[:space:]]*=' | head -1)
if [ -n "$version_line" ]; then
    # Extrai valor entre aspas
    version_value=$(printf '%s' "$version_line" | sed -E 's/^version[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/')
    if [ -n "$version_value" ]; then
        # Regex PEP 440 simplificada (cobre os casos comuns)
        if ! printf '%s' "$version_value" | grep -qE '^[0-9]+(\.[0-9]+)*((a|b|c|rc)[0-9]+)?(\.post[0-9]+)?(\.dev[0-9]+)?(\+[a-zA-Z0-9.]+)?$'; then
            echo "pyproject-validator: versao '$version_value' nao casa PEP 440 em $file_path" >&2
            echo "Formato esperado: N.N.N (ex: 0.1.0); N.N.NaN (ex: 0.1.0a1); N.N.N.devN (ex: 0.1.0.dev0)" >&2
            echo "Drill F-A 2026-05-18 descobriu 'foundation-f-a' como sufixo invalido." >&2
            exit 2
        fi
    fi
fi

# =============================================================
# Validacao 2: [tool.poetry] presente quando ha [tool.poetry.dependencies]
# =============================================================
if printf '%s' "$content" | grep -qE '^\[tool\.poetry\.dependencies\]'; then
    if ! printf '%s' "$content" | grep -qE '^\[tool\.poetry\]'; then
        echo "pyproject-validator: [tool.poetry.dependencies] presente mas [tool.poetry] ausente em $file_path" >&2
        exit 2
    fi
fi

# =============================================================
# Validacao 3: extras devem usar inline-table syntax
# Bug 2 do drill: "package[extras]" = "version" eh invalido. Correto:
#   package = {version = "X", extras = ["a", "b"]}
# =============================================================
# Pattern errado: linha que comeca com aspa + nome[extras] + = + aspa
linhas_erradas=$(printf '%s' "$content" | grep -nE '^"[a-zA-Z0-9_-]+\[[a-zA-Z0-9_,-]+\]"[[:space:]]*=[[:space:]]*"' || true)
if [ -n "$linhas_erradas" ]; then
    echo "pyproject-validator: dependencia com extras em sintaxe invalida em $file_path" >&2
    echo "$linhas_erradas" >&2
    echo "Use inline-table: package = {version = \"^X.Y\", extras = [\"a\", \"b\"]}" >&2
    echo "Drill F-A 2026-05-18 descobriu 'psycopg[binary,pool] = \"^3\"' como invalido." >&2
    exit 2
fi

exit 0
