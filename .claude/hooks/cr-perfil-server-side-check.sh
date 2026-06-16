#!/usr/bin/env bash
# =============================================================
# cr-perfil-server-side-check.sh — contas-receber Fatia 3d / INV-FIN-PERFIL-001 (T-CR-047)
#
# Defesa anti-fraude L6: a `categoria_receita` perfil-aware (RBC so perfil A — ADR-0067)
# decorre do perfil regulatorio, que NUNCA pode vir do payload da request — senao um
# tenant D forja um titulo de calibracao RBC (fraude documental, cl. 8.1.3). O perfil
# efetivo so sai server-side: `obter_perfil_tenant_corrente()` (ContextVar do middleware,
# lancamento manual) OU `envelope["perfil_no_evento"]` (consumer, D-CR-6); a trava roda
# no use case (validacao perfil-aware — ADR-0073), nunca no DRF.
#
# Heuristica (so .py em path *contas_receber*, fora de teste/migration/doc/dominio):
#   BLOCK quando QUALQUER linha de codigo (nao comentario) atribui `perfil` a partir de
#   fonte do cliente (request.data/POST/JSON/body, validated_data, payload, initial_data).
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py ; path nao-*contas_receber*
#   - src/domain/contas_receber/** (dominio puro recebe perfil por parametro)
#
# Override: '# cr-perfil-server-side: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/contas_receber/views.py","content":"perfil = request.data[\"perfil\"]"}}' | bash .claude/hooks/cr-perfil-server-side-check.sh; echo $?  # 2
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

# So arquivos da frente contas-receber.
case "$norm_path" in
    *contas_receber*) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    */domain/contas_receber/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*cr-perfil-server-side:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Line-oriented: bloqueia se QUALQUER linha de codigo (nao comentario) atribui `perfil`
# a partir do payload — mesmo que um token server-side legitimo apareca noutra linha.
# `envelope["perfil_no_evento"]`/`obter_perfil_tenant_corrente()` NAO casam (fonte server).
if printf '%s' "$content" | grep -vE '^[[:space:]]*#' \
    | grep -qE 'perfil["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|initial_data)'; then
    echo "cr-perfil-server-side (INV-FIN-PERFIL-001): perfil de titulo vindo do payload em $file_path" >&2
    echo "O perfil regulatorio NUNCA vem da request (ADR-0067) — tenant D forjaria titulo RBC." >&2
    echo "Derive server-side e valide no use case:" >&2
    echo "  perfil = obter_perfil_tenant_corrente()        # lancamento manual" >&2
    echo "  perfil = envelope[\"perfil_no_evento\"]          # consumer (D-CR-6)" >&2
    echo "Override: '# cr-perfil-server-side: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
