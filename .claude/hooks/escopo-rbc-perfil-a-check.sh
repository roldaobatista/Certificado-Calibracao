#!/usr/bin/env bash
# =============================================================
# escopo-rbc-perfil-a-check.sh — M6 P7 / INV-ECMC-002 (T-ECMC-061)
#
# Defende o anti-fraude do escopo CGCRE: `rbc_acreditado` (o selo RBC) NUNCA
# pode vir do payload da request nem ser copiado cru da intencao do usuario
# (`rbc_solicitado`). O valor efetivo so sai de `rbc_efetivo(...)` no dominio
# (`src/domain/metrologia/escopos_cmc/transicoes.py`), que forca False quando o
# tenant nao e perfil A (ADR-0067 / FAIL L6 SAN-PERFIL).
#
# Por que existir:
#   ISO/IEC 17025 cl. 8.1.3 + INV-ECMC-002 + INV-015 — tenant B/C/D que se passe
#   por RBC (acreditado CGCRE) e fraude regulatoria / propaganda enganosa, com
#   Roldao solidario (R-039). A barreira de runtime e `rbc_efetivo`; este hook e
#   a camada A (pre-commit) que impede REINTRODUZIR o vetor pelo payload.
#
# Heuristica (so .py de src/, fora de teste/migration/doc):
#   BLOCK quando `rbc_acreditado` recebe valor de uma fonte controlada pelo
#   cliente (request.data/POST/JSON/body, validated_data, payload, dados,
#   resource[...], initial_data) OU e copiado cru de `rbc_solicitado` —
#   e o gate `rbc_efetivo(` NAO aparece no mesmo conteudo.
#
# Auto-allow (exit 0):
#   - tests/**, *_test.py, conftest.py
#   - **/migrations/**
#   - .md / nao-.py
#   - src/domain/metrologia/escopos_cmc/transicoes.py (lar do rbc_efetivo)
#
# Override: '# escopo-rbc-perfil-a: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/x/views.py","content":"rbc_acreditado = request.data[\"rbc\"]"}}' | bash .claude/hooks/escopo-rbc-perfil-a-check.sh; echo $?  # 2
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
    *src/domain/metrologia/escopos_cmc/transicoes.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*escopo-rbc-perfil-a:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# O gate de dominio aplicado no mesmo conteudo isenta (valor ja passou por rbc_efetivo).
if printf '%s' "$content" | grep -qE 'rbc_efetivo[[:space:]]*\('; then
    exit 0
fi

violacao=""

# 1. rbc_acreditado vindo do payload da request / serializer / dict de input.
if printf '%s' "$content" | grep -qE 'rbc_acreditado["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|\bdados\b|resource(\.get|\[)|initial_data)'; then
    violacao='rbc_acreditado recebendo valor do payload da request (self-attestation proibida)'
# 2. rbc_acreditado copiado cru da intencao (rbc_solicitado) sem o gate rbc_efetivo.
elif printf '%s' "$content" | grep -qE 'rbc_acreditado["'"'"']?[[:space:]]*[:=][[:space:]]*[^=].*rbc_solicitado'; then
    violacao='rbc_acreditado = rbc_solicitado (intencao crua) — falta passar por rbc_efetivo()'
fi

if [ -n "$violacao" ]; then
    echo "escopo-rbc-perfil-a (INV-ECMC-002): selo RBC derivado de fonte nao-confiavel em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "" >&2
    echo "rbc_acreditado=True so e licito para tenant perfil A (ADR-0067). B/C/D" >&2
    echo "declaram capacidade interna (rbc_acreditado FORCADO False — ADR-0075)." >&2
    echo "Use o gate de dominio:" >&2
    echo "  from src.domain.metrologia.escopos_cmc.transicoes import rbc_efetivo" >&2
    echo "  rbc = rbc_efetivo(rbc_solicitado=inp.rbc_solicitado, perfil=perfil_server_side)" >&2
    echo "onde perfil vem de Tenant.perfil_regulatorio (NUNCA do payload)." >&2
    echo "Override: '# escopo-rbc-perfil-a: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
