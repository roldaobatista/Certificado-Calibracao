#!/usr/bin/env bash
# =============================================================
# fiscal-provider-import-fronteira-check.sh — fiscal/NFS-e Fatia 3 / INV-FIS-003 (T-FIS-041)
#
# Porta agnostica (ADR-0008 §1 / D-FIS-8): dominio e use case NUNCA importam SDK de
# fornecedor; toda emissao passa pela porta `FiscalProvider`. `plugnotas*`/`focus*`/
# `pybreaker` so podem ser importados em `src/infrastructure/fiscal/` (adapters reais
# + circuit breaker, ambos diferidos GATE pre-producao). Acoplar o SDK ao dominio
# obriga reescrita ao trocar de fornecedor ou sair pra LATAM.
#
# Heuristica:
#   BLOCK quando .py importa `plugnotas`/`focusnfe`/`focus_nfe`/`pybreaker` E o path
#   NAO esta sob `src/infrastructure/fiscal/` (e nao e teste/migration/doc).
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py
#   - src/infrastructure/fiscal/** (lar dos adapters reais + breaker)
#
# Override: '# fiscal-provider-import: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/domain/fiscal/x.py","content":"import plugnotas"}}' | bash .claude/hooks/fiscal-provider-import-fronteira-check.sh; echo $?  # 2
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

case "$norm_path" in
    tests/*|*/tests/*|*/test_*|*_test.py|*conftest.py) exit 0 ;;
    */migrations/*) exit 0 ;;
    docs/*|*/docs/*) exit 0 ;;
    */infrastructure/fiscal/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*fiscal-provider-import:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# import de SDK de fornecedor fiscal / circuit breaker fora da fronteira de infra.
if printf '%s' "$content" | grep -qE '^[[:space:]]*(import|from)[[:space:]]+(plugnotas|focusnfe|focus_nfe|pybreaker)'; then
    echo "fiscal-provider-import (INV-FIS-003): SDK de fornecedor importado fora de infrastructure/fiscal em $file_path" >&2
    echo "Dominio/use case nunca importam SDK — use a porta FiscalProvider (ADR-0008 §1)." >&2
    echo "plugnotas*/focus*/pybreaker so em src/infrastructure/fiscal/." >&2
    echo "Override: '# fiscal-provider-import: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
