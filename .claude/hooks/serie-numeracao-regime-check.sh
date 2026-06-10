#!/usr/bin/env bash
# =============================================================
# serie-numeracao-regime-check.sh — configuracoes-sistema Fatia 3 / INV-CFG-NUM-ATOMICA (T-CFG-041)
#
# ADR-0080: o regime de numeracao de uma SerieDocumento e DERIVADO do TIPO do
# documento (`regime_numeracao_do_tipo` — fatura/certificado = gap-less; demais =
# buracos-aceitos). Se o caller puder escolher o regime via payload, um tenant
# cria fatura com buracos-aceitos (autuacao fiscal) ou certificado com gap
# (NIT-DICLA-021). O hook tambem barra a volta do tipo `nf`/`nfse` na enumeracao
# local (BaaS/municipio numera — ADV-04 / INV-028 reconciliada).
#
# Heuristica (so .py em path *configuracoes_sistema*, fora de teste/migration/doc):
#   BLOCK quando o conteudo:
#   a) declara campo `regime_numeracao`/`reset_anual` em Serializer (input do caller); ou
#   b) atribui regime a partir de fonte do cliente (request.data/validated_data/payload); ou
#   c) acrescenta `nf`/`nfse` ao enum TipoDocumento.
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py ; path nao-*configuracoes_sistema*
#   - src/domain/configuracoes_sistema/transicoes.py (lar da derivacao)
#
# Override: '# serie-numeracao-regime: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/configuracoes_sistema/serializers.py","content":"regime_numeracao = serializers.ChoiceField()"}}' | bash .claude/hooks/serie-numeracao-regime-check.sh; echo $?  # 2
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
    *.py) ;;
    *) exit 0 ;;
esac

# So arquivos da frente configuracoes-sistema.
case "$norm_path" in
    *configuracoes_sistema*) ;;
    *) exit 0 ;;
esac

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    *src/domain/configuracoes_sistema/transicoes.py) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*serie-numeracao-regime:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

codigo=$(printf '%s' "$content" | grep -vE '^[[:space:]]*#')

# a) campo de Serializer aceitando regime/reset do caller
if printf '%s' "$codigo" | grep -qE '(regime_numeracao|reset_anual)[[:space:]]*=[[:space:]]*serializers\.'; then
    echo "serie-numeracao-regime (INV-CFG-NUM-ATOMICA): regime_numeracao/reset_anual como input do caller em $file_path" >&2
    echo "ADR-0080: regime e DERIVADO do tipo (regime_numeracao_do_tipo); reset_anual do {ano} no formato (TL-07)." >&2
    echo "Remova o campo do Serializer — o use case deriva." >&2
    echo "Override: '# serie-numeracao-regime: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

# b) regime atribuido a partir do payload
if printf '%s' "$codigo" | grep -qE 'regime_numeracao["'"'"']?[[:space:]]*[:=][^=].*((request\.(data|POST|JSON|json|body))|validated_data|payload|initial_data)'; then
    echo "serie-numeracao-regime (INV-CFG-NUM-ATOMICA): regime_numeracao vindo do payload em $file_path" >&2
    echo "ADR-0080: derive com regime_numeracao_do_tipo(tipo) — nunca do caller." >&2
    echo "Override: '# serie-numeracao-regime: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

# c) nf/nfse na enumeracao local de TipoDocumento (ADV-04)
if printf '%s' "$codigo" | grep -qE '^[[:space:]]*NFS?E?[[:space:]]*=[[:space:]]*["'"'"']nfs?e?["'"'"']'; then
    echo "serie-numeracao-regime (INV-028 reconciliada/ADV-04): tipo nf/nfse na numeracao LOCAL em $file_path" >&2
    echo "NFS-e/NF sao numeradas pelo BaaS/municipio (ADR-0008/ADR-0080) — nao entram em SerieDocumento." >&2
    echo "Override: '# serie-numeracao-regime: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
