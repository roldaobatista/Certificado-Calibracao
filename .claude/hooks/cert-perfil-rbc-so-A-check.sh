#!/usr/bin/env bash
# =============================================================
# cert-perfil-rbc-so-A-check.sh — M8 Fatia 3 / INV-CER-PERFIL-001 + RESSALVA-001 (T-CER-055)
#
# Defende o anti-fraude do SELO do certificado: `tipo_acreditacao` (RBC vs NAO_RBC)
# NUNCA pode vir do payload da request. O valor efetivo so sai server-side de
# `perfil_e_acreditado(...)`/`tenant_perfil_e(...)` (perfil A E pontos cobertos);
# tenant B/C/D que forje `tipo_acreditacao=RBC` no JSON e fraude documental
# (cl. 8.1.3 / FAIL L6 invertido — ADR-0067/0075).
#
# Por que existir:
#   A barreira de runtime e a derivacao no use case (`perfil_e_acreditado(perfil)
#   and tem_rbc`) + INV-CER-PERFIL-001; este hook (camada A) impede REINTRODUZIR o
#   vetor pelo payload. Molde direto do `escopo-rbc-perfil-a-check.sh` (M6).
#
# Heuristica (so .py de src/, fora de teste/migration/doc):
#   BLOCK quando `tipo_acreditacao` recebe valor de fonte controlada pelo cliente
#   (request.data/POST/JSON/body, validated_data, payload, dados, resource[...],
#   initial_data) E o gate `perfil_e_acreditado(`/`tenant_perfil_e(` NAO aparece no
#   mesmo conteudo.
#
# Auto-allow (exit 0):
#   - tests/**, *_test.py, conftest.py ; **/migrations/** ; .md / nao-.py
#   - src/domain/metrologia/certificados/transicoes.py (lar do perfil_e_acreditado)
#
# Override: '# cert-perfil-rbc-so-A: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/x/views.py","content":"tipo_acreditacao = request.data[\"tipo\"]"}}' | bash .claude/hooks/cert-perfil-rbc-so-A-check.sh; echo $?  # 2
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
    *src/domain/metrologia/certificados/transicoes.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*cert-perfil-rbc-so-A:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Gate de dominio no mesmo conteudo isenta (valor passou por perfil server-side).
if printf '%s' "$content" | grep -qE '(perfil_e_acreditado|tenant_perfil_e)[[:space:]]*\('; then
    exit 0
fi

violacao=""
if printf '%s' "$content" | grep -qE 'tipo_acreditacao["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|\bdados\b|resource(\.get|\[)|initial_data)'; then
    violacao='tipo_acreditacao recebendo valor do payload da request (self-attestation do selo RBC proibida)'
fi

if [ -n "$violacao" ]; then
    echo "cert-perfil-rbc-so-A (INV-CER-PERFIL-001): selo RBC derivado de fonte nao-confiavel em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "" >&2
    echo "tipo_acreditacao=RBC so e licito quando o tenant e perfil A acreditado-vigente" >&2
    echo "E os pontos estao cobertos. Derive server-side:" >&2
    echo "  from src.domain.metrologia.certificados.transicoes import perfil_e_acreditado" >&2
    echo "  tipo = RBC if (perfil_e_acreditado(perfil_server_side) and tem_rbc) else NAO_RBC" >&2
    echo "onde perfil vem de Tenant.perfil_regulatorio (NUNCA do payload — ADR-0067)." >&2
    echo "Override: '# cert-perfil-rbc-so-A: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
