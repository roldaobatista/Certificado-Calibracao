#!/usr/bin/env bash
# =============================================================
# lic-perfil-cgcre-check.sh — M9 Fatia 4 / INV-LIC-PERFIL-001 (T-LIC-062)
#
# Defesa anti-fraude L6: o cadastro de `ACREDITACAO_CGCRE` exige perfil A/B/C, e o
# perfil regulatorio NUNCA pode vir do payload da request (ADR-0067) — senao um
# tenant D forja uma acreditacao RBC (fraude documental viavel, cl. 8.1.3). O perfil
# efetivo so sai server-side (`obter_perfil_tenant_corrente`/`tenant_perfil_e`/
# `_contexto_com_perfil`) e e validado por `validar_tipo_x_perfil`.
#
# Heuristica (so .py de src/, fora de teste/migration/doc/transicoes):
#   BLOCK quando o conteudo menciona `ACREDITACAO_CGCRE` E atribui `perfil` a partir
#   de fonte controlada pelo cliente (request.data/POST/JSON/body, validated_data,
#   payload, dados, resource[...], initial_data) SEM o gate server-side no mesmo conteudo.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py
#   - src/domain/metrologia/licencas_acreditacoes/transicoes.py (lar do validar_tipo_x_perfil)
#   - conteudo com `validar_tipo_x_perfil(`/`obter_perfil_tenant_corrente`/`tenant_perfil_e(`/`_contexto_com_perfil`
#
# Override: '# lic-perfil-cgcre: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/x/views.py","content":"tipo=ACREDITACAO_CGCRE\nperfil = request.data[\"perfil\"]"}}' | bash .claude/hooks/lic-perfil-cgcre-check.sh; echo $?  # 2
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

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    *src/domain/metrologia/licencas_acreditacoes/transicoes.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*lic-perfil-cgcre:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Sem contexto CGCRE no conteudo, nao e dominio deste hook.
if ! printf '%s' "$content" | grep -qE 'ACREDITACAO_CGCRE'; then
    exit 0
fi

# Gate server-side no mesmo conteudo isenta.
if printf '%s' "$content" | grep -qE '(validar_tipo_x_perfil|obter_perfil_tenant_corrente|tenant_perfil_e|_contexto_com_perfil)[[:space:]]*\(?'; then
    exit 0
fi

if printf '%s' "$content" | grep -qE 'perfil["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|\bdados\b|resource(\.get|\[)|initial_data)'; then
    echo "lic-perfil-cgcre (INV-LIC-PERFIL-001): perfil de cadastro CGCRE vindo do payload em $file_path" >&2
    echo "O perfil regulatorio NUNCA vem da request (ADR-0067) — tenant D forjaria acreditacao RBC." >&2
    echo "Derive server-side e valide:" >&2
    echo "  perfil = obter_perfil_tenant_corrente()  # ContextVar populado pelo middleware" >&2
    echo "  validar_tipo_x_perfil(tipo=tipo, perfil=perfil, escopo=escopo)  # 403 se D" >&2
    echo "Override: '# lic-perfil-cgcre: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
