#!/usr/bin/env bash
# =============================================================
# outbound-webhook-ssrf-check.sh
# Foundation F-C1 P4 T-FC1-10 — INV-WEBHOOK-OUT-001
#
# Bloqueia uso direto de bibliotecas HTTP em src/infrastructure/**
# fora do adapter canonico src/infrastructure/webhook_out/.
#
# Forca todo HTTP outbound passar por OutboundWebhookProvider
# (ADR-0054) que implementa SSRF guard + HMAC + DNS rebinding lock +
# DPA enforcement.
#
# Bibliotecas detectadas:
#   - requests.get / post / put / patch / delete / head / options / request
#   - httpx.* (sync e AsyncClient)
#   - urllib.request.urlopen / Request
#   - urllib3.PoolManager / request
#   - aiohttp.ClientSession
#
# Aplica a: src/infrastructure/**/*.py FORA de webhook_out/
#
# Allow via:
#   - Linha: # webhook-out: skip -- <razao ≥10 chars>
#   - Arquivo: # webhook-out: skip-all -- <razao ≥10 chars>
# =============================================================

set -u
input=$(cat)

content=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    my $ti = $j->{tool_input} // {};
    print $ti->{content} // $ti->{new_string} // "";
' 2>/dev/null)

file_path=$(printf '%s' "$input" | perl -MJSON::PP -e '
    local $/; my $raw = <STDIN>; my $j;
    eval { $j = JSON::PP->new->decode($raw); 1 } or exit 0;
    print $j->{tool_input}{file_path} // "";
' 2>/dev/null)

[ -z "$content" ] && exit 0
file_path_norm=$(printf '%s' "$file_path" | tr '\\' '/')

# Aplica somente a src/infrastructure/**/*.py
case "$file_path_norm" in
    src/infrastructure/*.py|*/src/infrastructure/*.py) ;;
    *) exit 0 ;;
esac

# Permite USO no proprio webhook_out (eh quem implementa o adapter)
case "$file_path_norm" in
    *src/infrastructure/webhook_out/*) exit 0 ;;
esac

# Pula tests/ e migrations/
case "$file_path_norm" in
    */tests/*|*/migrations/*) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'webhook-out:\s*skip-all\s*--\s*.{10,}'; then
    exit 0
fi

violations=()

# Helper pra checar se a LINHA tem skip inline
# Aceita skip ate 5 linhas acima (pra suportar comentario antes do bloco
# de uso, ex: skip + import + chamada na linha 3)
linha_tem_skip() {
    local linha_n="$1"
    local janela
    janela=$(printf '%s' "$content" | awk -v ln="$linha_n" 'NR>=ln-5 && NR<=ln {print}')
    printf '%s' "$janela" | grep -qE 'webhook-out:\s*skip\s*--\s*.{10,}'
}

# 1. requests.get/post/put/patch/delete/head/options/request
while IFS=: read -r linha_n linha_conteudo; do
    [ -z "$linha_n" ] && continue
    if ! linha_tem_skip "$linha_n"; then
        violations+=("linha $linha_n: uso direto de 'requests' — usar OutboundWebhookProvider (ADR-0054)")
    fi
done < <(printf '%s' "$content" | grep -nE '\brequests\.(get|post|put|patch|delete|head|options|request)\(' || true)

# 2. httpx (sync ou async)
while IFS=: read -r linha_n linha_conteudo; do
    [ -z "$linha_n" ] && continue
    if ! linha_tem_skip "$linha_n"; then
        violations+=("linha $linha_n: uso direto de 'httpx' — usar OutboundWebhookProvider")
    fi
done < <(printf '%s' "$content" | grep -nE '\bhttpx\.(get|post|put|patch|delete|head|options|request|Client|AsyncClient)\(' || true)

# 3. urllib.request
while IFS=: read -r linha_n linha_conteudo; do
    [ -z "$linha_n" ] && continue
    if ! linha_tem_skip "$linha_n"; then
        violations+=("linha $linha_n: uso direto de 'urllib.request' — usar OutboundWebhookProvider")
    fi
done < <(printf '%s' "$content" | grep -nE '(urllib\.request\.(urlopen|Request)|from urllib\.request import)' || true)

# 4. urllib3 PoolManager / direct request
while IFS=: read -r linha_n linha_conteudo; do
    [ -z "$linha_n" ] && continue
    if ! linha_tem_skip "$linha_n"; then
        violations+=("linha $linha_n: uso direto de 'urllib3' — usar OutboundWebhookProvider")
    fi
done < <(printf '%s' "$content" | grep -nE '\burllib3\.(PoolManager|HTTPSConnectionPool|HTTPConnectionPool|request)\(' || true)

# 5. aiohttp ClientSession
while IFS=: read -r linha_n linha_conteudo; do
    [ -z "$linha_n" ] && continue
    if ! linha_tem_skip "$linha_n"; then
        violations+=("linha $linha_n: uso direto de 'aiohttp' — usar OutboundWebhookProvider")
    fi
done < <(printf '%s' "$content" | grep -nE '\baiohttp\.ClientSession\(' || true)

if [ ${#violations[@]} -gt 0 ]; then
    echo "outbound-webhook-ssrf-check: uso direto de biblioteca HTTP em $file_path" >&2
    echo "" >&2
    for v in "${violations[@]}"; do
        echo "  - $v" >&2
    done
    echo "" >&2
    echo "INV-WEBHOOK-OUT-001 (ADR-0054 / F-C1): toda chamada HTTP outbound em" >&2
    echo "src/infrastructure/** passa por OutboundWebhookProvider (porta" >&2
    echo "canonica). Implementacao: src/infrastructure/webhook_out/." >&2
    echo "" >&2
    echo "Allow linha: # webhook-out: skip -- <razao ≥10 chars>" >&2
    echo "Allow arquivo: # webhook-out: skip-all -- <razao ≥10 chars>" >&2
    exit 2
fi

exit 0
