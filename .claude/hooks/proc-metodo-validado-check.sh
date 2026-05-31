#!/usr/bin/env bash
# =============================================================
# proc-metodo-validado-check.sh — M7 Fatia 3 / INV-PROC-010 (T-PROC-047)
#
# Mantem DOCUMENTADO o estado fail-open LAZY da qualificacao de metodo (cl. 7.2.2,
# paralelo ADR-0066). Hoje `metodo_exige_validacao_pendente(...)` so EMITE AVISO
# (resultado vira `aviso_validacao_metodo`); o bloqueio duro de perfil A +
# NAO_NORMALIZADO/MODIFICADO sem `registro_validacao_id` so entra quando o modulo
# `licencas-acreditacoes` existir (GATE-PROC-METODO-VALIDADO). Virar fail-closed
# ANTES disso trava laboratorio A legitimo que ainda nao tem onde registrar a
# validacao do metodo.
#
# Por que existir:
#   Flip prematuro lazy->bloqueio = regressao silenciosa que quebra publicacao de
#   procedimento de metodo proprio enquanto a evidencia de validacao nao tem
#   modelo. O AVISO e o comportamento correto no MVP.
#
# Heuristica (so nos use cases canonicos que consomem o helper):
#   Atua em '*/procedimentos_calibracao/{cadastrar,publicar}_procedimento.py'. Se o
#   resultado de `metodo_exige_validacao_pendente(...)` GATEIA um bloqueio
#   (padrao `if ... metodo_exige_validacao_pendente`) -> BLOCK, a menos que o
#   marcador `GATE-PROC-METODO-VALIDADO` esteja presente (gate ativado,
#   licencas-acreditacoes ja existe) ou skip override.
#
# Override: '# proc-metodo-validado: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/metrologia/procedimentos_calibracao/cadastrar_procedimento.py","content":"    if metodo_exige_validacao_pendente(tipo_metodo=t):\n        raise MetodoNaoValidado()"}}' | bash .claude/hooks/proc-metodo-validado-check.sh; echo $?  # 2
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

# Atua so nos use cases que consomem o helper lazy.
case "$norm_path" in
    */metrologia/procedimentos_calibracao/cadastrar_procedimento.py) ;;
    */metrologia/procedimentos_calibracao/publicar_procedimento.py) ;;
    *) exit 0 ;;
esac

# So avaliamos quando o trecho usa o helper.
if ! printf '%s' "$content" | grep -qE 'metodo_exige_validacao_pendente'; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*proc-metodo-validado:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gate ativado (licencas-acreditacoes existe): permite o bloqueio se documentado.
if printf '%s' "$content" | grep -qE 'GATE-PROC-METODO-VALIDADO'; then
    exit 0
fi

# Sinal de flip prematuro: o helper gateia um if (bloqueio), em vez de virar aviso.
if printf '%s' "$content" | grep -qE 'if[^\n]*metodo_exige_validacao_pendente'; then
    echo "proc-metodo-validado (INV-PROC-010): flip prematuro lazy->bloqueio em $file_path" >&2
    echo "" >&2
    echo "metodo_exige_validacao_pendente() e fail-open LAZY no MVP (cl. 7.2.2 /" >&2
    echo "paralelo ADR-0066): o resultado deve virar AVISO (aviso_validacao_metodo)," >&2
    echo "nunca gatear um raise/bloqueio. O bloqueio duro so entra com" >&2
    echo "licencas-acreditacoes (GATE-PROC-METODO-VALIDADO) — referencie esse gate" >&2
    echo "no codigo quando ativar, ou use skip." >&2
    echo "Override: '# proc-metodo-validado: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
