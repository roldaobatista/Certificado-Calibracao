#!/usr/bin/env bash
# =============================================================
# cert-snapshot-nao-reconsulta-check.sh — M8 Fatia 3 / INV-CER-SNAPSHOT-CMC-001 (T-CER-054)
#
# O read-path do certificado EMITIDO le SO o snapshot persistido — NUNCA reconsulta
# `cmc_para`/`tenant_perfil_e`. Reler a CMC vigente ao exibir um cert antigo faria o
# documento WORM "mudar de valor" depois de emitido (TL-04 — WORM furado por LEITURA).
#
# Por que existir:
#   A garantia comportamental e o teste anti-reconsulta (TestINV_CER_SNAPSHOT_CMC_001
#   / T-CER-052). Este hook (camada A) impede que o read-path serializer reintroduza
#   uma consulta de CMC/perfil — o `serializers.py` do certificado e read-path PURO.
#
# Heuristica (so no serializer do certificado):
#   Atua em '*/metrologia/certificados/serializers.py'. BLOCK se o conteudo
#   referenciar `cmc_para` (qualquer adapter/porta de CMC) ou `tenant_perfil_e`
#   (predicate de perfil regulatorio) — read-path nao reconsulta.
#
# Override: '# cert-snapshot-nao-reconsulta: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/infrastructure/metrologia/certificados/serializers.py","content":"cmc = cmc_para(ponto=p)"}}' | bash .claude/hooks/cert-snapshot-nao-reconsulta-check.sh; echo $?  # 2
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
    */metrologia/certificados/serializers.py) ;;
    *) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*cert-snapshot-nao-reconsulta:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# Casa CHAMADA (`cmc_para(`, `cmc_para_adapter(`, `tenant_perfil_e(`) ou IMPORT —
# NAO a mera mencao em docstring/comentario (que existe pra explicar a regra).
violacao=""
if printf '%s' "$content" | grep -qE '(cmc_para[a-z_]*|tenant_perfil_e)[[:space:]]*\('; then
    violacao='chamada de cmc_para/tenant_perfil_e (reconsulta de CMC/perfil no read-path)'
elif printf '%s' "$content" | grep -qE '^[[:space:]]*(from|import)[[:space:]].*(cmc_para|tenant_perfil_e)'; then
    violacao='import de cmc_para/tenant_perfil_e no read-path serializer'
fi

if [ -n "$violacao" ]; then
    echo "cert-snapshot-nao-reconsulta (INV-CER-SNAPSHOT-CMC-001): read-path reconsulta em $file_path" >&2
    echo "Padrao detectado: $violacao" >&2
    echo "" >&2
    echo "O read-path do cert emitido le SO o snapshot persistido (cmc_no_ponto e o" >&2
    echo "congelado na emissao). Reconsultar cmc_para/tenant_perfil_e faria o WORM" >&2
    echo "mudar de valor por LEITURA (TL-04). Use os campos ja gravados no snapshot." >&2
    echo "Override: '# cert-snapshot-nao-reconsulta: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
