#!/usr/bin/env bash
# =============================================================
# cr-provider-import-fronteira-check.sh — contas-receber Fatia 3d / INV-FIN-GW-001 (T-CR-047)
#
# Porta agnostica (ADR-0050 / D-CR-7): dominio e use case de contas-receber NUNCA
# importam SDK de gateway de pagamento; toda cobranca/baixa passa pela porta
# `PaymentGatewayProvider`. SDK de provedor (asaas/mercadopago/stripe/pagseguro/iugu/
# pagarme/pyboleto) + circuit breaker (pybreaker) so podem ser importados em
# `src/infrastructure/contas_receber/` (adapter real = GATE pre-producao; Wave A roda
# com Mock). Acoplar o SDK ao dominio obriga reescrita ao trocar de gateway.
#
# Heuristica:
#   BLOCK quando .py importa SDK de gateway/breaker E o path NAO esta sob
#   `src/infrastructure/contas_receber/` (e nao e teste/migration/doc).
#
# Auto-allow (exit 0):
#   - tests/** ; migrations/** ; docs/** ; nao-.py
#   - src/infrastructure/contas_receber/** (lar do adapter real + breaker)
#
# Override: '# cr-provider-import: skip -- <razao com >=10 chars>'
#
# Como testar:
#   echo '{"tool_input":{"file_path":"src/domain/contas_receber/x.py","content":"import asaas"}}' | bash .claude/hooks/cr-provider-import-fronteira-check.sh; echo $?  # 2
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
    */infrastructure/contas_receber/*) exit 0 ;;
esac

if printf '%s' "$content" | grep -qE '#[[:space:]]*cr-provider-import:[[:space:]]*skip[[:space:]]*--[[:space:]]*.{10,}'; then
    exit 0
fi

# import de SDK de gateway de pagamento / circuit breaker fora da fronteira de infra.
if printf '%s' "$content" | grep -qE '^[[:space:]]*(import|from)[[:space:]]+(asaas|mercadopago|stripe|pagseguro|iugu|pagarme|pyboleto|pybreaker)'; then
    echo "cr-provider-import (INV-FIN-GW-001): SDK de gateway importado fora de infrastructure/contas_receber em $file_path" >&2
    echo "Dominio/use case nunca importam SDK — use a porta PaymentGatewayProvider (ADR-0050)." >&2
    echo "asaas*/mercadopago/stripe/pagseguro/iugu/pagarme/pyboleto/pybreaker so em src/infrastructure/contas_receber/." >&2
    echo "Override: '# cr-provider-import: skip -- <razao com >=10 chars>'" >&2
    exit 2
fi

exit 0
