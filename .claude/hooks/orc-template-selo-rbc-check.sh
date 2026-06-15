#!/usr/bin/env bash
# =============================================================
# orc-template-selo-rbc-check.sh — orcamentos T-ORC-039 / INV-ORC-SELO-RBC (D-ORC-13)
#
# Template com `selo_rbc=True` SO pode existir em tenant perfil A (matriz feature×perfil
# ADR-0067 / NIT-DICLA-021). Perfil B/C/D nao pode ostentar referencia a acreditacao
# RBC/ILAC-MRA. O gate e server-side (perfil NUNCA do payload) e mora no use case
# `validar_selo_rbc_permitido`.
#
# Risco que o hook fecha: um refactor "afrouxar" o gate (sumir o raise, ou aceitar
# perfil != A, ou ler perfil do payload), deixando um laboratorio nao-acreditado
# emitir orcamento com selo RBC. Garantia comportamental = UNHAPPY em
# tests/test_orcamentos_templates.py; este hook (camada A) trava a regressao estrutural.
#
# Heuristica (so no use case de templates):
#   Atua em '*/application/comercial/orcamentos/templates.py'. Se define
#   `def validar_selo_rbc_permitido`, exige presenca de:
#     - `raise SeloRbcNaoPermitido`     (perfil != A com selo)
#     - `raise PerfilIndeterminado`     (perfil vazio com selo -> fail-closed)
#     - comparacao com "A"              (`!= "A"` / != 'A')
#   Falta de qualquer uma -> BLOCK (gate afrouxado).
#
# Override: '# orc-template-selo-rbc: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/comercial/orcamentos/templates.py","content":"def validar_selo_rbc_permitido():\n    return ok"}}' | bash .claude/hooks/orc-template-selo-rbc-check.sh; echo $?  # 2
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
    */application/comercial/orcamentos/templates.py) ;;
    *) exit 0 ;;
esac

# So fiscaliza quando a funcao de gate esta presente no conteudo gravado.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+validar_selo_rbc_permitido'; then
    exit 0
fi

# Override por skip explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*orc-template-selo-rbc:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

violacao=""

if ! printf '%s' "$content" | grep -qE 'raise[[:space:]]+SeloRbcNaoPermitido'; then
    violacao="sem 'raise SeloRbcNaoPermitido' (perfil != A com selo deve ser bloqueado)"
elif ! printf '%s' "$content" | grep -qE 'raise[[:space:]]+PerfilIndeterminado'; then
    violacao="sem 'raise PerfilIndeterminado' (perfil vazio + selo deve falhar fechado)"
elif ! printf '%s' "$content" | grep -qE '!=[[:space:]]*["'"'"']A["'"'"']'; then
    violacao="sem comparacao de perfil com 'A' (selo RBC so em perfil A — D-ORC-13)"
fi

if [ -n "$violacao" ]; then
    echo "orc-template-selo-rbc (INV-ORC-SELO-RBC): gate D-ORC-13 afrouxado em $file_path" >&2
    echo "Padrao ausente: $violacao" >&2
    echo "" >&2
    echo "Template com selo_rbc=True so e permitido em tenant perfil A (ADR-0067)." >&2
    echo "Perfil != A -> SeloRbcNaoPermitido (422); perfil vazio -> PerfilIndeterminado." >&2
    echo "Perfil resolvido server-side, NUNCA do payload (AJUSTE-3)." >&2
    echo "Override: '# orc-template-selo-rbc: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
