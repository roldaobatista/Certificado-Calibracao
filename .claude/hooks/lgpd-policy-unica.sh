#!/usr/bin/env bash
# =============================================================
# lgpd-policy-unica.sh — INV-CLI-002 / SANEA-07
#
# Bloqueia (exit 2) hardcode de base legal LGPD fora de
# `politicas_lgpd.py` / `lgpd.py`. Toda decisão sobre base legal vem
# do agregado de política única. Mudar regra exige editar um lugar.
#
# Allowlist (auto-allow):
#   - src/infrastructure/audit/politicas_lgpd.py  (a primitiva mora aqui)
#   - src/infrastructure/clientes/lgpd.py          (enum + mapeamento)
#   - src/domain/comercial/clientes/**             (agregado de domínio)
#   - tests/**                                     (testa a política)
#   - **/migrations/**                             (data migration one-off)
#   - docs/**                                      (não é código)
#
# Override em arquivo fora da allowlist:
#   # lgpd-policy: skip -- <razão com >=10 chars>
#
# Detecta padrões proibidos:
#   - `base_legal == "CONSENTIMENTO"` / `if base_legal in (...)` (decisão de fluxo)
#   - hardcode comparativo da enumeração fora da política única
#
# Padrões PERMITIDOS (não bloqueados):
#   - default em FormField/serializer (aceite_lgpd_base_legal=...)
#   - constants em enum/migration
#   - assignment de payload (audit / event payload contém base_legal=...)
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/clientes/views.py","content":"if base_legal == \"CONSENTIMENTO\":\n    return ..."}}' | bash .claude/hooks/lgpd-policy-unica.sh
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

case "$norm_path" in
    *.py) ;;
    *) exit 0 ;;
esac

# AUTO-ALLOW
case "$norm_path" in
    *src/infrastructure/audit/politicas_lgpd.py) exit 0 ;;
    *src/infrastructure/clientes/lgpd.py) exit 0 ;;
    *src/domain/comercial/clientes/*) exit 0 ;;
    */tests/*|*/test_*|*_test.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    *docs/*) exit 0 ;;
esac

# Override com justificativa
if printf '%s' "$content" | grep -qE '#[[:space:]]*lgpd-policy:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Detecta padrões PROIBIDOS — decisão de fluxo hardcoded.
# 1. `if base_legal == "<ENUM>"` (igualdade direta em condicional)
# 2. `if base_legal in (...)` (containment em condicional)
# 3. comparação com `aceite_lgpd_base_legal == "<ENUM>"` em condicional
violacao=""

if printf '%s' "$content" | grep -qE '\bif[[:space:]]+(aceite_lgpd_)?base_legal[[:space:]]*==[[:space:]]*["'\'']CONSENTIMENTO["'\'']'; then
    violacao="if base_legal == \"CONSENTIMENTO\" — decisão LGPD fora da política única"
elif printf '%s' "$content" | grep -qE '\bif[[:space:]]+(aceite_lgpd_)?base_legal[[:space:]]*==[[:space:]]*["'\'']EXECUCAO_CONTRATO["'\'']'; then
    violacao="if base_legal == \"EXECUCAO_CONTRATO\" — decisão LGPD fora da política única"
elif printf '%s' "$content" | grep -qE '\bif[[:space:]]+(aceite_lgpd_)?base_legal[[:space:]]*==[[:space:]]*["'\'']OBRIG_LEGAL["'\'']'; then
    violacao="if base_legal == \"OBRIG_LEGAL\" — decisão LGPD fora da política única"
elif printf '%s' "$content" | grep -qE '\bif[[:space:]]+(aceite_lgpd_)?base_legal[[:space:]]*==[[:space:]]*["'\'']LEGITIMO_INTERESSE["'\'']'; then
    violacao="if base_legal == \"LEGITIMO_INTERESSE\" — decisão LGPD fora da política única"
elif printf '%s' "$content" | grep -qE '\bif[[:space:]]+(aceite_lgpd_)?base_legal[[:space:]]+in[[:space:]]*[\(\[\{]'; then
    violacao="if base_legal in (...) — decisão LGPD fora da política única"
fi

if [ -n "$violacao" ]; then
    echo "lgpd-policy-unica (INV-CLI-002): $violacao em $file_path" >&2
    echo "Decisão de base legal mora em src/infrastructure/audit/politicas_lgpd.py" >&2
    echo "(ou src/domain/comercial/clientes/lgpd_policy.py quando agregado existir)." >&2
    echo "Importe a função decisória (ex: base_legal_aplicavel_pos_revogacao) e chame-a." >&2
    echo "Override (raro): adicione '# lgpd-policy: skip -- <razão com >=10 chars>'" >&2
    exit 2
fi

exit 0
