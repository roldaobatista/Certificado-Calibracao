#!/usr/bin/env bash
# =============================================================
# fiscal-anti-rbc-em-descricao.sh — fiscal/NFS-e Fatia 3 / INV-FIS-007 (T-FIS-041)
#
# Uso indevido de acreditacao (ISO 17025 cl. 8.1.3 / ADR-0075): a descricao impressa
# da NFS-e de perfis B/C/D NAO pode conter "RBC"/"ISO 17025"/"acreditada(o)" — senao
# o tomador interpreta servico nao-acreditado como acreditado. "Calibracao" sozinha e
# generica e permitida (decisao Roldao D-FIS-7); o proibido e o QUALIFICADOR acreditado.
#
# Heuristica (so .py em path *fiscal*, fora de teste/migration/doc):
#   BLOCK quando uma linha de codigo atribui/define `service_description`/
#   `descricao_servico`/`descricao` com STRING LITERAL contendo `RBC`/`ISO 17025`/
#   `acreditad` (hardcode de qualificador acreditado na descricao da nota).
#
# A renderizacao impressa (PDF/template) tera validacao em runtime quando existir
# (diferida — GATE). Este hook e defesa estatica contra hardcode.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py ; path nao-*fiscal*
#   - linhas de comentario/docstring (iniciadas por # ou contendo so doc)
#
# Override: '# fiscal-anti-rbc-descricao: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/fiscal/x.py","content":"service_description = \"Calibracao RBC acreditada\""}}' | bash .claude/hooks/fiscal-anti-rbc-em-descricao.sh; echo $?  # 2
# =============================================================

set -u

input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/;
    my $raw = <STDIN>;
    my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
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

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    *fiscal*) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*fiscal-anti-rbc-descricao:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Linhas de codigo (nao comentario) que definem descricao com qualificador acreditado.
# 1) ignora linhas iniciadas por # (comentario/docstring de bloco simples)
# 2) exige token de descricao + literal proibido na MESMA linha
if printf '%s' "$content" \
    | grep -vE '^[[:space:]]*#' \
    | grep -qiE '(service_description|descricao_servico|descricao)[^#]*["'"'"'][^"'"'"']*(RBC|ISO[[:space:]]*17025|acreditad)'; then
    echo "fiscal-anti-rbc-descricao (INV-FIS-007): qualificador acreditado hardcoded na descricao da NFS-e em $file_path" >&2
    echo "Perfis B/C/D nao podem exibir 'RBC'/'ISO 17025'/'acreditada' na descricao (cl. 8.1.3 / ADR-0075)." >&2
    echo "'Calibracao' sozinha e permitida; o qualificador acreditado nao." >&2
    echo "Override: '# fiscal-anti-rbc-descricao: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
