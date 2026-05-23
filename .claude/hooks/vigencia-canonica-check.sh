#!/usr/bin/env bash
# =============================================================
# vigencia-canonica-check.sh
# ADR-0030 + INV-VIG-001..004 — vigencia temporal canonica.
#
# Bloqueia migration/model que cria coluna `data_inicio_vigencia |
# data_fim_vigencia | iniciada_em | concluida_em | declarado_em |
# vigente_ate | encerrado_em` em entidade regulatoria.
#
# Allow via comentario: `# vigencia-canonica: skip -- <razao >=10 chars>`.
#
# Evento: PreToolUse(Write|Edit) em arquivos *.py sob src/infrastructure/*/{models.py,migrations/*.py}.
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

# Normaliza separadores Windows
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

case "$file_path_norm" in
    */models.py|*/migrations/*.py) ;;
    *) exit 0 ;;
esac

# Allow via skip comment
if printf '%s' "$content" | grep -qE 'vigencia-canonica:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

# Padroes proibidos (substituir por vigencia_inicio/vigencia_fim/revogado_em/motivo_revogacao)
bad_patterns='data_inicio_vigencia|data_fim_vigencia|iniciada_em|concluida_em|declarado_em|vigente_ate|encerrado_em|cancelada_em|cancelado_em'

if printf '%s' "$content" | grep -qE "($bad_patterns)\s*=\s*models\."; then
    echo "vigencia-canonica-check (ADR-0030 INV-VIG-001..004): coluna proibida em $file_path" >&2
    echo "Padrao canonico: (vigencia_inicio, vigencia_fim, revogado_em, motivo_revogacao)" >&2
    echo "Use VO JanelaVigencia de src/domain/shared/value_objects.py" >&2
    echo "Allow via: # vigencia-canonica: skip -- <razao com >=10 chars>" >&2
    exit 2
fi

exit 0
