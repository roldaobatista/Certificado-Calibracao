#!/usr/bin/env bash
# =============================================================
# escopo-cobre-fail-closed-check.sh — M6 P7 / INV-ECMC-004 (T-ECMC-061)
#
# Protege o GATE central do modulo: a porta `cobre()` em
# `src/infrastructure/metrologia/escopos_cmc/query_service.py` NAO pode regredir
# para fail-open (deixar passar calibracao RBC fora do escopo acreditado). O
# `cmc_cobre` era STUB fail-open (sempre True) ate o M6 plugar a leitura real;
# reintroduzir o fail-open aqui = fraude regulatoria silenciosa (INV-ECMC-004,
# substitui o fail-open lazy da ADR-0066).
#
# Por que existir:
#   ISO/IEC 17025 cl. 6.4.10 — emitir RBC fora da CMC declarada na CGCRE perde a
#   acreditacao. A garantia de runtime e a propria funcao + TestINV_ECMC_004;
#   este hook (camada A) impede que um edit silencioso reescreva `cobre()` para
#   fail-open sem que ninguem perceba.
#
# Heuristica (so no arquivo canonico da porta):
#   Atua APENAS em '*/metrologia/escopos_cmc/query_service.py'. Se o conteudo
#   define `def cobre(` mas PERDE alguma das duas garantias fail-closed:
#     - a checagem de contencao `faixa_contida` (sem ela qualquer faixa "passa")
#     - o sentinela de bloqueio `REASON_FORA_DO_ESCOPO` (retorno negativo)
#   entao BLOCK — sinal de que a funcao foi gutada para liberar geral.
#
# Override: '# escopo-cobre-fail-closed: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/metrologia/escopos_cmc/query_service.py","content":"def cobre(**kw):\n    return True, \"\""}}' | bash .claude/hooks/escopo-cobre-fail-closed-check.sh; echo $?  # 2
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

# Atua so no arquivo canonico da porta de cobertura.
case "$norm_path" in
    */metrologia/escopos_cmc/query_service.py) ;;
    *) exit 0 ;;
esac

# new_string parcial (Edit) que nao toca a funcao cobre nao precisa carregar tudo:
# so avaliamos quando o trecho DEFINE a funcao cobre.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+cobre[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*escopo-cobre-fail-closed:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

faltou=""
if ! printf '%s' "$content" | grep -qE 'faixa_contida'; then
    faltou="checagem de contencao 'faixa_contida'"
elif ! printf '%s' "$content" | grep -qE 'REASON_FORA_DO_ESCOPO'; then
    faltou="sentinela de bloqueio 'REASON_FORA_DO_ESCOPO'"
fi

if [ -n "$faltou" ]; then
    echo "escopo-cobre-fail-closed (INV-ECMC-004): porta cobre() perdeu garantia fail-closed em $file_path" >&2
    echo "Faltando: $faltou" >&2
    echo "" >&2
    echo "cobre() DEVE conferir contencao total (faixa_contida) e retornar" >&2
    echo "(False, REASON_FORA_DO_ESCOPO) quando nenhum escopo CONFIRMADO vigente" >&2
    echo "contem a faixa. Sem isso a porta vira fail-open = emite RBC fora do" >&2
    echo "escopo CGCRE (cl. 6.4.10 / fraude). Nao reintroduza o stub fail-open." >&2
    echo "Override: '# escopo-cobre-fail-closed: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
