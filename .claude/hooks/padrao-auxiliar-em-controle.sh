#!/usr/bin/env bash
# =============================================================
# padrao-auxiliar-em-controle.sh  (INV-PAD-007 / cl. 6.4.5 / C-8)
# GUARDA estatica da checagem de equipamentos auxiliares vigentes na porta
# `padrao_bloqueado_para_uso` (metrologia/padroes/query_service.py).
#
# INV-PAD-007 e 100% RUNTIME (compara data vs proximo_recal/validade de cada
# auxiliar vinculado). O enforcement REAL e o loop em `_bloqueado_por_auxiliar`
# dentro de `padrao_bloqueado_para_uso` + teste PG-real do caminho bloqueado
# (GATE-PAD-DRILL-LOCAL). Este hook NAO prova a regra — apenas impede que a
# checagem seja REMOVIDA, ENFRAQUECIDA (auxiliar so filtrado por soft-delete
# sem comparar vencimento) ou DESATIVADA por comentario, sem override formal.
#
# Escopo estreito: so age em */metrologia/padroes/query_service.py.
#
# Bloqueia (exit 2):
#   1. porta `padrao_bloqueado_para_uso` presente SEM nenhuma referencia a
#      auxiliar (VinculoAuxiliar / listar_auxiliares_vigentes_de / padrao_auxiliar_id)
#   2. comentario desativando INV-PAD-007 (# INV-PAD-007 ... skip/desativ/TODO/...)
#   3. auxiliar consultado (VinculoAuxiliar + revogado_em__isnull) SEM nenhuma
#      checagem de vencimento (proximo_recal / validade_certificado_rastreabilidade)
#      no arquivo — auxiliar so por soft-delete = INV-PAD-007 enfraquecida
#
# Override: '# padrao-auxiliar-em-controle: skip -- <razao com >=10 chars>'
#   (aceito so quando a checagem foi LEGITIMAMENTE movida pra outro arquivo;
#    a razao deve apontar onde a regra passou a viver + o teste que a cobre)
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/metrologia/padroes/query_service.py","content":"def padrao_bloqueado_para_uso(p):\n    return (False, \"\")"}}' | bash .claude/hooks/padrao-auxiliar-em-controle.sh
#   echo $?  # 2
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

# Escopo estreito: so a porta onde INV-PAD-007 deve viver.
case "$norm_path" in
    */metrologia/padroes/query_service.py) ;;
    *) exit 0 ;;
esac

# Override formal (>= 10 chars uteis apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*padrao-auxiliar-em-controle:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

tem_porta=$(printf '%s' "$content" | grep -cE 'def[[:space:]]+padrao_bloqueado_para_uso' || true)
tem_aux_ref=$(printf '%s' "$content" | grep -cE '(VinculoAuxiliar|listar_auxiliares_vigentes_de|padrao_auxiliar_id)' || true)
tem_soft_delete_aux=$(printf '%s' "$content" | grep -cE 'revogado_em__isnull' || true)
tem_saude_aux=$(printf '%s' "$content" | grep -cE '(proximo_recal|validade_certificado_rastreabilidade)' || true)

violacao=""

if printf '%s' "$content" | grep -qiE '#[[:space:]]*INV-PAD-007.*(skip|desativ|todo|fixme|pular|bypass|ignora)'; then
    violacao="checagem INV-PAD-007 desativada por comentario (sem override formal)"
elif [ "$tem_porta" -gt 0 ] && [ "$tem_aux_ref" -eq 0 ]; then
    violacao="porta padrao_bloqueado_para_uso sem nenhuma referencia a auxiliar (INV-PAD-007 ausente/removida)"
elif [ "$tem_aux_ref" -gt 0 ] && [ "$tem_soft_delete_aux" -gt 0 ] && [ "$tem_saude_aux" -eq 0 ]; then
    violacao="auxiliar consultado so por soft-delete (revogado_em) sem checar vencimento — INV-PAD-007 enfraquecida"
fi

if [ -n "$violacao" ]; then
    echo "padrao-auxiliar-em-controle: regra INV-PAD-007 (cl. 6.4.5) ausente/enfraquecida em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "Auxiliar (termo-higrometro/banho/fonte) vencido contamina o balanco de incerteza do principal." >&2
    echo "A porta padrao_bloqueado_para_uso DEVE percorrer VinculoAuxiliar vigentes e reavaliar a saude de cada auxiliar (fail-CLOSED)." >&2
    echo "Override (raro, exige aprovacao Roldao): '# padrao-auxiliar-em-controle: skip -- <onde a regra passou a viver + teste>'" >&2
    exit 2
fi

exit 0
