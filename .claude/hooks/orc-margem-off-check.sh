#!/usr/bin/env bash
# =============================================================
# orc-margem-off-check.sh — orcamentos Onda 2f / INV-ORC-MARGEM-OFF (T-ORC-051)
#
# Margem/custo/comissao do orcamento sao SEGREDO COMERCIAL (TL-ORC-06 / ADV-ORC-09):
#   1. O snapshot do item (`ItemOrcamento`) NUNCA persiste margem/custo — esses
#      campos vivem so em `precificacao` (visiveis com `orcamento.ver_margem`).
#   2. O serializer PUBLICO (link do cliente) devolve so a allowlist
#      (descricao/quantidade/preco_unitario/total) — nunca margem/custo/comissao/
#      observacoes/semaforo/preco_resolvido.
#
# Heuristica (2 paths, checagens distintas):
#   (A) '*/domain/comercial/orcamentos/entities.py' → BLOCK se aparecer DECLARACAO
#       de campo `margem`/`custo`/`custo_unitario`/`margem_estimada`/`custo_estimado`
#       (dataclass field `    nome: ...`). `comissao_prevista` no agregado Orcamento
#       e LEGITIMO (so visivel com ver_margem) — nao entra na denylist.
#   (B) '*/orcamentos/serializers_publico.py' → BLOCK se houver ACESSO de atributo
#       ou CHAVE de dict de campo interno (`.comissao_prevista`, `.preco_resolvido`,
#       `.observacoes`, `.semaforo`, `.margem`, `.custo`, ou `"margem":` etc).
#       Mera mencao em docstring/comentario NAO casa (a docstring explica a regra).
#
# Override: '# orc-margem-off: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/orcamentos/serializers_publico.py","content":"return {\"margem\": item.margem}"}}' | bash .claude/hooks/orc-margem-off-check.sh; echo $?  # 2
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

# Override por skip explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*orc-margem-off:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

violacao=""

case "$norm_path" in
    */domain/comercial/orcamentos/entities.py)
        # (A) Declaracao de campo de margem/custo no dominio de orcamentos.
        # `    margem: Dinheiro` / `    custo_unitario: Decimal` etc.
        if printf '%s' "$content" | grep -qE '^[[:space:]]+(margem|custo|custo_unitario|margem_estimada|custo_estimado|margem_pct|custo_real)[[:space:]]*:'; then
            violacao='declaracao de campo de margem/custo no dominio de orcamentos (vive so em precificacao)'
        fi
        ;;
    */orcamentos/serializers_publico.py)
        # (B) Vazamento no serializer publico: acesso de atributo ou chave de dict.
        if printf '%s' "$content" | grep -qE '\.(comissao_prevista|preco_resolvido|observacoes|semaforo|margem|custo)\b'; then
            violacao='acesso a atributo interno (margem/custo/comissao/preco_resolvido/observacoes/semaforo) no serializer publico'
        elif printf '%s' "$content" | grep -qE '["'"'"'](margem|custo|comissao|comissao_prevista|preco_resolvido|observacoes|semaforo|custo_unitario|margem_estimada|custo_estimado)["'"'"'][[:space:]]*:'; then
            violacao='chave de dict de campo interno exposta no serializer publico'
        fi
        ;;
    *)
        exit 0
        ;;
esac

if [ -n "$violacao" ]; then
    echo "orc-margem-off (INV-ORC-MARGEM-OFF): vazamento de segredo comercial em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "" >&2
    echo "Margem/custo/comissao do orcamento sao segredo comercial (TL-ORC-06 / ADV-ORC-09)." >&2
    echo "  - ItemOrcamento NUNCA persiste margem/custo (vivem so em precificacao)." >&2
    echo "  - O serializer publico devolve so descricao/quantidade/preco_unitario/total." >&2
    echo "Override: '# orc-margem-off: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
