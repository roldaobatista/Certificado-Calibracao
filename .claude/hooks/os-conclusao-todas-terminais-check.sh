#!/usr/bin/env bash
# =============================================================
# os-conclusao-todas-terminais-check.sh
# INV-OS-ATIV-001 — OS so transiciona para CONCLUIDA quando TODAS as
# atividades estao em estado terminal (CONCLUIDA, NAO_CONFORME, CANCELADA).
#
# Estado da OS e COMPUTADO a partir das atividades — nao setado diretamente.
#
# Bloqueia codigo que set OS.estado = 'CONCLUIDA' diretamente em
# src/infrastructure/os/ ou src/domain/operacao/os/ (Marco 3).
# Permite apenas via trigger PG ou service `recomputar_estado_os(os_id)`.
#
# Allow via: `# os-conclusao: skip -- <razao>`
# =============================================================

set -u
input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

case "$file_path_norm" in
    *.py) ;;
    *) exit 0 ;;
esac
case "$file_path_norm" in
    */tests/*|*/test_*|*_test.py|*/migrations/*) exit 0 ;;
esac

# So aplica a arquivos do modulo os
case "$file_path_norm" in
    */infrastructure/os/*|*/domain/operacao/os/*) ;;
    *) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE 'os-conclusao:\s*skip\s*--\s*.{5,}'; then
    exit 0
fi

# Bloqueia atribuicao direta de estado CONCLUIDA
if printf '%s' "$content" | grep -qE "(OS|os)\.estado\s*=\s*['\"]CONCLUIDA['\"]" || \
   printf '%s' "$content" | grep -qE "os\.estado\s*=\s*EstadoOS\.CONCLUIDA"; then
    if ! printf '%s' "$content" | grep -qE 'recomputar_estado_os|trigger_os_estado'; then
        echo "os-conclusao-todas-terminais-check (INV-OS-ATIV-001): set OS.estado=CONCLUIDA direto em $file_path" >&2
        echo "Estado da OS e COMPUTADO de atividades — use recomputar_estado_os(os_id)." >&2
        echo "Allow via: # os-conclusao: skip -- <razao>" >&2
        exit 2
    fi
fi

exit 0
