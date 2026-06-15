#!/usr/bin/env bash
# =============================================================
# orc-envelope-contrato-check.sh — orcamentos Onda 2f / INV-ORC-APROVADO-ENVELOPE (T-ORC-051)
#
# O evento `orcamento.aprovado` carrega o envelope EXATO que a OS consome
# (ADR-0082 — equipamento POR ITEM). Produtor `montar_envelope_orcamento_aprovado`
# (`domain/comercial/orcamentos/transicoes.py`) e consumidor
# `handle_orcamento_aprovado._parse_input` (`infrastructure/ordens_servico/
# consumers/orcamento.py`) batem por contrato. Se o produtor renomear/remover uma
# chave, a OS quebra SILENCIOSAMENTE em producao (dead-letter ou OS malformada).
#
# Garantia comportamental real = teste de contrato E2E
# (`tests/regressao/test_inv_orc_envelope.py`). Este hook (camada A) e a rede:
# impede que o builder do envelope perca uma chave canonica que o `_parse_input` le.
#
# Heuristica (so no produtor):
#   Atua em '*/domain/comercial/orcamentos/transicoes.py'. Se o conteudo define
#   `def montar_envelope_orcamento_aprovado`, entao TODAS as chaves canonicas do
#   header + do item devem aparecer como literal de string. Falta de qualquer uma
#   → BLOCK.
#
# Override: '# orc-envelope-contrato: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/domain/comercial/orcamentos/transicoes.py","content":"def montar_envelope_orcamento_aprovado():\n    return {\"orcamento_id\": 1}"}}' | bash .claude/hooks/orc-envelope-contrato-check.sh; echo $?  # 2
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
    */domain/comercial/orcamentos/transicoes.py) ;;
    *) exit 0 ;;
esac

# So fiscaliza quando o builder esta presente no conteudo gravado.
if ! printf '%s' "$content" | grep -qE 'def[[:space:]]+montar_envelope_orcamento_aprovado'; then
    exit 0
fi

# Override por skip explicito.
if printf '%s' "$content" | grep -qE '#[[:space:]]*orc-envelope-contrato:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Chaves canonicas que o consumidor `_parse_input` le do envelope (header + item).
chaves_obrigatorias="orcamento_id tenant_id cliente_id cliente_referencia_hash cliente_key_id analise_critica_id analise_critica_snapshot_hash valor_total abertura_at itens tipo sequencia valor_unitario requer_recebimento equipamento_id"

faltando=""
for chave in $chaves_obrigatorias; do
    # Casa o literal de string da chave: "chave" ou 'chave'.
    if ! printf '%s' "$content" | grep -qE "[\"']${chave}[\"']"; then
        faltando="$faltando $chave"
    fi
done

if [ -n "$faltando" ]; then
    echo "orc-envelope-contrato (INV-ORC-APROVADO-ENVELOPE): chave(s) ausente(s) no envelope orcamento.aprovado em $file_path" >&2
    echo "Chave(s) faltando:$faltando" >&2
    echo "" >&2
    echo "O consumidor handle_orcamento_aprovado._parse_input le essas chaves (ADR-0082)." >&2
    echo "Remover/renomear quebra a OS em producao (dead-letter). Atualize o contrato +" >&2
    echo "o teste tests/regressao/test_inv_orc_envelope.py antes de mudar o envelope." >&2
    echo "Override: '# orc-envelope-contrato: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
