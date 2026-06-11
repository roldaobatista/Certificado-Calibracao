#!/usr/bin/env bash
# =============================================================
# pps-porta-fail-closed-check.sh — produtos-pecas-servicos P7 / INV-PPS-PRECO-FAIL-CLOSED (T-PPS-051)
#
# Protege o GATE central da frente: a porta `preco_para_os` em
# `src/infrastructure/produtos_pecas_servicos/query_service.py` NAO pode
# regredir para fallback ao `preco_padrao` da LISTA quando nao ha linha de
# VENDA vigente (ADR-0081 / D-PPS-2). Fallback silencioso cobraria preco de
# lista nao aprovado como preco de venda (ADV-PPS-09c) — a OS espera 422
# `PrecoTabelaAusente` (US-OS-015), nunca um numero "conveniente".
#
# Heuristica (so no arquivo canonico da porta):
#   Atua APENAS em '*/produtos_pecas_servicos/query_service.py'. Se o conteudo
#   define `def preco_para_os(` mas PERDE alguma das duas garantias:
#     - a resolucao pela linha de venda `linha_vigente_em` (sem ela o valor
#       viria de outro lugar — ex.: preco_padrao da lista)
#     - o sentinela fail-closed `PrecoTabelaAusenteError` (raise na ausencia)
#   entao BLOCK — sinal de que a porta foi gutada para fail-open/fallback.
#
# Override: '# pps-porta-fail-closed: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/produtos_pecas_servicos/query_service.py","content":"def preco_para_os(**kw):\n    return versao.preco_padrao"}}' | bash .claude/hooks/pps-porta-fail-closed-check.sh; echo $?  # 2
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

# Atua so no arquivo canonico da porta de preco.
case "$norm_path" in
    */produtos_pecas_servicos/query_service.py) ;;
    *) exit 0 ;;
esac

# Edit parcial que nao toca a porta nao precisa carregar tudo.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+preco_para_os[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*pps-porta-fail-closed:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

faltou=""
if ! printf '%s' "$content" | grep -qE 'linha_vigente_em'; then
    faltou="resolucao pela linha de venda 'linha_vigente_em'"
elif ! printf '%s' "$content" | grep -qE 'PrecoTabelaAusenteError'; then
    faltou="sentinela fail-closed 'PrecoTabelaAusenteError'"
fi

if [ -n "$faltou" ]; then
    echo "pps-porta-fail-closed (INV-PPS-PRECO-FAIL-CLOSED): porta preco_para_os perdeu garantia em $file_path" >&2
    echo "Faltando: $faltou" >&2
    echo "" >&2
    echo "preco_para_os DEVE resolver pela linha de VENDA vigente (linha_vigente_em)" >&2
    echo "e levantar PrecoTabelaAusenteError na ausencia — SEM fallback ao" >&2
    echo "preco_padrao da lista (ADR-0081 / D-PPS-2 / ADV-PPS-09c). Fallback" >&2
    echo "silencioso = cobrar preco nao aprovado. Nao regrida a porta." >&2
    echo "Override: '# pps-porta-fail-closed: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
