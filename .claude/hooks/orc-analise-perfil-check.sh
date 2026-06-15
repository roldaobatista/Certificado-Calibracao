#!/usr/bin/env bash
# =============================================================
# orc-analise-perfil-check.sh — orcamentos Onda 2f / INV-ORC-CL71-001 (T-ORC-051)
#
# A analise critica cl. 7.1 e PERFIL-AWARE e FAIL-CLOSED (D-ORC-5 / ADR-0067 /
# NIT-DICLA-021). A funcao pura `decidir_analise_critica`
# (`domain/comercial/orcamentos/analise_critica.py`) DEVE:
#   1. Levantar `PerfilIndeterminado` quando o perfil for vazio/desconhecido
#      (fail-closed — nunca aprovar silenciosamente sem perfil).
#   2. Ter caminho REPROVADA com bloqueia=True para perfil A (fora do CMC / sem
#      procedimento / acreditacao suspensa) — emitir RBC fora do escopo acreditado
#      e' NC CGCRE.
#
# Risco que o hook fecha: um refactor "afrouxar" a matriz (perfil A virar fail-open,
# ou sumir o raise PerfilIndeterminado), aprovando orcamento de calibracao indevido.
# Garantia comportamental = UNHAPPY por perfil em tests/regressao/test_inv_orc_cl71.py;
# este hook (camada A) impede a regressao estrutural no arquivo de decisao.
#
# Heuristica (so no arquivo de decisao):
#   Atua em '*/domain/comercial/orcamentos/analise_critica.py'. Se define
#   `def decidir_analise_critica`, exige presenca de:
#     - `raise PerfilIndeterminado`
#     - `VeredictoAnaliseCritica.REPROVADA`
#     - `bloqueia=True`
#   Falta de qualquer uma → BLOCK (fail-closed afrouxado).
#
# Override: '# orc-analise-perfil: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/domain/comercial/orcamentos/analise_critica.py","content":"def decidir_analise_critica():\n    return ok"}}' | bash .claude/hooks/orc-analise-perfil-check.sh; echo $?  # 2
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
    */domain/comercial/orcamentos/analise_critica.py) ;;
    *) exit 0 ;;
esac

# So fiscaliza quando a funcao de decisao esta presente no conteudo gravado.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+decidir_analise_critica'; then
    exit 0
fi

# Override por skip explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*orc-analise-perfil:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

violacao=""

if ! printf '%s' "$content" | grep -qE 'raise[[:space:]]+PerfilIndeterminado'; then
    violacao="sem 'raise PerfilIndeterminado' (perfil vazio/desconhecido deve falhar fechado)"
elif ! printf '%s' "$content" | grep -qE 'VeredictoAnaliseCritica\.REPROVADA'; then
    violacao="sem caminho VeredictoAnaliseCritica.REPROVADA (perfil A fail-closed perdido)"
elif ! printf '%s' "$content" | grep -qE 'bloqueia[[:space:]]*=[[:space:]]*True'; then
    violacao="sem 'bloqueia=True' (reprovada nao bloqueia mais a transicao para aprovado)"
fi

if [ -n "$violacao" ]; then
    echo "orc-analise-perfil (INV-ORC-CL71-001): analise critica cl. 7.1 afrouxada em $file_path" >&2
    echo "Padrao ausente: $violacao" >&2
    echo "" >&2
    echo "Perfil A e fail-closed: item fora do CMC / sem procedimento / acreditacao" >&2
    echo "suspensa -> reprovada (bloqueia=True, 422). Perfil indeterminado -> " >&2
    echo "PerfilIndeterminado. Aprovar calibracao fora do escopo acreditado = NC CGCRE." >&2
    echo "Override: '# orc-analise-perfil: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
