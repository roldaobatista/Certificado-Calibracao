#!/usr/bin/env bash
# =============================================================
# fk-pii-anonimizavel-check.sh
# ADR-0032 + INV-ANON-001..004 — FK cross-modulo para entidade PII.
#
# Bloqueia `models.ForeignKey(Cliente|Usuario|ResponsavelTecnicoTenant)`
# em entidade regulatoria Padrao B (revogado_em) sem o par
# `*_referencia_hash` + `*_referencia_key_id` (VO ReferenciaPIIAnonimizavel).
#
# Allow via: `# fk-pii-anonimizavel: skip -- <razao>`
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
    */models.py) ;;
    *) exit 0 ;;
esac

# Allow via skip
if printf '%s' "$content" | grep -qE 'fk-pii-anonimizavel:\s*skip\s*--\s*.{5,}'; then
    exit 0
fi

# Detecta FK a entidades PII em arquivo que aparenta ser Padrao B (revogado_em)
fk_pii_re='models\.ForeignKey\([[:space:]]*"?(Cliente|Usuario|ResponsavelTecnicoTenant)"?'
padrao_b_re='revogado_em\s*=\s*models\.'

if printf '%s' "$content" | grep -qE "$fk_pii_re" && \
   printf '%s' "$content" | grep -qE "$padrao_b_re"; then
    # E faltam campos do par
    if ! printf '%s' "$content" | grep -qE '_referencia_hash\s*=\s*models\.' || \
       ! printf '%s' "$content" | grep -qE '_referencia_key_id\s*=\s*models\.'; then
        echo "fk-pii-anonimizavel-check (ADR-0032 INV-ANON-001): entidade Padrao B com FK a PII sem par hash+key_id em $file_path" >&2
        echo "Adicione: *_referencia_hash (CharField 128 NOT NULL) + *_referencia_key_id (CharField 32 NOT NULL)" >&2
        echo "Use VO ReferenciaPIIAnonimizavel de src/domain/shared/value_objects.py" >&2
        echo "Allow via: # fk-pii-anonimizavel: skip -- <razao>" >&2
        exit 2
    fi
fi

exit 0
