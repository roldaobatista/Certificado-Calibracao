#!/usr/bin/env bash
# =============================================================
# prc-costplus-stub-check.sh — precificacao P7 / INV-PRC-COSTPLUS-STUB (T-PRC-052)
#
# Bloqueia publicar_regra em `application/precificacao/regra.py` (o unico
# arquivo que faz o gate COST_PLUS) se o gate desaparecer:
#   - A funcao `publicar_regra` existe no arquivo, E
#   - A verificacao `custo_provider.disponivel()` foi removida, OU
#   - O raise `CustoRealIndisponivel` foi removido.
#
# Heuristica (so no arquivo canonico do use case):
#   Atua APENAS em '*/application/precificacao/regra.py'. Se o conteudo
#   define `def publicar_regra(` mas PERDE alguma das duas garantias:
#     - verificacao 'custo_provider.disponivel()' (gate do stub)
#     - raise 'CustoRealIndisponivel' (sinalizacao de falha)
#   entao BLOCK — sinal de que o gate foi gutado.
#
# Override: '# prc-costplus-stub: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/application/precificacao/regra.py","content":"def publicar_regra(inp, *, repo, custo_provider):\n    return repo.salvar(None)"}}' | bash .claude/hooks/prc-costplus-stub-check.sh; echo $?  # 2
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

# Atua so no arquivo canonico do use case de publicacao de regra.
case "$norm_path" in
    */application/precificacao/regra.py) ;;
    *) exit 0 ;;
esac

# Edit parcial que nao toca a funcao nao precisa carregar tudo.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+publicar_regra[[:space:]]*\('; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*prc-costplus-stub:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

faltou=""
if ! printf '%s' "$content" | grep -qE 'custo_provider\.disponivel\(\)'; then
    faltou="verificacao 'custo_provider.disponivel()' — gate do stub"
elif ! printf '%s' "$content" | grep -qE 'CustoRealIndisponivel'; then
    faltou="raise 'CustoRealIndisponivel' — sinalizacao de falha fail-closed"
fi

if [ -n "$faltou" ]; then
    echo "prc-costplus-stub (INV-PRC-COSTPLUS-STUB): publicar_regra perdeu gate COST_PLUS em $file_path" >&2
    echo "Faltando: $faltou" >&2
    echo "" >&2
    echo "publicar_regra DEVE verificar custo_provider.disponivel() e levantar" >&2
    echo "CustoRealIndisponivel quando False + modo == COST_PLUS (D-PRC-6)." >&2
    echo "Fail-open geraria preco calculado sem custo real — prejuizo silencioso." >&2
    echo "Override: '# prc-costplus-stub: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
