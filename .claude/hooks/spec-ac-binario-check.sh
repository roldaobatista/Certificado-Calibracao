#!/usr/bin/env bash
# =============================================================
# spec-ac-binario-check.sh
# Auditor-produto lente 5 — AC binarios em spec FORWARD.
#
# Em docs/faseamento/M*/spec.md e docs/dominios/**/spec.md (FORWARD), os
# Acceptance Criteria devem ser BINARIOS (endpoint + status + payload
# verificavel), nao vagos ("deve funcionar bem", "adequado", "razoavel",
# "suficiente").
#
# Bloqueia commit que introduza palavras-coringa em spec FORWARD.
# Allow via: `# spec-ac-binario: skip -- <razao>`
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

# So spec FORWARD
case "$file_path_norm" in
    */faseamento/*/spec.md|*/dominios/*/spec.md) ;;
    *) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE 'spec-ac-binario:\s*skip\s*--\s*.{5,}'; then
    exit 0
fi

# Palavras-coringa em AC (caso-insensitivo)
# Restringe matching a contextos suspeitos: linhas AC-* ou que comecem com "-"
ac_lines=$(printf '%s' "$content" | grep -iE '^(-|AC-[A-Z]+-[0-9])' || true)
[ -z "$ac_lines" ] && exit 0

bad_words='deve funcionar bem|funciona adequadamente|de forma adequada|razoavel|razoável|suficiente|aceitavel|aceitável|deve ser bom|deve ser robusto'

if printf '%s' "$ac_lines" | grep -iqE "$bad_words"; then
    echo "spec-ac-binario-check (auditor-produto): AC vago em $file_path" >&2
    echo "AC FORWARD devem ser binarios: endpoint X retorna 201 com payload Y." >&2
    echo "Palavras-coringa detectadas: ($bad_words)" >&2
    echo "Allow via: # spec-ac-binario: skip -- <razao>" >&2
    exit 2
fi

exit 0
