#!/usr/bin/env bash
# =============================================================
# frontmatter-revisado-em-check.sh
# Auditoria projeto-inteiro lente 5 (auditor-produto) — 33/49 PRDs sem
# `revisado-em` em frontmatter. Hook bloqueia novo prd.md sem o campo.
#
# Aplica a: docs/dominios/**/prd.md, docs/**/spec.md, docs/adr/*.md
# Exige: owner, revisado-em, status no frontmatter YAML.
#
# Allow via: `# frontmatter-revisado-em: skip -- <razao>`
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

# Aplica a docs canonicos
case "$file_path_norm" in
    */prd.md|*/spec.md|*/adr/*.md|*/conformidade/*.md|*/governanca/*.md) ;;
    *) exit 0 ;;
esac

# Pula templates
case "$file_path_norm" in
    *_TEMPLATE*|*template*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE 'frontmatter-revisado-em:\s*skip\s*--\s*.{5,}'; then
    exit 0
fi

# Verifica frontmatter YAML
if ! printf '%s' "$content" | head -1 | grep -qE '^---$'; then
    echo "frontmatter-revisado-em-check: arquivo sem frontmatter YAML em $file_path" >&2
    echo "Exigido: --- owner: ... revisado-em: YYYY-MM-DD status: draft|stable|deprecated ---" >&2
    exit 2
fi

# Extrai frontmatter (entre os 2 primeiros ---) e valida campos
header=$(printf '%s' "$content" | awk '/^---$/{c++; next} c==1' | head -50)

missing=()
printf '%s' "$header" | grep -qE '^owner:' || missing+=("owner")
printf '%s' "$header" | grep -qE '^revisado-em:[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}' || missing+=("revisado-em (YYYY-MM-DD)")
printf '%s' "$header" | grep -qE '^status:[[:space:]]*(draft|stable|deprecated|minuta|proposta|aceito)' || missing+=("status")

if [ ${#missing[@]} -gt 0 ]; then
    echo "frontmatter-revisado-em-check: campos faltando em $file_path:" >&2
    for m in "${missing[@]}"; do echo "  - $m" >&2; done
    echo "Allow via: # frontmatter-revisado-em: skip -- <razao>" >&2
    exit 2
fi

exit 0
