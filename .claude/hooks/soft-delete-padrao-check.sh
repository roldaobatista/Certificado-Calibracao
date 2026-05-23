#!/usr/bin/env bash
# =============================================================
# soft-delete-padrao-check.sh
# ADR-0031 + INV-SOFT-001..003 — soft-delete em 3 padroes (A|B|C).
#
# Bloqueia coluna com nome anti-padrao em migration/model sem declarar
# qual padrao se aplica.
#
# Padroes aceitos:
#   A — estado-maquina explicita (sem flag separada)
#   B — revogado_em (entidades imutaveis pos-emissao, WORM)
#   C — deletado_em (configuracao mutavel)
#
# Allow via: `# soft-delete-padrao: A|B|C -- <justificativa>`
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
    */models.py|*/migrations/*.py) ;;
    *) exit 0 ;;
esac

# Allow via skip comment
if printf '%s' "$content" | grep -qE 'soft-delete-padrao:\s*(A|B|C)\s*--\s*.{5,}'; then
    exit 0
fi

# Padroes anti (proibidos — exigem A, B ou C)
bad_patterns='excluido_em|removido_em|arquivado_em|inativo_em|is_deleted|is_active'

if printf '%s' "$content" | grep -qE "($bad_patterns)\s*=\s*models\."; then
    echo "soft-delete-padrao-check (ADR-0031 INV-SOFT-001): coluna anti-padrao em $file_path" >&2
    echo "Use 1 dos 3 padroes:" >&2
    echo "  A — estado-maquina explicita (sem flag separada)" >&2
    echo "  B — revogado_em (WORM imutavel pos-emissao)" >&2
    echo "  C — deletado_em (config mutavel — manager filtra IS NULL)" >&2
    echo "Allow via: # soft-delete-padrao: A|B|C -- <justificativa>" >&2
    exit 2
fi

exit 0
