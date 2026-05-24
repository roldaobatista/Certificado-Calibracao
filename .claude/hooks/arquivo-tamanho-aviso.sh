#!/usr/bin/env bash
# =============================================================
# arquivo-tamanho-aviso.sh
# Onda 2 plano-v2 (2026-05-23) — auditor QUAL apontou god-modules
# em src/infrastructure/equipamentos/models.py (1831L) e
# src/infrastructure/ordens_servico/models.py (1055L).
#
# Rede de seguranca PRA NAO criar novos god-modules. Quebra dos
# atuais fica DEFERIDA pos-Marco 3 Fase 5 (docs/arquitetura/god-modules-deferral.md).
#
# Limites:
# - 600 linhas: AVISO (exit 0 + mensagem stderr)
# - 1500 linhas: BLOQUEIO (exit 2)
#
# Aplica a: src/infrastructure/**/models.py
#           src/infrastructure/**/views.py
#
# Allow via:
#   - Comentario no topo do arquivo: # arquivo-tamanho: skip -- <razao ≥10 chars>
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

# Aplica somente a models.py e views.py em src/infrastructure/
case "$file_path_norm" in
    src/infrastructure/*/models.py|*/src/infrastructure/*/models.py) ;;
    src/infrastructure/*/views.py|*/src/infrastructure/*/views.py) ;;
    *) exit 0 ;;
esac

# Pula tests/ e migrations/
case "$file_path_norm" in
    */tests/*|*/migrations/*) exit 0 ;;
esac

# Skip arquivo inteiro
if printf '%s' "$content" | grep -qE 'arquivo-tamanho:\s*skip\s*--\s*.{10,}'; then
    exit 0
fi

# Conta linhas (com \n no final ou nao)
linhas=$(printf '%s' "$content" | awk 'END { print NR }')

LIMITE_AVISO=600
LIMITE_BLOQUEIO=1500

if [ "$linhas" -gt "$LIMITE_BLOQUEIO" ]; then
    echo "arquivo-tamanho-aviso: arquivo com $linhas linhas (limite bloqueio: $LIMITE_BLOQUEIO)" >&2
    echo "" >&2
    echo "Arquivo $file_path passou do limite de bloqueio." >&2
    echo "Ver docs/arquitetura/god-modules-deferral.md para guia de quebra por agregado (DDD)." >&2
    echo "Allow via: # arquivo-tamanho: skip -- <razao ≥10 chars>" >&2
    exit 2
elif [ "$linhas" -gt "$LIMITE_AVISO" ]; then
    # Aviso nao-bloqueante
    echo "arquivo-tamanho-aviso: arquivo com $linhas linhas (limite aviso: $LIMITE_AVISO; bloqueio: $LIMITE_BLOQUEIO)" >&2
    echo "Considere quebrar por agregado (DDD). Ver docs/arquitetura/god-modules-deferral.md" >&2
    exit 0
fi

exit 0
