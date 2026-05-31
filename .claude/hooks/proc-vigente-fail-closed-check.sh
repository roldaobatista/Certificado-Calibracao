#!/usr/bin/env bash
# =============================================================
# proc-vigente-fail-closed-check.sh — M7 Fatia 3 / INV-PROC-004 (T-PROC-047)
#
# Protege o GATE central do modulo: a porta `vigente_em()` em
# `src/infrastructure/metrologia/procedimentos_calibracao/query_service.py` NAO
# pode regredir para fail-open (deixar passar calibracao RBC sem procedimento
# tecnico documentado vigente). O predicate `procedimento_vigente_para` era STUB
# fail-open (sempre True) ate o M7 plugar a leitura real; reintroduzir o fail-open
# aqui = emitir RBC sem metodo controlado (cl. 7.2.1 / fraude documental,
# INV-PROC-004, substitui o fail-open lazy da ADR-0066).
#
# Por que existir:
#   ISO/IEC 17025 cl. 7.2.1 — emitir calibracao RBC sem procedimento documentado
#   controlado vigente e NC de supervisao CGCRE. A garantia de runtime e a propria
#   funcao + TestINV_PROC_004; este hook (camada A) impede que um edit silencioso
#   reescreva `vigente_em()` para fail-open sem que ninguem perceba.
#
# Heuristica (so no arquivo canonico da porta):
#   Atua APENAS em '*/metrologia/procedimentos_calibracao/query_service.py'. Se o
#   conteudo define `def vigente_em(` mas PERDE alguma das duas garantias:
#     - a checagem de contencao `faixa_contida` (sem ela qualquer faixa "passa")
#     - o filtro de estado `PUBLICADO` (sem ele RASCUNHO/REVOGADO resolveriam)
#   entao BLOCK — sinal de que a funcao foi gutada para liberar geral.
#
# Override: '# proc-vigente-fail-closed: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/metrologia/procedimentos_calibracao/query_service.py","content":"def vigente_em(**kw):\n    return object()"}}' | bash .claude/hooks/proc-vigente-fail-closed-check.sh; echo $?  # 2
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

# Atua so no arquivo canonico da porta de procedimento vigente.
case "$norm_path" in
    */metrologia/procedimentos_calibracao/query_service.py) ;;
    *) exit 0 ;;
esac

# So avaliamos quando o trecho DEFINE a funcao vigente_em.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+vigente_em[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*proc-vigente-fail-closed:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

faltou=""
if ! printf '%s' "$content" | grep -qE 'faixa_contida'; then
    faltou="checagem de contencao 'faixa_contida'"
elif ! printf '%s' "$content" | grep -qE 'PUBLICADO'; then
    faltou="filtro de estado 'PUBLICADO'"
fi

if [ -n "$faltou" ]; then
    echo "proc-vigente-fail-closed (INV-PROC-004): porta vigente_em() perdeu garantia fail-closed em $file_path" >&2
    echo "Faltando: $faltou" >&2
    echo "" >&2
    echo "vigente_em() DEVE filtrar so PUBLICADO vigente e conferir contencao total" >&2
    echo "(faixa_contida); retornar None quando nenhum procedimento documentado" >&2
    echo "vigente contem a faixa. Sem isso a porta vira fail-open = emite RBC sem" >&2
    echo "metodo controlado (cl. 7.2.1 / NC CGCRE). Nao reintroduza o stub fail-open." >&2
    echo "Override: '# proc-vigente-fail-closed: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
