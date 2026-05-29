#!/usr/bin/env bash
# =============================================================
# shewhart-perfil-A.sh  (INV-PAD-008 / ADR-0070 + ADR-0067)
# Garante que todo use case de padroes que DISPARA carta de controle Shewhart
# esteja gated por perfil A (laboratorio acreditado CGCRE) no MESMO arquivo.
#
# Cartas Shewhart e o registro WORM AnaliseCartaControle sao EXCLUSIVOS de
# tenant perfil A. Tenant B/C/D que calcule/registre carta aparenta controle
# estatistico de lab acreditado que nao possui = fraude regulatoria.
#
# Escopo: src/application/metrologia/padroes/*.py (use cases). O hook so age
# quando o conteudo contem um GATILHO Shewhart de CODIGO; arquivos de padroes
# sem gatilho (cadastrar/baixar/etc) passam direto. Motor puro do dominio
# (src/domain/.../shewhart.py) e entities/enums NAO entram no escopo (definicao
# != disparo).
#
# Bloqueia (exit 2): gatilho Shewhart presente E nenhum sinal de gate perfil A.
#   Gatilhos: shewhart.calcular_limites(/detectar_violacoes( ; import shewhart ;
#             AnaliseCartaControleSnapshot( ; RegistrarAnaliseCarta ;
#             RegraWesternElectric / ViolacaoWesternElectric / LimitesControle
#   Gate aceito (qualquer um): tenant_e_perfil_a | tenant_perfil_e |
#             PerfilNaoPermite | obter_perfil_tenant_corrente | exige_perfil_a |
#             perfil_a | comentario INV-PAD-008
#
# Override: '# shewhart-perfil-A: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/metrologia/padroes/x.py","content":"from src.domain.metrologia.padroes import shewhart\nshewhart.calcular_limites(s)"}}' | bash .claude/hooks/shewhart-perfil-A.sh
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

# Escopo: use cases de padroes (application). Demais paths exit 0.
case "$norm_path" in
    */application/metrologia/padroes/*.py) ;;
    *) exit 0 ;;
esac

# Pula testes
case "$norm_path" in
    */tests/*|*/test_*|*_test.py) exit 0 ;;
esac

# Override com justificativa explicita (>= 10 chars uteis apos --)
if printf '%s' "$content" | grep -qE '#[[:space:]]*shewhart-perfil-A:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gatilho Shewhart de CODIGO (nao prosa/docstring).
gatilho=""
if printf '%s' "$content" | grep -qE 'shewhart\.(calcular_limites|detectar_violacoes)\('; then
    gatilho="shewhart.calcular_limites/detectar_violacoes()"
elif printf '%s' "$content" | grep -qE '(import[[:space:]]+shewhart|import[[:space:]].*[[:space:]]shewhart\b|[[:space:]]shewhart[[:space:]]*$)'; then
    gatilho="import do motor shewhart"
elif printf '%s' "$content" | grep -qE 'AnaliseCartaControleSnapshot\('; then
    gatilho="construcao de AnaliseCartaControleSnapshot"
elif printf '%s' "$content" | grep -qE 'RegistrarAnaliseCarta'; then
    gatilho="use case RegistrarAnaliseCarta"
elif printf '%s' "$content" | grep -qE '(RegraWesternElectric|ViolacaoWesternElectric|LimitesControle)'; then
    gatilho="tipos do motor Western Electric"
fi

[ -z "$gatilho" ] && exit 0

# Sinal de gate de perfil A (qualquer um basta).
if printf '%s' "$content" | grep -qE '(tenant_e_perfil_a|tenant_perfil_e|PerfilNaoPermite|obter_perfil_tenant_corrente|exige_perfil_a|perfil_a|INV-PAD-008)'; then
    exit 0
fi

echo "shewhart-perfil-A: use case dispara carta Shewhart SEM gate de perfil A em $file_path" >&2
echo "Gatilho detectado: $gatilho" >&2
echo "Cartas Shewhart / AnaliseCartaControle sao EXCLUSIVAS de tenant perfil A (ADR-0067/ADR-0070 + INV-PAD-008)." >&2
echo "Traga o gate no mesmo arquivo, ex: 'if not inp.tenant_e_perfil_a: raise PerfilNaoPermiteCartaError'" >&2
echo "ou 'allowed, _ = tenant_perfil_e([\"A\"])'. Modelo: registrar_analise_carta_controle.py / registrar_verificacao_intermediaria.py." >&2
echo "Override (raro, exige aprovacao Roldao): '# shewhart-perfil-A: skip -- <razao com >=10 chars>'" >&2
exit 2
