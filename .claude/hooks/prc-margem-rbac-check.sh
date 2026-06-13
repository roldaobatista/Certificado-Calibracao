#!/usr/bin/env bash
# =============================================================
# prc-margem-rbac-check.sh — precificacao P7 / INV-PRC-MARGEM-RBAC (T-PRC-052)
#
# Bloqueia serializers da frente `precificacao` que exponham campos de
# margem/custo sem passar pelo choke-point `filtrar_visao_margem`.
#
# A INV-PRC-MARGEM-RBAC exige que QUALQUER funcao de serializacao de saida
# da frente que inclua 'margem_estimada' ou 'custo_estimado' no payload
# DEVE invocar `filtrar_visao_margem(` antes de retornar (D-PRC-4 / ADV-PRC-06).
#
# Heuristica (so em arquivos de serializers da frente):
#   Atua APENAS em '*/precificacao/*serializer*.py' e '*/precificacao/serializers.py'.
#   Para cada funcao `def serializar_*` ou funcao que contém tanto
#   'margem_estimada' quanto 'custo_estimado' no corpo, BLOCK se o corpo
#   NAO invocar `filtrar_visao_margem(`.
#
# Override: '# prc-margem-rbac: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/precificacao/serializers.py","content":"def serializar_resultado(r):\n    return {\"margem_estimada\": r.m, \"custo_estimado\": r.c}"}}' | bash .claude/hooks/prc-margem-rbac-check.sh; echo $?  # 2
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

# Atua so em arquivos de serializers da frente precificacao.
case "$norm_path" in
    */precificacao/serializers.py) ;;
    */precificacao/*serializer*.py) ;;
    *) exit 0 ;;
esac

# Se nao tem campos restritos, nao ha risco.
if ! printf '%s' "$content" | grep -qE '"margem_estimada"|"custo_estimado"'; then
    exit 0
fi

if printf '%s' "$content" | grep -qE '#[[:space:]]*prc-margem-rbac:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# O arquivo tem campos restritos — verifica se filtrar_visao_margem esta presente.
if ! printf '%s' "$content" | grep -qE 'filtrar_visao_margem[[:space:]]*\('; then
    echo "prc-margem-rbac (INV-PRC-MARGEM-RBAC): serializer em $file_path expoe" >&2
    echo "  'margem_estimada' ou 'custo_estimado' sem chamar filtrar_visao_margem()." >&2
    echo "" >&2
    echo "filtrar_visao_margem() e o choke-point UNICO — TODOS os serializers de" >&2
    echo "saida da frente precificacao que incluam esses campos DEVEM passar por ela" >&2
    echo "(D-PRC-4 / INV-PRC-MARGEM-RBAC / ADV-PRC-06). Sem o filtro, custo e" >&2
    echo "margem vazam para qualquer papel — segredo comercial exposto." >&2
    echo "Override: '# prc-margem-rbac: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
