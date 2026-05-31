#!/usr/bin/env bash
# =============================================================
# proc-controle-documental-check.sh — M7 Fatia 3 / INV-PROC-009 (T-PROC-047)
#
# Garante que a PUBLICACAO de procedimento exija controle documental completo
# (cl. 8.3.1): numero_revisao + aprovado_em + aprovado_por_id. O use case
# `publicar_procedimento` valida isso via `validar_controle_documental(...)`; sem
# essa barreira um procedimento "PUBLICADO" entra na resolucao `vigente_em` sem
# rastro de quem/quando aprovou — e os 3 campos entram no snapshot da calibracao
# (reconstituivel sem cruzar audit log).
#
# Por que existir:
#   ISO/IEC 17025 cl. 8.3.1 — documento controlado sem aprovacao registrada e NC.
#   A garantia de runtime e `validar_controle_documental` + TestINV_PROC_009; este
#   hook (camada A) impede que um edit silencioso remova a validacao do publicar.
#
# Heuristica (so no arquivo canonico do use case publicar):
#   Atua APENAS em '*/metrologia/procedimentos_calibracao/publicar_procedimento.py'.
#   Se o conteudo define a publicacao (classe PublicarProcedimentoInput OU def
#   executar) mas PERDE a chamada `validar_controle_documental(` -> BLOCK.
#
# Override: '# proc-controle-documental: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/metrologia/procedimentos_calibracao/publicar_procedimento.py","content":"class PublicarProcedimentoInput:\n    def executar(): pass"}}' | bash .claude/hooks/proc-controle-documental-check.sh; echo $?  # 2
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

# Atua so no arquivo canonico do use case de publicacao.
case "$norm_path" in
    */metrologia/procedimentos_calibracao/publicar_procedimento.py) ;;
    *) exit 0 ;;
esac

# So avaliamos quando o trecho DEFINE a publicacao (Input ou executar).
if ! printf '%s' "$content" | grep -qE 'PublicarProcedimentoInput|def[[:space:]]+executar[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*proc-controle-documental:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

if ! printf '%s' "$content" | grep -qE 'validar_controle_documental[[:space:]]*\('; then
    echo "proc-controle-documental (INV-PROC-009): publicar perdeu a validacao de controle documental em $file_path" >&2
    echo "" >&2
    echo "Publicar procedimento DEVE chamar validar_controle_documental(numero_revisao," >&2
    echo "aprovado_em, aprovado_por_id) — cl. 8.3.1. Sem os 3 campos um PUBLICADO" >&2
    echo "entra na resolucao vigente_em sem rastro de aprovacao e contamina o" >&2
    echo "snapshot da calibracao (nao reconstituivel)." >&2
    echo "Override: '# proc-controle-documental: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
